from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from typing import Annotated, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from funding_assistant.policy import resolve_inside_root
from funding_assistant.test_ingestion import (
    CATEGORY_TO_FOLDER,
    PROJECT_ROOT,
    TEST_EVENTS,
    TEST_INBOX,
    TEST_INDEX,
    TEST_ROOT,
    ingest_test_file,
    list_test_inbox,
)


app = FastAPI(title="Local Funding Assistant Test Dashboard")


@app.get("/", response_class=HTMLResponse)
def dashboard(message: Optional[str] = None, error: Optional[str] = None) -> str:
    inbox_files = list_test_inbox()
    index_records = _read_jsonl(TEST_INDEX, limit=15)
    event_records = _read_jsonl(TEST_EVENTS, limit=15)

    return _page(
        title="Test Dashboard",
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

          <form class="drop-form" action="/upload" method="post" enctype="multipart/form-data">
            <label class="dropzone">
              <input type="file" name="files" multiple>
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
            {_ingest_form(inbox_files)}
          </div>
        </section>

        <section class="grid">
          <div class="panel">
            <h2>Seneste index records</h2>
            {_records_table(index_records)}
          </div>
          <div class="panel">
            <h2>Seneste events</h2>
            {_records_table(event_records)}
          </div>
        </section>
        """,
    )


@app.post("/upload")
def upload(files: Annotated[list[UploadFile], File()]) -> RedirectResponse:
    if not files:
        return _redirect(error="Ingen filer valgt.")

    uploaded = 0
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

    return _redirect(message=f"{uploaded} fil(er) uploadet til test-inbox.")


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


def _page(title: str, body: str) -> str:
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
          {body}
        </main>
      </body>
    </html>
    """


def _notice(text: Optional[str], kind: str) -> str:
    if not text:
        return ""
    return f'<div class="notice {kind}">{html.escape(text)}</div>'


def _inbox_table(filenames: list[str]) -> str:
    if not filenames:
        return '<p class="muted">Ingen filer i test-inbox.</p>'

    rows = "".join(f"<tr><td>{html.escape(name)}</td></tr>" for name in filenames)
    return f"<table><thead><tr><th>Filnavn</th></tr></thead><tbody>{rows}</tbody></table>"


def _ingest_form(filenames: list[str]) -> str:
    if not filenames:
        return '<p class="muted">Upload en fil foerst.</p>'

    file_options = "".join(f'<option value="{html.escape(name)}">{html.escape(name)}</option>' for name in filenames)
    company_options = "".join(
        f'<option value="company-{index:02d}">company-{index:02d}</option>' for index in range(1, 9)
    )
    type_options = "".join(
        f'<option value="{html.escape(document_type)}">{html.escape(document_type)}</option>'
        for document_type in sorted(CATEGORY_TO_FOLDER)
    )

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


def _records_table(records: list[dict[str, object]]) -> str:
    if not records:
        return '<p class="muted">Ingen records endnu.</p>'

    rows = []
    for record in records:
        primary = record.get("destination_path") or record.get("event_type") or record.get("status") or "record"
        secondary = record.get("company_id") or ""
        created_at = record.get("created_at") or ""
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(primary))}</td>"
            f"<td>{html.escape(str(secondary))}</td>"
            f"<td>{html.escape(str(created_at))}</td>"
            "</tr>"
        )
    return "<table><thead><tr><th>Record</th><th>Company</th><th>Created</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"


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
    p { color: var(--muted); }
    .status-card, .panel { background: rgba(255, 253, 247, 0.92); border: 1px solid var(--line); box-shadow: var(--shadow); border-radius: 8px; }
    .status-card { padding: 16px; min-width: 260px; }
    .status-card span, .status-card small { display: block; color: var(--muted); }
    .status-card strong { display: block; margin: 6px 0; }
    .panel { padding: 20px; margin-bottom: 18px; }
    .panel-header { display: flex; justify-content: space-between; gap: 18px; align-items: start; }
    .badge { border: 1px solid var(--line); border-radius: 999px; padding: 6px 10px; color: var(--accent); white-space: nowrap; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
    .drop-form { display: grid; gap: 14px; }
    .dropzone { border: 2px dashed #9f9a8d; border-radius: 8px; padding: 32px; display: grid; place-items: center; gap: 6px; text-align: center; cursor: pointer; background: #fbf7ec; }
    .dropzone input { display: none; }
    .dropzone span { color: var(--muted); }
    .stack { display: grid; gap: 14px; }
    label { display: grid; gap: 7px; color: var(--muted); font-size: 14px; }
    select, button { min-height: 42px; border-radius: 6px; border: 1px solid var(--line); font: inherit; }
    select { background: white; color: var(--ink); padding: 0 10px; }
    button { background: var(--accent); color: white; border: 0; font-weight: 700; cursor: pointer; padding: 0 16px; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th, td { border-bottom: 1px solid var(--line); text-align: left; padding: 10px 6px; vertical-align: top; }
    th { color: var(--muted); font-weight: 700; }
    .muted { color: var(--muted); }
    .notice { border-radius: 8px; padding: 12px 14px; margin-bottom: 16px; border: 1px solid var(--line); }
    .notice.success { background: #e7f3ee; color: #0e513f; }
    .notice.error { background: #f8e4dd; color: #7c2d1c; }

    @media (max-width: 820px) {
      main { width: min(100vw - 20px, 1180px); padding-top: 18px; }
      .hero, .grid, .panel-header { display: grid; grid-template-columns: 1fr; }
      h1 { font-size: 34px; }
      .status-card { min-width: 0; }
    }
    """
