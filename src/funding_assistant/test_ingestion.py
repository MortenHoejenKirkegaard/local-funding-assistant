from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from funding_assistant.policy import resolve_inside_root, validate_action


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_ROOT = PROJECT_ROOT / "funding-assistant-test"
TEST_INBOX = TEST_ROOT / "system" / "inbox"
TEST_INDEX = TEST_ROOT / "system" / "index" / "documents-index.jsonl"
TEST_EVENTS = TEST_ROOT / "system" / "logs" / "ingestion-events.jsonl"
TEST_RUNTIME_CONFIG = TEST_ROOT / "system" / "config" / "runtime.json"
TEST_APPLICATION_INDEX = TEST_ROOT / "applications" / "applications-index.jsonl"

CATEGORY_TO_FOLDER = {
    "profile": "00_profile",
    "technical": "01_technical",
    "ip_patents": "02_ip_patents",
    "clinical": "03_clinical",
    "market": "04_market",
    "commercial": "05_commercial",
    "team_partners": "06_team_partners",
    "pitch_investor": "07_pitch_investor",
    "applications": "08_applications",
    "raw_inbox": "09_raw_inbox",
}

DOCUMENT_KEYWORDS = {
    "profile": ["profile", "onepager", "one-pager", "overview", "status"],
    "technical": ["technical", "tech", "spec", "architecture", "test", "validation"],
    "ip_patents": ["patent", "ip", "claims", "freedom-to-operate", "fto"],
    "clinical": ["clinical", "clinic", "study", "evidence", "protocol", "endpoint"],
    "market": ["market", "tam", "sam", "som", "competitor", "analysis"],
    "commercial": ["commercial", "business", "gtm", "reimbursement", "pricing"],
    "team_partners": ["team", "partner", "advisor", "loi", "cv"],
    "pitch_investor": ["pitch", "investor", "deck", "memo"],
    "applications": ["application", "grant", "funding", "budget", "milestone"],
    "raw_inbox": ["raw", "misc", "unknown"],
}

WRITING_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "will", "can", "has", "have",
    "der", "det", "den", "som", "med", "til", "for", "har", "kan", "skal", "fra", "vil", "paa",
}


@dataclass(frozen=True)
class TestCompany:
    company_id: str
    display_name: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class IngestionResult:
    status: str
    source_path: str
    destination_path: str
    company_id: str
    document_type: str
    sha256: str
    file_size_bytes: int
    extracted_text_preview: str
    created_at: str


@dataclass(frozen=True)
class IndexSuggestion:
    filename: str
    suggested_company_id: str
    suggested_document_type: str
    confidence: int
    rationale: str
    auto_index: bool


@dataclass(frozen=True)
class ApplicationRecord:
    status: str
    source_path: str
    destination_path: str
    outcome: str
    company_id: str
    external_company_name: str
    sha256: str
    file_size_bytes: int
    text_preview: str
    created_at: str


