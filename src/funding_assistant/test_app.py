from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from typing import Annotated, Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from funding_assistant.policy import resolve_inside_root
from funding_assistant.test_ingestion import (
    CATEGORY_TO_FOLDER,
    PROJECT_ROOT,
    TEST_EVENTS,
    TEST_INBOX,
    TEST_INDEX,
    TEST_ROOT,
    add_test_company,
    analyze_application_patterns,
    configure_test_workspace,
    ingest_application_file,
    ingest_test_file,
    is_test_workspace_configured,
    list_test_inbox,
    list_test_companies,
    remove_test_company,
    rename_test_company,
    suggest_indexing,
)


app = FastAPI(title="Local Funding Assistant Test Dashboard")


@app.get("/", response_class=HTMLResponse)
def dashboard(message: Optional[str] = None, error: Optional[str] = None) -> str:
    if not is_test_workspace_configured():
        return onboarding(message=message, error=error)

    inbox_files = list_test_inbox()
    companies = list_test_companies()
    index_records = _read_jsonl(TEST_INDEX, limit=15)
    writing_patterns = analyze_application_patterns()
    application_summary = (
        f"{writing_patterns.get('successful_count', 0)} successful / "
        f"{writing_patterns.get('unsuccessful_count', 0)} unsuccessful"
    )

    return _page(
        title="Test Dashboard",
        body=f"""
        {_notice(message, "success")}
        {_notice(error, "error")}

        <section class="dashboard-grid">
          {_nav_card("Uploads", "/upload", f"{len(inbox_files)} filer afventer", "Upload, bulk-allokation og indexing.")}
          {_nav_card("Ansogninger", "/applications", application_summary, "Skriveagent og application patterns.")}
          {_nav_card("Virksomheder", "/companies", f"{len(companies)} aktive", "Navne, aliases og projektakronymer.")}
          {_nav_card("Database", "/database", f"{len(index_records)} seneste records", "Index records og event log.")}
          {_nav_card("System", "/system", "Local only", "Status, sikkerhedsregler og schedule.")}
        </section>
        """,
        active="dashboard",
    )


@app.get("/upload", response_class=HTMLResponse)
def upload_page(message: Optional[str] = None, error: Optional[str] = None) -> str:
    if not is_test_workspace_configured():
        return onboarding(message=message, error=error)

    inbox_files = list_test_inbox()
    companies = list_test_companies()
    suggestions = [suggest_indexing(filename) for filename in inbox_files]

    return _page(
        title="Upload",
        body=f"""
        {_notice(message, "success")}
        {_notice(error, "error")}

        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>Dropzone</h2>
              <p>Upload testfiler til den lokale test-inbox. Ingen API-kald, ingen ekstern deling.</p>
            </div>
            <span class="badge">{len(inbox_files)} filer venter</span>
          </div>

          <form id="upload-form" class="drop-form" action="/upload" method="post" enctype="multipart/form-data">
            <label id="dropzone" class="dropzone">
              <input id="file-input" type="file" name="files" multiple>
              <strong>Traek filer hertil</strong>
              <span>eller klik for at vaelge filer</span>
            </label>
            <button type="submit">Upload til test-inbox</button>
          </form>
        </section>

        <section class="grid">
          <div class="panel">
            <h2>Inbox</h2>
            {_inbox_table(inbox_files)}
          </div>
          <div class="panel">
            <h2>Index file</h2>
            {_ingest_form(inbox_files, companies)}
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>Bekraeft allokation</h2>
              <p>Dokumenter under 95% sikkerhed bliver liggende her, indtil du bekraefter placeringen.</p>
            </div>
            <span class="badge">{len(suggestions)} forslag</span>
          </div>
          {_bulk_allocation_form(suggestions, companies)}
        </section>
        """,
        active="upload",
    )


@app.get("/companies", response_class=HTMLResponse)
def companies_page(message: Optional[str] = None, error: Optional[str] = None) -> str:
    if not is_test_workspace_configured():
        return onboarding(message=message, error=error)

    companies = list_test_companies()
    return _page(
        title="Virksomheder",
        body=f"""
        {_notice(message, "success")}
        {_notice(error, "error")}

        <section class="panel">
          <h2>Virksomheder</h2>
          {_companies_panel(companies)}
        </section>
        """,
        active="companies",
    )


