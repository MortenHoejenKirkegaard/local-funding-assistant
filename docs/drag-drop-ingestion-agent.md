# Drag-and-drop ingestion-agent

Dette dokument beskriver agenten, der skal modtage filer via dashboardet, spoerge hvilken virksomhed/projekt filen hoerer til, og derefter placere og indeksere filen korrekt.

## Maal

Brugeren skal kunne traekke filer ind i dashboardet uden at skulle kende mappestrukturen.

Agenten skal:

- Modtage en eller flere filer via drag-and-drop.
- Kopiere filerne til en intern dropzone.
- Foreslaa virksomhed, projekt og dokumenttype.
- Kraeve brugerbekraeftelse foer filen flyttes endeligt.
- Flytte filen til korrekt case-mappe.
- Udtraekke tekst og metadata.
- Oprette dokument- og chunk-records.
- Sende relevante chunks til det korrekte vektorindeks.
- Logge handlingen i audit trail.

## Brugerflow

```text
Drop file
  -> Upload to local dropzone
  -> Estimate file type and content category
  -> Ask: Which company?
  -> Ask: Which project?
  -> Ask: Which document category?
  -> Confirm destination
  -> Move file
  -> Parse and index
  -> Show result
```

## UI-felter

Dashboardet skal vise disse felter efter drop:

- Filnavn
- Filtype
- Filstoerrelse
- Foreslaaet virksomhed
- Foreslaaet projekt
- Foreslaaet dokumentkategori
- Destination folder
- Confidentiality: `internal`, `confidential`, `highly_confidential`
- Knapper: `Index file`, `Change destination`, `Cancel`

## Dokumentkategorier

| Kategori | Destination |
| --- | --- |
| `profile` | `00_profile` |
| `technical` | `01_technical` |
| `ip_patents` | `02_ip_patents` |
| `clinical` | `03_clinical` |
| `market` | `04_market` |
| `commercial` | `05_commercial` |
| `team_partners` | `06_team_partners` |
| `pitch_investor` | `07_pitch_investor` |
| `applications` | `08_applications` |
| `raw_inbox` | `09_raw_inbox` |

## Klassificering

Foerste version kan bruge simpel lokal logik:

- Filsti og filnavn
- Filtype
- Foerste tekstudtraek
- Nogle noegleord som `patent`, `clinical`, `market`, `budget`, `pitch`, `team`

Senere kan systemet bruge AI-klassificering, men kun efter `Ask first` cost approval.

## Databaseflow

1. Opret `ingestion_jobs` record med status `pending_user_selection`.
2. Gem original filinformation i `ingestion_files`.
3. Naar brugeren godkender, skift status til `approved`.
4. Flyt filen til destination.
5. Opret eller opdater `documents`.
6. Opret `document_chunks`.
7. Opret embeddings i korrekt Qdrant collection.
8. Skift status til `indexed`.

## Fejltilstande

| Fejl | Handling |
| --- | --- |
| Ukendt filtype | Gem i dropzone og bed bruger vælge manuelt |
| Dublet hash | Vis eksisterende dokument og spørg om versionering |
| Parserfejl | Gem dokumentrecord med `extraction_status = failed` |
| Manglende projekt | Tillad virksomhedsniveau uden projekt |
| Path uden for allowed root | Afvis og audit-log |
| API mode off | Brug kun lokal klassificering |

## Sikkerhed

- Agenten maa kun skrive inden for `allowed_root`.
- Agenten maa aldrig sende fulde dokumenter til Slack/email.
- AI-baseret klassificering maa kun bruge korte uddrag og skal respektere API mode.
- Originalfilen maa ikke slettes foer destination og hash er bekraeftet.
- Alle flytninger skal audit-logges med kilde, destination, company_id og document_id.
