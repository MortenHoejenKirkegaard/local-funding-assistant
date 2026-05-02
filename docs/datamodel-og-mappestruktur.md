# Lokal funding assistant: datamodel og mappestruktur

Dette dokument beskriver foerste konkrete datastruktur for en lokal AI-baseret funding assistant paa en Mac Mini. Formaalet er at holde otte medtech-portefoljevirksomheder adskilt, soegbare og sammenlignelige, samtidig med at historiske soft funding-ansoegninger kan bruges som laeringsgrundlag.

## Designprincipper

- Alt koerer lokalt som udgangspunkt.
- Hver virksomhed har sit eget datarum og eget semantisk indeks.
- Faelles metadatafelter goer det muligt at sammenligne cases paa tvaers.
- Historiske ansoegninger gemmes som selvstaendigt vidensgrundlag med udfald: `approved`, `rejected`, `submitted`, `draft`.
- Funding calls normaliseres til en ensartet struktur, uanset om kilden er en fond, et program, en PDF eller en webside.
- Notifikationer maa kun sende korte sammendrag og links/interne referencer, ikke fulde fortrolige dokumenter.

## Anbefalet lokal mappestruktur

```text
funding-assistant/
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
      index_manifest.yml
    company-02/
      ...
  funding/
    calls/
      active/
      upcoming/
      closed/
    funder_profiles/
    source_snapshots/
  applications/
    historical/
      approved/
      rejected/
      submitted/
      draft/
    templates/
    pattern_library/
  outputs/
    matches/
    drafts/
    notifications/
  system/
    logs/
    audit/
    config/
```

## Case-mapper

| Mappe | Indhold | Eksempler |
| --- | --- | --- |
| `00_profile` | Kurateret virksomhedsprofil | one-pager, strategi, statusnotat |
| `01_technical` | Teknologi og produkt | tekniske beskrivelser, architecture, testdata |
| `02_ip_patents` | IP og patenter | patentansoegninger, freedom-to-operate, IP-status |
| `03_clinical` | Klinisk evidens | studier, protokoller, endpoints, clinical need |
| `04_market` | Marked og konkurrence | markedsanalyse, TAM/SAM/SOM, konkurrenter |
| `05_commercial` | Go-to-market og business case | pricing, reimbursement, partnerskaber |
| `06_team_partners` | Team, advisors og partnere | CV'er, LOI'er, samarbejdsaftaler |
| `07_pitch_investor` | Investor- og pitchmateriale | pitch decks, investor memos |
| `08_applications` | Case-specifikke ansoegninger | tidligere drafts, indsendte versioner |
| `09_raw_inbox` | Nye filer foer klassificering | dropzone for loebende upload |

## Dokumentmetadata

Alle dokumenter, der indekseres, boer have disse metadatafelter.

```yaml
document_id: uuid
company_id: company-01
source_path: cases/company-01/03_clinical/clinical-study.docx
document_type: clinical_evidence
title: Human factors study summary
created_at: 2026-04-30
updated_at: 2026-04-30
source_created_at:
source_modified_at:
language: da
confidentiality: confidential
version:
author:
project_id:
ip_relevance: high
clinical_relevance: high
commercial_relevance: medium
funding_relevance: high
extraction_status: indexed
extraction_errors: []
tags:
  - medtech
  - clinical
  - evidence
```

## Virksomhedsprofil

Hver virksomhed skal have en maskinlaesbar profil, som opdateres af portfolio-dataagenten og kan bruges af matchmaking- og ansoegningsagenten.

```yaml
company_id: company-01
display_name:
short_description:
therapeutic_area:
technology_type:
product_stage:
trl:
regulatory_stage:
ip_status:
patent_families: []
clinical_evidence_level:
target_users:
target_buyers:
market_geography:
primary_projects:
  - project_id:
    name:
    objective:
    stage:
    funding_need:
    next_milestones: []
strategic_keywords: []
known_gaps: []
last_profile_update:
```

## Relationel database

PostgreSQL anbefales til metadata, status, relationer, scoringer og audit trail.

### `companies`

| Felt | Type | Beskrivelse |
| --- | --- | --- |
| `id` | text pk | Stabilt ID, fx `company-01` |
| `display_name` | text | Navn vist i dashboard |
| `short_description` | text | Kort profil |
| `therapeutic_area` | text | Klinisk/terapeutisk omraade |
| `technology_type` | text | Device, diagnostic, digital health, software, biomateriale osv. |
| `product_stage` | text | Idea, prototype, validation, clinical, market-ready |
| `trl` | int | Technology readiness level |
| `regulatory_stage` | text | Ikke startet, planlagt, igang, submitted, approved |
| `ip_status` | text | Patent pending, granted, licensed, university-owned, mixed |
| `created_at` | timestamptz | Oprettelse |
| `updated_at` | timestamptz | Seneste opdatering |

### `projects`