@app.get("/applications", response_class=HTMLResponse)
def applications_page(message: Optional[str] = None, error: Optional[str] = None) -> str:
    if not is_test_workspace_configured():
        return onboarding(message=message, error=error)

    companies = list_test_companies()
    writing_patterns = analyze_application_patterns()
    return _page(
        title="Ansogninger",
        body=f"""
        {_notice(message, "success")}
        {_notice(error, "error")}

        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>Skriveagent</h2>
              <p>Upload successfulde og ikke-successfulde funding applications. De kan kobles til en intern virksomhed eller markeres som ekstern/ukendt.</p>
            </div>
            <span class="badge">Local language analysis</span>
          </div>
          {_application_upload_form(companies)}
          {_writing_patterns_panel(writing_patterns)}
        </section>
        """,
        active="applications",
    )


@app.get("/database", response_class=HTMLResponse)
def database_page(message: Optional[str] = None, error: Optional[str] = None) -> str:
    if not is_test_workspace_configured():
        return onboarding(message=message, error=error)

    index_records = _read_jsonl(TEST_INDEX, limit=25)
    event_records = _read_jsonl(TEST_EVENTS, limit=25)
    return _page(
        title="Database",
        body=f"""
        {_notice(message, "success")}
        {_notice(error, "error")}

        <section class="grid">
          <div class="panel">
            <h2>Index records</h2>
            {_records_table(index_records)}
          </div>
          <div class="panel">
            <h2>Events</h2>
            {_records_table(event_records)}
          </div>
        </section>
        """,
        active="database",
    )


@app.get("/system", response_class=HTMLResponse)
def system_page(message: Optional[str] = None, error: Optional[str] = None) -> str:
    configured = is_test_workspace_configured()
    companies = list_test_companies() if configured else []
    return _page(
        title="System",
        body=f"""
        {_notice(message, "success")}
        {_notice(error, "error")}

        <section class="grid">
          <div class="panel">
            <h2>Status</h2>
            <table>
              <tbody>
                <tr><th>Environment</th><td>Test</td></tr>
                <tr><th>Access</th><td>127.0.0.1 local only</td></tr>
                <tr><th>API</th><td>Off in test dashboard</td></tr>
                <tr><th>External sharing</th><td>Off</td></tr>
                <tr><th>Companies</th><td>{len(companies)}</td></tr>
              </tbody>
            </table>
          </div>
          <div class="panel">
            <h2>Schedules</h2>
            <table>
              <tbody>
                <tr><th>Softfunding scraper</th><td>Weekly, Monday 07:00 Europe/Copenhagen</td></tr>
                <tr><th>Deadline reminders</th><td>30, 14, 7 and 3 days before deadline</td></tr>
              </tbody>
            </table>
          </div>
        </section>
        """,
        active="system",
    )


@app.get("/setup", response_class=HTMLResponse)
def onboarding(message: Optional[str] = None, error: Optional[str] = None) -> str:
    return _page(
        title="Setup",
        body=f"""
        {_notice(message, "success")}
        {_notice(error, "error")}
        <section class="panel setup-panel">
          <h2>Foerste setup</h2>
          <p>Vaelg om testmiljoeet skal haandtere information for en eller flere virksomheder.</p>
          <form class="stack" action="/setup" method="post">
            <label>Antal virksomheder
              <input id="company-count" name="company_count" type="number" min="1" max="25" value="1">
            </label>
            <div id="company-name-fields" class="stack">
              <label>Virksomhed 1
                <input name="company_names" placeholder="Virksomhedsnavn" required>
              </label>
            </div>
            <button type="submit">Opret testmiljoe</button>
          </form>
        </section>
        """,
    )


