from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from funding_assistant.policy import resolve_inside_root, validate_action


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_ROOT = PROJECT_ROOT / "funding-assistant-test"
TEST_INBOX = TEST_ROOT / "system" / "inbox"
TEST_INDEX = TEST_ROOT / "system" / "index" / "documents-index.jsonl"
TEST_EVENTS = TEST_ROOT / "system" / "logs" / "ingestion-events.jsonl"

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
    if path.suffix.lower() not in {".txt", ".md", ".csv"}:
        return "Preview extraction is available for text-like files in the test harness."

    text = path.read_text(encoding="utf-8", errors="replace")
    return " ".join(text.split())[:500]


def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
    resolve_inside_root(path, PROJECT_ROOT)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=True) + "\n")


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