| Felt | Type | Beskrivelse |
| --- | --- | --- |
| `id` | uuid pk | Projekt-ID |
| `company_id` | text fk | Reference til virksomhed |
| `name` | text | Projektnavn |
| `objective` | text | Hvad funding skal bruges til |
| `stage` | text | Modenhed |
| `funding_need_amount` | numeric | Estimeret behov |
| `funding_need_currency` | text | Typisk DKK/EUR |
| `target_deadline` | date | Intern deadline hvis relevant |
| `milestones` | jsonb | Milepaele |
| `known_gaps` | jsonb | Manglende dokumentation/partnere/data |

### `documents`

| Felt | Type | Beskrivelse |
| --- | --- | --- |
| `id` | uuid pk | Dokument-ID |
| `company_id` | text nullable | Tom ved generelle funding-dokumenter |
| `project_id` | uuid nullable | Reference til projekt |
| `source_path` | text | Lokal filsti |
| `sha256` | text | Deduplicering og versionskontrol |
| `document_type` | text | Teknisk, IP, klinisk, marked osv. |
| `title` | text | Titel |
| `language` | text | Sprog |
| `confidentiality` | text | internal, confidential, highly_confidential |
| `indexed_at` | timestamptz | Seneste indeksering |
| `parser` | text | tika, docx, xlsx, pdf, ocr |
| `metadata` | jsonb | Ekstra felter |

### `document_chunks`

| Felt | Type | Beskrivelse |
| --- | --- | --- |
| `id` | uuid pk | Chunk-ID |
| `document_id` | uuid fk | Dokument |
| `company_id` | text nullable | Bruges til filtrering |
| `chunk_index` | int | Rækkefølge |
| `text` | text | Ekstraheret tekst |
| `page_number` | int nullable | PDF/PPT side |
| `sheet_name` | text nullable | Excel sheet |
| `section_heading` | text nullable | Word/PDF afsnit |
| `token_count` | int | Størrelse |
| `embedding_id` | text | Reference til vektorindeks |

### `funders`

| Felt | Type | Beskrivelse |
| --- | --- | --- |
| `id` | uuid pk | Funder-ID |
| `name` | text | Fond/programorganisation |
| `country` | text | DK som default |
| `website` | text | Kilde |
| `profile_type` | text | impact, research, commercialization, clinical, mixed |
| `typical_grant_size_min` | numeric | Nedre ramme |
| `typical_grant_size_max` | numeric | Øvre ramme |
| `typical_requirements` | jsonb | Kravmønstre |
| `historical_notes` | text | Kvalitativ profil |

### `funding_calls`

| Felt | Type | Beskrivelse |
| --- | --- | --- |
| `id` | uuid pk | Call-ID |
| `funder_id` | uuid fk | Fonden/programmet |
| `title` | text | Call-navn |
| `status` | text | active, upcoming, closed, unknown |
| `opens_at` | date | Aabner |
| `deadline_at` | timestamptz | Deadline |
| `decision_at` | date | Forventet svar |
| `grant_min` | numeric | Minimum |
| `grant_max` | numeric | Maximum |
| `currency` | text | DKK/EUR |
| `focus_areas` | jsonb | Temaer |
| `eligibility_criteria` | jsonb | Hvem kan soege |
| `documentation_requirements` | jsonb | Bilag, budget, partnere |
| `evaluation_criteria` | jsonb | Vurderingskriterier |
| `source_url` | text | Primær kilde |
| `source_snapshot_path` | text | Lokal kopi af kildeside/PDF |
| `last_checked_at` | timestamptz | Seneste screening |

### `applications`

| Felt | Type | Beskrivelse |
| --- | --- | --- |
| `id` | uuid pk | Ansoegnings-ID |
| `company_id` | text nullable | Virksomhed |
| `project_id` | uuid nullable | Projekt |
| `funding_call_id` | uuid nullable | Call |
| `funder_id` | uuid nullable | Funder |
| `title` | text | Titel |
| `status` | text | approved, rejected, submitted, draft |
| `submitted_at` | date | Indsendelse |
| `decision_at` | date | Svar |
| `requested_amount` | numeric | Ansøgt beløb |
| `awarded_amount` | numeric | Bevilliget beløb |
| `currency` | text | DKK/EUR |
| `score_or_feedback` | text | Evalueringsfeedback |
| `source_path` | text | Lokal filsti |
| `metadata` | jsonb | Ekstra felter |

### `match_scores`

| Felt | Type | Beskrivelse |
| --- | --- | --- |
| `id` | uuid pk | Match-ID |
| `funding_call_id` | uuid fk | Call |
| `company_id` | text fk | Virksomhed |
| `project_id` | uuid nullable | Projekt |
| `overall_score` | numeric | 0-100 |
| `strategic_fit_score` | numeric | Strategisk relevans |
| `eligibility_score` | numeric | Opfyldelse af formelle krav |
| `evidence_score` | numeric | Klinisk/teknisk evidens |
| `ip_score` | numeric | IP-fit |
| `commercial_score` | numeric | Marked/kommercialisering |
| `effort_score` | numeric | Lavere score ved høj arbejdsbyrde |
| `deadline_urgency_score` | numeric | Tidskritikalitet |
| `rationale` | text | Forklaring |
| `missing_requirements` | jsonb | Mangler |
| `recommended_action` | text | Næste skridt |
| `created_at` | timestamptz | Oprettet |