@app.post("/setup")
def setup_workspace(
    company_count: Annotated[int, Form()],
    company_names: Annotated[list[str], Form()],
) -> RedirectResponse:
    names = [name.strip() for name in company_names[:company_count] if name.strip()]
    if len(names) != company_count:
        return _redirect(error="Udfyld navn for alle virksomheder.")

    try:
        configure_test_workspace(names)
    except ValueError as exc:
        return _redirect(error=str(exc))
    return _redirect(message=f"Testmiljoe oprettet med {len(names)} virksomhed(er).")


@app.post("/upload")
def upload(files: Annotated[list[UploadFile], File()]) -> RedirectResponse:
    if not files:
        return _redirect(error="Ingen filer valgt.")

    uploaded = 0
    auto_indexed = 0
    for upload_file in files:
        if not upload_file.filename:
            continue

        safe_name = Path(upload_file.filename).name
        destination = _deduplicated_inbox_path(TEST_INBOX / safe_name)
        resolve_inside_root(destination, PROJECT_ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)

        with destination.open("wb") as output:
            shutil.copyfileobj(upload_file.file, output)
        uploaded += 1

        suggestion = suggest_indexing(destination.name)
        if suggestion.auto_index:
            ingest_test_file(destination.name, suggestion.suggested_company_id, suggestion.suggested_document_type)
            auto_indexed += 1

    pending = uploaded - auto_indexed
    return _redirect(message=f"{uploaded} fil(er) uploadet. {auto_indexed} auto-indekseret, {pending} afventer bekraeftelse.")


@app.post("/applications/upload")
def upload_application(
    file: Annotated[UploadFile, File()],
    outcome: Annotated[str, Form()],
    company_id: Annotated[str, Form()],
    external_company_name: Annotated[str, Form()] = "",
) -> RedirectResponse:
    if not file.filename:
        return _redirect(error="Ingen application-fil valgt.")

    safe_name = Path(file.filename).name
    staging_dir = TEST_ROOT / "system" / "inbox" / "applications"
    staging_path = _deduplicated_inbox_path(staging_dir / safe_name)
    resolve_inside_root(staging_path, PROJECT_ROOT)
    staging_path.parent.mkdir(parents=True, exist_ok=True)

    with staging_path.open("wb") as output:
        shutil.copyfileobj(file.file, output)

    try:
        record = ingest_application_file(staging_path, outcome, company_id, external_company_name)
    except (FileNotFoundError, PermissionError, ValueError) as exc:
        return _redirect(error=str(exc))

    return _redirect(message=f"Application indekseret: {record.outcome} / {record.company_id}")


@app.post("/ingest")
def ingest(
    filename: Annotated[str, Form()],
    company_id: Annotated[str, Form()],
    document_type: Annotated[str, Form()],
) -> RedirectResponse:
    try:
        result = ingest_test_file(filename, company_id, document_type)
    except (FileNotFoundError, PermissionError, ValueError) as exc:
        return _redirect(error=str(exc))

    return _redirect(message=f"Indekseret: {result.destination_path}")


@app.post("/bulk-ingest")
def bulk_ingest(
    filenames: Annotated[list[str], Form()],
    company_ids: Annotated[list[str], Form()],
    document_types: Annotated[list[str], Form()],
) -> RedirectResponse:
    if not (len(filenames) == len(company_ids) == len(document_types)):
        return _redirect(error="Allokationsformularen er inkonsistent.")

    indexed = 0
    errors = []
    for filename, company_id, document_type in zip(filenames, company_ids, document_types):
        try:
            ingest_test_file(filename, company_id, document_type)
            indexed += 1
        except (FileNotFoundError, PermissionError, ValueError) as exc:
            errors.append(f"{filename}: {exc}")

    if errors:
        return _redirect(error=f"{indexed} indekseret. Fejl: {' | '.join(errors)}")
    return _redirect(message=f"{indexed} fil(er) indekseret efter bekraeftelse.")


@app.post("/inbox/delete")
def delete_inbox_file(filename: Annotated[str, Form()]) -> RedirectResponse:
    try:
        path = resolve_inside_root(TEST_INBOX / filename, PROJECT_ROOT)
        if path.exists() and path.is_file():
            path.unlink()
    except ValueError as exc:
        return _redirect(error=str(exc))
    return _redirect(message=f"Slettet fra inbox: {filename}")


