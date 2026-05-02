# Testmiljoe

Testmiljoeet spejler det egentlige system, men ligger separat:

```text
funding-assistant-test/
```

Det bruges til at teste drag-and-drop, placering, hash, metadata og valideringsloops uden at blande testfiler med rigtige portefoljedata.

## Struktur

```text
funding-assistant-test/
  cases/
    company-01/
      00_profile/
      01_technical/
      02_ip_patents/
      03_clinical/
      04_market/
      05_commercial/
      06_team_partners/
      07_pitch_investor/
      08_applications/
      09_raw_inbox/
    ...
    company-08/
  system/
    inbox/
    quarantine/
    logs/
    index/
  outputs/
```

## Saadan tester du

Start web-dashboard:

```bash
./scripts/run-test-app.sh
```

Appen aabner paa:

```text
http://localhost:3000
```

Laeg en testfil i:

```text
funding-assistant-test/system/inbox
```

List filer der venter:

```bash
./scripts/test-ingest.sh --list
```

Flyt og indeksér en fil til en test-case:

```bash
./scripts/test-ingest.sh --file eksempel.md --company company-01 --document-type clinical
```

Dokumenttyper:

```text
profile
technical
ip_patents
clinical
market
commercial
team_partners
pitch_investor
applications
raw_inbox
```

## Hvad scriptet tester

Scriptet koerer samme grundprincipper som det rigtige flow:

- Path skal blive inden for `Codex Access`.
- Lokal skrivehandling skal godkendes af policy engine.
- Virksomhed skal findes.
- Dokumenttype skal vaere kendt.
- Filen flyttes fra test-inbox til korrekt kategori-mappe.
- SHA256 beregnes.
- Metadata skrives til test-index.
- Event skrives til test-log.

## Output

Test-index:

```text
funding-assistant-test/system/index/documents-index.jsonl
```

Test-events:

```text
funding-assistant-test/system/logs/ingestion-events.jsonl
```

Disse JSONL-filer er udelukket fra Git, fordi testdata kan komme til at indeholde fortrolige filnavne eller metadata.

## Vigtigt

Dette er et test harness, ikke fuld dokumentparser endnu.

I denne version:

- `.txt`, `.md` og `.csv` giver tekst-preview.
- Word, Excel, PowerPoint og PDF flyttes, hashes og logges, men fuld parsing kommer i naeste ingestion-MVP.
- Ingen API-kald bruges.
- Ingen Slack-beskeder sendes.
- Ingen data deles eksternt.

## Foerste installation

Hvis appen siger, at FastAPI mangler, koer:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
```