### `drafts`

| Felt | Type | Beskrivelse |
| --- | --- | --- |
| `id` | uuid pk | Draft-ID |
| `application_id` | uuid fk | Ansoegning |
| `version` | int | Version |
| `section` | text | Projektbeskrivelse, impact osv. |
| `content` | text | Drafttekst |
| `assumptions` | jsonb | Antagelser |
| `source_references` | jsonb | Dokument- og chunkreferencer |
| `created_at` | timestamptz | Oprettet |

### `notifications`

| Felt | Type | Beskrivelse |
| --- | --- | --- |
| `id` | uuid pk | Notifikations-ID |
| `channel` | text | dashboard, slack, email |
| `recipient` | text | Slack channel eller email |
| `trigger_type` | text | deadline, high_match, missing_requirement |
| `funding_call_id` | uuid nullable | Call |
| `company_id` | text nullable | Virksomhed |
| `project_id` | uuid nullable | Projekt |
| `subject` | text | Kort emne |
| `body` | text | Kort besked |
| `contains_confidential_content` | boolean | Skal normalt være false for Slack/email |
| `sent_at` | timestamptz | Afsendt |
| `status` | text | queued, sent, failed |

### `audit_events`

| Felt | Type | Beskrivelse |
| --- | --- | --- |
| `id` | uuid pk | Event-ID |
| `actor` | text | agent/user/system |
| `action` | text | indexed, searched, drafted, notified |
| `entity_type` | text | document, call, application, draft |
| `entity_id` | text | ID |
| `company_id` | text nullable | Scope |
| `details` | jsonb | Tekniske detaljer |
| `created_at` | timestamptz | Tidspunkt |

## Vektorindeks

Qdrant anbefales som foerstevalg til lokal semantisk soegning. Brug separate collections for at mindske risikoen for utilsigtet krydsblanding.

```text
collection: case_company_01
collection: case_company_02
collection: case_company_03
collection: case_company_04
collection: case_company_05
collection: case_company_06
collection: case_company_07
collection: case_company_08
collection: funding_calls
collection: historical_applications
collection: funder_profiles
```

Payload pr. vektor:

```yaml
chunk_id: uuid
document_id: uuid
company_id: company-01
project_id:
document_type: clinical_evidence
title:
source_path:
page_number:
sheet_name:
section_heading:
confidentiality: confidential
created_at:
tags: []
```

## Dokumentparsing

| Filtype | Parser | Noter |
| --- | --- | --- |
| `.docx` | mammoth eller Apache Tika | Bevar overskrifter og tabeller saa vidt muligt |
| `.xlsx` | LibreOffice headless eller openpyxl-lignende parser | Indeksér pr. sheet og tabelomraade |
| `.pptx` | Apache Tika eller LibreOffice export | Brug slide-nummer som metadata |
| `.pdf` | Apache Tika + OCR fallback | OCR kun hvis tekstlag mangler |
| billeder/scans | OCR | Brug kun ved relevante bilag |
| `.txt/.md/.csv` | direkte parser | Lav chunking efter struktur |

## Sikkerhedsregler

- Slack og email maa som default kun indeholde korte resumeer, deadlines, matchscore og interne referencer.
- Fuld dokumenttekst og drafts vises i dashboardet, ikke i eksterne notifikationer.
- Alle eksterne kald samles i en allowlist, fx funding-kilder, Slack webhook og SMTP.
- Secrets gemmes i macOS Keychain eller lokal `.env`, aldrig i dokumentmapperne.
- Audit-log skal registrere hvilke dokumenter der bruges til drafts og match-analyser.
- Hver agent skal bruge `company_id` som obligatorisk filter, naar der arbejdes med virksomhedsspecifik data.

## Foerste MVP-objekter

Start med disse objekter foer resten bygges ud:

```text
companies
projects
documents
document_chunks
funders
funding_calls
applications
match_scores
drafts
notifications
audit_events
```

## Minimum dashboard views

- Portfolio: oversigt over 8 virksomheder, datastatus og kendte funding gaps.
- Documents: dokumenter pr. virksomhed med parserstatus og seneste indeksering.
- Funding radar: aktive og kommende calls med deadlines.
- Matches: prioriteret call-liste pr. virksomhed/projekt.
- Drafts: ansøgningsudkast, antagelser og kildehenvisninger.
- Notifications: kø, historik og fejlede Slack/email-beskeder.
- Audit: søgninger, drafts og afsendte notifikationer.

## Naeste tekniske skridt

1. Opret PostgreSQL migrationer for tabellerne i dette dokument.
2. Opret lokal mappestruktur med otte `company-*` cases.
3. Byg ingestion-worker for Word og Excel som foerste dokumenttyper.
4. Opret Qdrant collections og payload-schema.
5. Byg dashboardets foerste views: Portfolio, Documents, Funding radar og Matches.
6. Tilfoej Slack/email notification service med fortrolighedsfilter.