@app.post("/files/delete")
def delete_test_file(relative_path: Annotated[str, Form()]) -> RedirectResponse:
    try:
        path = resolve_inside_root(PROJECT_ROOT / relative_path, PROJECT_ROOT)
        if TEST_ROOT not in path.parents:
            raise ValueError("Only test environment files can be deleted here.")
        if path.exists() and path.is_file():
            path.unlink()
    except ValueError as exc:
        return _redirect(error=str(exc))
    return _redirect(message=f"Slettet testfil: {relative_path}")


@app.post("/companies/add")
def add_company(display_name: Annotated[str, Form()], aliases: Annotated[str, Form()] = "") -> RedirectResponse:
    try:
        company = add_test_company(display_name, aliases)
    except ValueError as exc:
        return _redirect(error=str(exc))
    return _redirect(message=f"Tilfoejet virksomhed: {company.display_name} ({company.company_id})")


@app.post("/companies/rename")
def rename_company(
    company_id: Annotated[str, Form()],
    display_name: Annotated[str, Form()],
    aliases: Annotated[str, Form()] = "",
) -> RedirectResponse:
    try:
        rename_test_company(company_id, display_name, aliases)
    except ValueError as exc:
        return _redirect(error=str(exc))
    return _redirect(message=f"Omdobt {company_id} til {display_name.strip()}")


@app.post("/companies/remove")
def remove_company(company_id: Annotated[str, Form()]) -> RedirectResponse:
    try:
        remove_test_company(company_id)
    except ValueError as exc:
        return _redirect(error=str(exc))
    return _redirect(message=f"Fjernet virksomhed: {company_id}")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": "test"}


def _redirect(message: Optional[str] = None, error: Optional[str] = None) -> RedirectResponse:
    query = []
    if message:
        query.append(f"message={_query_escape(message)}")
    if error:
        query.append(f"error={_query_escape(error)}")
    suffix = f"?{'&'.join(query)}" if query else ""
    return RedirectResponse(url=f"/{suffix}", status_code=303)


def _page(title: str, body: str, active: str = "") -> str:
    nav_items = [
        ("dashboard", "Dashboard", "/"),
        ("upload", "Uploads", "/upload"),
        ("applications", "Ansogninger", "/applications"),
        ("companies", "Virksomheder", "/companies"),
        ("database", "Database", "/database"),
        ("system", "System", "/system"),
    ]
    nav = "".join(
        f'<a class="{"active" if key == active else ""}" href="{href}">{label}</a>'
        for key, label, href in nav_items
    )
    return f"""
    <!doctype html>
    <html lang="da">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{html.escape(title)}</title>
        <style>{_css()}</style>
      </head>
      <body>
        <main>
          <header class="hero">
            <div>
              <p class="eyebrow">Local Funding Assistant</p>
              <h1>Testmiljoe</h1>
              <p>Samme ingestion-flow som systemet, men isoleret til testdata.</p>
            </div>
            <div class="status-card">
              <span>Mode</span>
              <strong>Local test only</strong>
              <small>API: off · Sharing: off · Slack: disabled</small>
            </div>
          </header>
          <nav class="top-nav" aria-label="Dashboard navigation">
            {nav}
          </nav>
          {body}
        </main>
        <script>{_javascript()}</script>
      </body>
    </html>
    """


def _nav_card(title: str, href: str, metric: str, description: str) -> str:
    return f"""
    <a class="nav-card" href="{html.escape(href)}">
      <span>{html.escape(metric)}</span>
      <strong>{html.escape(title)}</strong>
      <small>{html.escape(description)}</small>
    </a>
    """


def _notice(text: Optional[str], kind: str) -> str:
    if not text:
        return ""
    return f'<div class="notice {kind}">{html.escape(text)}</div>'