def ingest_test_file(filename: str, company_id: str, document_type: str) -> IngestionResult:
    _validate_local_write()
    _validate_company(company_id)
    _validate_document_type(document_type)

    source_path = resolve_inside_root(TEST_INBOX / filename, PROJECT_ROOT)
    if not source_path.exists() or not source_path.is_file():
        raise FileNotFoundError(f"Test inbox file not found: {source_path}")

    destination_dir = resolve_inside_root(
        TEST_ROOT / "cases" / company_id / CATEGORY_TO_FOLDER[document_type],
        PROJECT_ROOT,
    )
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination_path = _deduplicated_destination(destination_dir / source_path.name)

    file_hash = _sha256(source_path)
    file_size = source_path.stat().st_size
    preview = _extract_preview(source_path)

    shutil.move(str(source_path), str(destination_path))

    result = IngestionResult(
        status="indexed",
        source_path=str(source_path.relative_to(PROJECT_ROOT)),
        destination_path=str(destination_path.relative_to(PROJECT_ROOT)),
        company_id=company_id,
        document_type=document_type,
        sha256=file_hash,
        file_size_bytes=file_size,
        extracted_text_preview=preview,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    _append_jsonl(TEST_INDEX, asdict(result))
    _append_jsonl(
        TEST_EVENTS,
        {
            "event_type": "test_ingestion_indexed",
            "company_id": company_id,
            "document_type": document_type,
            "destination_path": result.destination_path,
            "created_at": result.created_at,
        },
    )

    return result


def list_test_inbox() -> list[str]:
    resolve_inside_root(TEST_INBOX, PROJECT_ROOT)
    return sorted(path.name for path in TEST_INBOX.iterdir() if path.is_file() and path.name != ".gitkeep")


def list_test_companies() -> list[TestCompany]:
    companies = []
    for manifest_path in sorted((TEST_ROOT / "cases").glob("*/index_manifest.yml")):
        manifest = _read_simple_manifest(manifest_path)
        company_id = manifest.get("company_id") or manifest_path.parent.name
        display_name = manifest.get("display_name") or company_id
        aliases = tuple(alias.strip() for alias in manifest.get("aliases", "").split(",") if alias.strip())
        companies.append(TestCompany(company_id=company_id, display_name=display_name, aliases=aliases))
    return companies


def suggest_indexing(filename: str) -> IndexSuggestion:
    source_path = resolve_inside_root(TEST_INBOX / filename, PROJECT_ROOT)
    text = _suggestion_text(source_path)
    company_id, company_score, company_reason = _suggest_company(text)
    document_type, type_score, type_reason = _suggest_document_type(text)

    confidence = min(company_score, type_score)
    rationale = "; ".join(part for part in [company_reason, type_reason] if part)

    return IndexSuggestion(
        filename=filename,
        suggested_company_id=company_id,
        suggested_document_type=document_type,
        confidence=confidence,
        rationale=rationale or "No strong local signal found.",
        auto_index=confidence >= 95,
    )


def add_test_company(display_name: str, aliases: str = "") -> TestCompany:
    cleaned_name = display_name.strip()
    if not cleaned_name:
        raise ValueError("Company name is required.")

    existing_ids = {company.company_id for company in list_test_companies()}
    next_number = 1
    while f"company-{next_number:02d}" in existing_ids:
        next_number += 1

    company_id = f"company-{next_number:02d}"
    company_dir = TEST_ROOT / "cases" / company_id
    _create_company_structure(company_dir)
    alias_tuple = _parse_aliases(aliases)
    _write_manifest(company_dir / "index_manifest.yml", company_id, cleaned_name, alias_tuple)
    return TestCompany(company_id=company_id, display_name=cleaned_name, aliases=alias_tuple)


def configure_test_workspace(company_names: list[str]) -> None:
    cleaned_names = [name.strip() for name in company_names if name.strip()]
    if not cleaned_names:
        raise ValueError("At least one company name is required.")

    cases_root = TEST_ROOT / "cases"
    archive_root = TEST_ROOT / "system" / "quarantine" / f"cases-reset-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    existing_case_dirs = [path for path in cases_root.glob("company-*") if path.is_dir()]
    if existing_case_dirs:
        archive_root.mkdir(parents=True, exist_ok=True)
        for path in existing_case_dirs:
            shutil.move(str(path), str(archive_root / path.name))

    for index, name in enumerate(cleaned_names, start=1):
        company_id = f"company-{index:02d}"
        company_dir = cases_root / company_id
        _create_company_structure(company_dir)
        _write_manifest(company_dir / "index_manifest.yml", company_id, name)

    _append_json(
        TEST_RUNTIME_CONFIG,
        {
            "configured": True,
            "company_count": len(cleaned_names),
            "configured_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def is_test_workspace_configured() -> bool:
    if not TEST_RUNTIME_CONFIG.exists():
        return False
    try:
        return bool(json.loads(TEST_RUNTIME_CONFIG.read_text(encoding="utf-8")).get("configured"))
    except json.JSONDecodeError:
        return False


def rename_test_company(company_id: str, display_name: str, aliases: str = "") -> None:
    cleaned_name = display_name.strip()
    if not cleaned_name:
        raise ValueError("Company name is required.")

    company_dir = TEST_ROOT / "cases" / company_id
    if not company_dir.exists():
        raise ValueError(f"Unknown test company_id: {company_id}")

    _write_manifest(company_dir / "index_manifest.yml", company_id, cleaned_name, _parse_aliases(aliases))


def remove_test_company(company_id: str) -> None:
    company_dir = TEST_ROOT / "cases" / company_id
    if not company_dir.exists():
        raise ValueError(f"Unknown test company_id: {company_id}")

    files = [path for path in company_dir.rglob("*") if path.is_file() and path.name != ".gitkeep"]
    files = [path for path in files if path.name != "index_manifest.yml"]
    if files:
        raise ValueError("Company contains test documents and cannot be removed.")

    shutil.rmtree(company_dir)


def ingest_application_file(
    source_path: Path,
    outcome: str,
    company_id: str = "external",
    external_company_name: str = "",
) -> ApplicationRecord:
    if outcome not in {"successful", "unsuccessful"}:
        raise ValueError("Outcome must be successful or unsuccessful.")
    if company_id not in {"external", "unknown"}:
        _validate_company(company_id)

    source_path = resolve_inside_root(source_path, PROJECT_ROOT)
    if not source_path.exists() or not source_path.is_file():
        raise FileNotFoundError(f"Application file not found: {source_path}")

    destination_dir = TEST_ROOT / "applications" / outcome
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination_path = _deduplicated_destination(destination_dir / source_path.name)
    file_hash = _sha256(source_path)
    file_size = source_path.stat().st_size
    preview = _extract_preview(source_path)

    shutil.move(str(source_path), str(destination_path))

    record = ApplicationRecord(
        status="indexed",
        source_path=str(source_path.relative_to(PROJECT_ROOT)),
        destination_path=str(destination_path.relative_to(PROJECT_ROOT)),
        outcome=outcome,
        company_id=company_id,
        external_company_name=external_company_name.strip(),
        sha256=file_hash,
        file_size_bytes=file_size,
        text_preview=preview,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    _append_jsonl(TEST_APPLICATION_INDEX, asdict(record))
    return record


def analyze_application_patterns() -> dict[str, object]:
    records = _read_jsonl(TEST_APPLICATION_INDEX)
    successful = [record for record in records if record.get("outcome") == "successful"]
    unsuccessful = [record for record in records if record.get("outcome") == "unsuccessful"]
    successful_terms = _top_terms(" ".join(str(record.get("text_preview", "")) for record in successful))
    unsuccessful_terms = _top_terms(" ".join(str(record.get("text_preview", "")) for record in unsuccessful))

    return {
        "successful_count": len(successful),
        "unsuccessful_count": len(unsuccessful),
        "successful_language_signals": successful_terms[:12],
        "unsuccessful_language_signals": unsuccessful_terms[:12],
        "grant_positive_only_terms": [term for term in successful_terms if term not in unsuccessful_terms][:8],
        "rejection_only_terms": [term for term in unsuccessful_terms if term not in successful_terms][:8],
    }


def _validate_local_write() -> None:
    decision = validate_action("local_write")
    if not decision.allowed:
        raise PermissionError(decision.reason)


def _validate_company(company_id: str) -> None:
    company_dir = TEST_ROOT / "cases" / company_id
    if not company_dir.exists():
        raise ValueError(f"Unknown test company_id: {company_id}")


def _validate_document_type(document_type: str) -> None:
    if document_type not in CATEGORY_TO_FOLDER:
        allowed = ", ".join(sorted(CATEGORY_TO_FOLDER))
        raise ValueError(f"Unknown document_type '{document_type}'. Allowed: {allowed}")


def _deduplicated_destination(destination_path: Path) -> Path:
    if not destination_path.exists():
        return destination_path

    stem = destination_path.stem
    suffix = destination_path.suffix
    parent = destination_path.parent
    counter = 2

    while True:
        candidate = parent / f"{stem}__v{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extract_preview(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".docx", ".xlsx", ".pptx"}:
        return _extract_office_preview(path)
    if suffix not in {".txt", ".md", ".csv"}:
        return "Preview extraction is available for text, docx, xlsx and pptx files in the test harness."

    text = path.read_text(encoding="utf-8", errors="replace")
    return " ".join(text.split())[:500]


def _extract_office_preview(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            text_parts = []
            for name in archive.namelist():
                if not _is_relevant_office_xml(name):
                    continue
                raw_xml = archive.read(name).decode("utf-8", errors="ignore")
                text_parts.append(_xml_text_preview(raw_xml))
            preview = " ".join(" ".join(text_parts).split())[:500]
            return preview or "No readable Office text found."
    except zipfile.BadZipFile:
        return "Office preview failed: file is not a valid zip-based Office document."


def _is_relevant_office_xml(name: str) -> bool:
    return (
        name.startswith("word/document")
        or name.startswith("xl/sharedStrings")
        or name.startswith("xl/worksheets")
        or name.startswith("ppt/slides")
    ) and name.endswith(".xml")


def _xml_text_preview(raw_xml: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", raw_xml)
    return html_unescape(without_tags)


def html_unescape(text: str) -> str:
    return (
        text.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&apos;", "'")
    )


def _suggestion_text(path: Path) -> str:
    parts = [_normalize_text(path.name)]
    if path.suffix.lower() in {".txt", ".md", ".csv"} and path.exists():
        parts.append(_normalize_text(_extract_preview(path)))
    return " ".join(parts)


def _suggest_company(text: str) -> tuple[str, int, str]:
    companies = list_test_companies()
    if not companies:
        return "company-01", 0, "No companies configured."

    normalized_text = _normalize_text(text)
    best_company = companies[0]
    best_score = 50
    best_reason = "Defaulted to first company; no strong company signal."

    for company in companies:
        if _normalize_text(company.company_id) in normalized_text:
            return company.company_id, 98, f"Company matched by id: {company.company_id}"

        for name_variant in _company_name_variants(company):
            if not name_variant:
                continue
            if name_variant in normalized_text:
                return company.company_id, 98, f"Company matched by configured name: {company.display_name}"

            token_score = _company_token_score(name_variant, normalized_text)
            if token_score > best_score:
                best_company = company
                best_score = token_score
                best_reason = f"Company partially matched configured name: {company.display_name}"

    return best_company.company_id, best_score, best_reason


def _suggest_document_type(text: str) -> tuple[str, int, str]:
    best_type = "raw_inbox"
    best_matches = 0
    matched_keywords: list[str] = []

    for document_type, keywords in DOCUMENT_KEYWORDS.items():
        matches = [keyword for keyword in keywords if keyword in text]
        if len(matches) > best_matches:
            best_type = document_type
            best_matches = len(matches)
            matched_keywords = matches

    if best_matches >= 2:
        return best_type, 98, f"Document type matched keywords: {', '.join(matched_keywords)}"
    if best_matches == 1:
        return best_type, 80, f"Document type matched keyword: {matched_keywords[0]}"
    return "raw_inbox", 40, "No strong document type signal."


def _create_company_structure(company_dir: Path) -> None:
    for folder in CATEGORY_TO_FOLDER.values():
        folder_path = company_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        (folder_path / ".gitkeep").touch()
    (company_dir / ".gitkeep").touch()


def _read_simple_manifest(path: Path) -> dict[str, str]:
    data = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def _write_manifest(path: Path, company_id: str, display_name: str, aliases: tuple[str, ...] = ()) -> None:
    resolve_inside_root(path, PROJECT_ROOT)
    path.write_text(
        "\n".join(
            [
                f"company_id: {company_id}",
                f"display_name: {display_name}",
                f"aliases: {', '.join(aliases)}",
                "short_description: Test environment case only.",
                "therapeutic_area: ",
                "technology_type: ",
                "product_stage: ",
                "trl: ",
                "regulatory_stage: ",
                "ip_status: ",
                "last_profile_update: ",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _parse_aliases(aliases: str) -> tuple[str, ...]:
    return tuple(alias.strip() for alias in aliases.split(",") if alias.strip())


def _company_name_variants(company: TestCompany) -> list[str]:
    names = [company.display_name, *company.aliases]
    variants = []
    for name in names:
        normalized = _normalize_text(name)
        compact = normalized.replace(" ", "")
        variants.extend([normalized, compact])
    return [variant for variant in variants if variant]


def _company_token_score(name_variant: str, normalized_text: str) -> int:
    tokens = [token for token in name_variant.split() if len(token) >= 3]
    if not tokens:
        return 50

    matches = [token for token in tokens if token in normalized_text]
    if not matches:
        return 50
    if len(matches) == len(tokens):
        return 95
    if len(matches) >= 2:
        return 85
    return 70


def _normalize_text(value: str) -> str:
    lowered = value.lower()
    normalized = re.sub(r"[^a-z0-9æøå]+", " ", lowered)
    return " ".join(normalized.split())


def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
    resolve_inside_root(path, PROJECT_ROOT)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=True) + "\n")


def _append_json(path: Path, payload: dict[str, object]) -> None:
    resolve_inside_root(path, PROJECT_ROOT)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def _top_terms(text: str) -> list[str]:
    words = re.findall(r"[a-zA-ZæøåÆØÅ]{4,}", text.lower())
    counts: dict[str, int] = {}
    for word in words:
        if word in WRITING_STOPWORDS:
            continue
        counts[word] = counts.get(word, 0) + 1
    return [word for word, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest files in the local test environment.")
    parser.add_argument("--list", action="store_true", help="List files waiting in the test inbox.")
    parser.add_argument("--file", help="Filename in funding-assistant-test/system/inbox.")
    parser.add_argument("--company", help="Test company id, e.g. company-01.")
    parser.add_argument("--document-type", choices=sorted(CATEGORY_TO_FOLDER), help="Document category.")
    args = parser.parse_args()

    if args.list:
        for filename in list_test_inbox():
            print(filename)
        return

    if not args.file or not args.company or not args.document_type:
        parser.error("--file, --company and --document-type are required unless --list is used.")

    result = ingest_test_file(args.file, args.company, args.document_type)
    print(json.dumps(asdict(result), indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