def _inbox_table(filenames: list[str]) -> str:
    if not filenames:
        return '<p class="muted">Ingen filer i test-inbox.</p>'

    rows = "".join(
        "<tr>"
        f"<td>{html.escape(name)}</td>"
        "<td>"
        '<form action="/inbox/delete" method="post" onsubmit="return confirm(\'Slet fil fra test-inbox?\')">'
        f'<input type="hidden" name="filename" value="{html.escape(name)}">'
        '<button class="secondary danger" type="submit">Slet</button>'
        "</form>"
        "</td>"
        "</tr>"
        for name in filenames
    )
    return f"<table><thead><tr><th>Filnavn</th><th></th></tr></thead><tbody>{rows}</tbody></table>"


def _companies_panel(companies: list[object]) -> str:
    rows = []
    for company in companies:
        rows.append(
            "<tr>"
            f"<td>{html.escape(company.company_id)}</td>"
            "<td>"
            '<form class="inline-form" action="/companies/rename" method="post">'
            f'<input type="hidden" name="company_id" value="{html.escape(company.company_id)}">'
            f'<input name="display_name" value="{html.escape(company.display_name)}">'
            f'<input name="aliases" value="{html.escape(", ".join(company.aliases))}" placeholder="Akronymer/aliases">'
            '<button type="submit">Gem</button>'
            "</form>"
            "</td>"
            "<td>"
            '<form action="/companies/remove" method="post" onsubmit="return confirm(\'Fjern virksomheden fra testmiljoeet?\')">'
            f'<input type="hidden" name="company_id" value="{html.escape(company.company_id)}">'
            '<button class="secondary danger" type="submit">Fjern</button>'
            "</form>"
            "</td>"
            "</tr>"
        )

    table = "<table><thead><tr><th>ID</th><th>Navn</th><th></th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    return (
        table
        + """
        <form class="inline-form add-company" action="/companies/add" method="post">
          <input name="display_name" placeholder="Ny virksomhed">
          <input name="aliases" placeholder="Projektakronymer/aliases">
          <button type="submit">Tilfoej</button>
        </form>
        """
    )


def _bulk_allocation_form(suggestions: list[object], companies: list[object]) -> str:
    if not suggestions:
        return '<p class="muted">Ingen filer afventer allokation.</p>'

    rows = []
    for suggestion in suggestions:
        company_options = _company_options(companies, suggestion.suggested_company_id)
        type_options = _document_type_options(suggestion.suggested_document_type)
        confidence_class = "high-confidence" if suggestion.confidence >= 95 else "needs-review"
        rows.append(
            "<tr>"
            f"<td><input type=\"hidden\" name=\"filenames\" value=\"{html.escape(suggestion.filename)}\">{html.escape(suggestion.filename)}</td>"
            f"<td><select name=\"company_ids\">{company_options}</select></td>"
            f"<td><select name=\"document_types\">{type_options}</select></td>"
            f"<td><span class=\"confidence {confidence_class}\">{suggestion.confidence}%</span></td>"
            f"<td>{html.escape(suggestion.rationale)}</td>"
            "<td>"
            '<button class="secondary danger row-delete" type="submit" formmethod="post" formaction="/inbox/delete" '
            f'name="filename" value="{html.escape(suggestion.filename)}">Slet</button>'
            "</td>"
            "</tr>"
        )

    return (
        '<form action="/bulk-ingest" method="post" onsubmit="return confirm(\'Bekraeft allokation for alle viste dokumenter?\')">'
        "<table><thead><tr><th>Dokument</th><th>Virksomhed</th><th>Dokumenttype</th><th>Sikkerhed</th><th>Grundlag</th><th></th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        '<button type="submit">Bekraeft allokation</button>'
        "</form>"
    )


def _application_upload_form(companies: list[object]) -> str:
    company_options = _company_options(companies)
    company_options += '<option value="external">External company</option><option value="unknown">Unknown/not linked</option>'
    return f"""
    <form class="stack application-form" action="/applications/upload" method="post" enctype="multipart/form-data">
      <label>Application file
        <input type="file" name="file" required>
      </label>
      <label>Outcome
        <select name="outcome">
          <option value="successful">Successful / grant</option>
          <option value="unsuccessful">Unsuccessful / rejected</option>
        </select>
      </label>
      <label>Virksomhed
        <select name="company_id">{company_options}</select>
      </label>
      <label>Ekstern virksomhedsnavn, hvis relevant
        <input name="external_company_name" placeholder="Kun hvis den ikke findes i systemet">
      </label>
      <button type="submit">Upload application</button>
    </form>
    """


def _writing_patterns_panel(patterns: dict[str, object]) -> str:
    successful_terms = ", ".join(str(term) for term in patterns.get("successful_language_signals", [])) or "Ingen endnu"
    unsuccessful_terms = ", ".join(str(term) for term in patterns.get("unsuccessful_language_signals", [])) or "Ingen endnu"
    positive_only = ", ".join(str(term) for term in patterns.get("grant_positive_only_terms", [])) or "Ingen endnu"
    rejection_only = ", ".join(str(term) for term in patterns.get("rejection_only_terms", [])) or "Ingen endnu"
    return f"""
    <div class="pattern-grid">
      <div>
        <h3>Successful ({patterns.get("successful_count", 0)})</h3>
        <p>{html.escape(successful_terms)}</p>
      </div>
      <div>
        <h3>Unsuccessful ({patterns.get("unsuccessful_count", 0)})</h3>
        <p>{html.escape(unsuccessful_terms)}</p>
      </div>
      <div>
        <h3>Grant-positive only</h3>
        <p>{html.escape(positive_only)}</p>
      </div>
      <div>
        <h3>Rejected only</h3>
        <p>{html.escape(rejection_only)}</p>
      </div>
    </div>
    """


def _ingest_form(filenames: list[str], companies: list[object]) -> str:
    if not filenames:
        return '<p class="muted">Upload en fil foerst.</p>'

    file_options = "".join(f'<option value="{html.escape(name)}">{html.escape(name)}</option>' for name in filenames)
    company_options = _company_options(companies)
    type_options = _document_type_options()

    return f"""
    <form class="stack" action="/ingest" method="post">
      <label>Fil
        <select name="filename">{file_options}</select>
      </label>
      <label>Virksomhed
        <select name="company_id">{company_options}</select>
      </label>
      <label>Dokumenttype
        <select name="document_type">{type_options}</select>
      </label>
      <button type="submit">Index file</button>
    </form>
    """


def _company_options(companies: list[object], selected_company_id: str = "") -> str:
    options = []
    for company in companies:
        selected = " selected" if company.company_id == selected_company_id else ""
        label = f"{company.company_id} - {company.display_name}"
        options.append(f'<option value="{html.escape(company.company_id)}"{selected}>{html.escape(label)}</option>')
    return "".join(options)


def _document_type_options(selected_document_type: str = "") -> str:
    options = []
    for document_type in sorted(CATEGORY_TO_FOLDER):
        selected = " selected" if document_type == selected_document_type else ""
        options.append(f'<option value="{html.escape(document_type)}"{selected}>{html.escape(document_type)}</option>')
    return "".join(options)


def _records_table(records: list[dict[str, object]]) -> str:
    if not records:
        return '<p class="muted">Ingen records endnu.</p>'

    rows = []
    for record in records:
        primary = record.get("destination_path") or record.get("event_type") or record.get("status") or "record"
        secondary = record.get("company_id") or ""
        created_at = record.get("created_at") or ""
        delete_button = ""
        if record.get("destination_path"):
            destination_path = html.escape(str(record.get("destination_path")))
            delete_button = (
                '<form action="/files/delete" method="post" onsubmit="return confirm(\'Slet fysisk testfil?\')">'
                f'<input type="hidden" name="relative_path" value="{destination_path}">'
                '<button class="secondary danger" type="submit">Slet fil</button>'
                "</form>"
            )
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(primary))}</td>"
            f"<td>{html.escape(str(secondary))}</td>"
            f"<td>{html.escape(str(created_at))}</td>"
            f"<td>{delete_button}</td>"
            "</tr>"
        )
    return "<table><thead><tr><th>Record</th><th>Company</th><th>Created</th><th></th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"


def _read_jsonl(path: Path, limit: int) -> list[dict[str, object]]:
    if not path.exists():
        return []

    lines = path.read_text(encoding="utf-8").splitlines()
    records = []
    for line in reversed(lines[-limit:]):
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def _deduplicated_inbox_path(destination_path: Path) -> Path:
    if not destination_path.exists():
        return destination_path

    stem = destination_path.stem
    suffix = destination_path.suffix
    parent = destination_path.parent
    counter = 2

    while True:
        candidate = parent / f"{stem}__upload{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _query_escape(value: str) -> str:
    from urllib.parse import quote

    return quote(value, safe="")


def _javascript() -> str:
    return """
    const form = document.getElementById("upload-form");
    const input = document.getElementById("file-input");
    const dropzone = document.getElementById("dropzone");

    if (form && input && dropzone) {
      const submitIfFilesSelected = () => {
        if (input.files && input.files.length > 0) {
          form.submit();
        }
      };

      input.addEventListener("change", submitIfFilesSelected);

      ["dragenter", "dragover"].forEach((eventName) => {
        dropzone.addEventListener(eventName, (event) => {
          event.preventDefault();
          event.stopPropagation();
          dropzone.classList.add("is-dragging");
        });
      });

      ["dragleave", "drop"].forEach((eventName) => {
        dropzone.addEventListener(eventName, (event) => {
          event.preventDefault();
          event.stopPropagation();
          dropzone.classList.remove("is-dragging");
        });
      });

      dropzone.addEventListener("drop", (event) => {
        const files = event.dataTransfer.files;
        if (!files || files.length === 0) {
          return;
        }

        const transfer = new DataTransfer();
        Array.from(files).forEach((file) => transfer.items.add(file));
        input.files = transfer.files;
        submitIfFilesSelected();
      });
    }

    const companyCount = document.getElementById("company-count");
    const companyFields = document.getElementById("company-name-fields");
    if (companyCount && companyFields) {
      const renderCompanyFields = () => {
        const count = Math.max(1, Math.min(25, parseInt(companyCount.value || "1", 10)));
        const existing = Array.from(companyFields.querySelectorAll("input")).map((field) => field.value);
        companyFields.innerHTML = "";
        for (let index = 0; index < count; index += 1) {
          const label = document.createElement("label");
          label.textContent = `Virksomhed ${index + 1}`;
          const input = document.createElement("input");
          input.name = "company_names";
          input.required = true;
          input.placeholder = "Virksomhedsnavn";
          input.value = existing[index] || "";
          label.appendChild(input);
          companyFields.appendChild(label);
        }
      };
      companyCount.addEventListener("input", renderCompanyFields);
    }
    """


def _css() -> str:
    return """
    :root {
      --bg: #f4f1e8;
      --ink: #17211c;
      --muted: #68726b;
      --panel: #fffdf7;
      --line: #d7d0c1;
      --accent: #0f6b57;
      --accent-2: #b94b31;
      --shadow: 0 18px 48px rgba(23, 33, 28, 0.10);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      background:
        linear-gradient(135deg, rgba(15, 107, 87, 0.10), transparent 38%),
        linear-gradient(315deg, rgba(185, 75, 49, 0.10), transparent 34%),
        var(--bg);
      color: var(--ink);
      font-family: Avenir Next, Charter, Georgia, sans-serif;
    }
    main { width: min(1180px, calc(100vw - 32px)); margin: 0 auto; padding: 32px 0 56px; }
    .hero { display: flex; justify-content: space-between; gap: 24px; align-items: end; margin-bottom: 24px; }
    .eyebrow { margin: 0 0 8px; color: var(--accent); text-transform: uppercase; font-size: 12px; letter-spacing: 0; font-weight: 700; }
    h1 { margin: 0; font-size: 42px; line-height: 1.05; }
    h2 { margin: 0 0 14px; font-size: 20px; }
    h3 { margin: 0 0 8px; font-size: 15px; }
    p { color: var(--muted); }
    .status-card, .panel { background: rgba(255, 253, 247, 0.92); border: 1px solid var(--line); box-shadow: var(--shadow); border-radius: 8px; }
    .status-card { padding: 16px; min-width: 260px; }
    .status-card span, .status-card small { display: block; color: var(--muted); }
    .status-card strong { display: block; margin: 6px 0; }
    .top-nav { display: flex; flex-wrap: wrap; gap: 8px; margin: -8px 0 22px; }
    .top-nav a { border: 1px solid var(--line); border-radius: 999px; color: var(--ink); background: rgba(255, 253, 247, 0.74); padding: 9px 13px; text-decoration: none; font-weight: 700; }
    .top-nav a.active { background: var(--accent); border-color: var(--accent); color: white; }
    .panel { padding: 20px; margin-bottom: 18px; }
    .panel-header { display: flex; justify-content: space-between; gap: 18px; align-items: start; }
    .badge { border: 1px solid var(--line); border-radius: 999px; padding: 6px 10px; color: var(--accent); white-space: nowrap; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
    .dashboard-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 14px; }
    .nav-card { min-height: 150px; display: grid; align-content: space-between; gap: 12px; background: rgba(255, 253, 247, 0.92); border: 1px solid var(--line); border-radius: 10px; box-shadow: var(--shadow); padding: 18px; color: var(--ink); text-decoration: none; transition: transform 140ms ease, border-color 140ms ease, box-shadow 140ms ease; }
    .nav-card:hover { transform: translateY(-2px); border-color: rgba(15, 107, 87, 0.55); box-shadow: 0 22px 54px rgba(23, 33, 28, 0.14); }
    .nav-card span { color: var(--accent); font-size: 12px; font-weight: 800; text-transform: uppercase; }
    .nav-card strong { font-size: 20px; }
    .nav-card small { color: var(--muted); line-height: 1.35; }
    .drop-form { display: grid; gap: 14px; }
    .dropzone { border: 2px dashed #9f9a8d; border-radius: 8px; padding: 32px; display: grid; place-items: center; gap: 6px; text-align: center; cursor: pointer; background: #fbf7ec; transition: border-color 140ms ease, background 140ms ease, transform 140ms ease; }
    .dropzone.is-dragging { border-color: var(--accent); background: #e7f3ee; transform: translateY(-1px); }
    .dropzone input { display: none; }
    .dropzone span { color: var(--muted); }
    .stack { display: grid; gap: 14px; }
    label { display: grid; gap: 7px; color: var(--muted); font-size: 14px; }
    select, button, input { min-height: 42px; border-radius: 6px; border: 1px solid var(--line); font: inherit; }
    select, input { background: white; color: var(--ink); padding: 0 10px; width: 100%; }
    button { background: var(--accent); color: white; border: 0; font-weight: 700; cursor: pointer; padding: 0 16px; }
    button.secondary { background: #e9e3d5; color: var(--ink); }
    button.danger { color: #8a2616; }
    .inline-form { display: flex; gap: 8px; align-items: center; }
    .inline-form input { min-width: 160px; }
    .add-company { margin-top: 14px; }
    .application-form { margin-bottom: 18px; }
    .pattern-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
    .pattern-grid > div { border: 1px solid var(--line); border-radius: 8px; padding: 12px; background: #fbf7ec; }
    .setup-panel { max-width: 760px; }
    .confidence { display: inline-flex; align-items: center; min-width: 54px; justify-content: center; border-radius: 999px; padding: 5px 8px; font-weight: 700; }
    .confidence.high-confidence { background: #e7f3ee; color: #0e513f; }
    .confidence.needs-review { background: #f8e4dd; color: #7c2d1c; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th, td { border-bottom: 1px solid var(--line); text-align: left; padding: 10px 6px; vertical-align: top; }
    th { color: var(--muted); font-weight: 700; }
    .muted { color: var(--muted); }
    .notice { border-radius: 8px; padding: 12px 14px; margin-bottom: 16px; border: 1px solid var(--line); }
    .notice.success { background: #e7f3ee; color: #0e513f; }
    .notice.error { background: #f8e4dd; color: #7c2d1c; }

    @media (max-width: 820px) {
      main { width: min(100vw - 20px, 1180px); padding-top: 18px; }
      .hero, .grid, .panel-header, .pattern-grid, .dashboard-grid { display: grid; grid-template-columns: 1fr; }
      h1 { font-size: 34px; }
      .status-card { min-width: 0; }
    }
    """
