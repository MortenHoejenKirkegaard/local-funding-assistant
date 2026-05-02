# Lokal Funding Assistant

Dette projekt er fundamentet for en lokal AI-baseret funding assistant paa en Mac Mini. Systemet skal organisere portefoljedata, overvage funding-muligheder, matche calls mod medtech-cases, generere drafts og give Slack/email-notifikationer med budgetkontrol for API-forbrug.

## Status

Projektet indeholder nu:

- Mappestruktur til 8 portefoljevirksomheder.
- PostgreSQL core schema.
- Datamodel og indeksdesign.
- Matchmaking scoring-framework.
- Design for Mac control app og API-budgetstyring.
- Adgangsrestriktioner, saa systemet kun maa arbejde inde i denne projektmappe.
- Penge- og handlingspolitik, saa agenten ikke kan betale, indgaa aftaler eller sende eksterne ansøgninger.
- Design for drag-and-drop ingestion-agent med brugerbekraeftelse foer indeksering.
- Start/stop/status scripts til den lokale service-stack.

## Daglig brug

Start services:

```bash
./scripts/start.sh
```

Se status:

```bash
./scripts/status.sh
```

Stop services:

```bash
./scripts/stop.sh
```

## Datasikkerhed

Fortrolige dokumenter skal placeres under `funding-assistant/cases/company-*/...` eller `funding-assistant/applications/historical/...`.

`.gitignore` er sat op til ikke at versionere Word, Excel, PowerPoint, PDF, billeder, runtime data, outputs, logs eller secrets. Kode, schema, dokumentation og manifests kan versioneres.

Systemets tilladte rodmappe er:

```text
/Users/mortenkirkegaard/Desktop/Codex Access
```

Se [docs/adgangsrestriktioner.md](docs/adgangsrestriktioner.md) og [config/security-policy.yml](config/security-policy.yml).

Agenten maa ikke bruge kortoplysninger, koebe noget, oprette abonnementer, acceptere vilkaar, underskrive aftaler, indsende ansøgninger, sende email, kontakte tredjeparter eller dele data paa brugerens vegne. Eksternt output maa kun vaere korte Slack-beskeder til brugeren.

Se [docs/eksterne-handlinger-og-pengepolitik.md](docs/eksterne-handlinger-og-pengepolitik.md).

## Drag-and-drop ingestion

Planlagt brugerflow:

1. Traek filer ind i dashboardet.
2. Systemet kopierer dem til `funding-assistant/system/inbox`.
3. Systemet foreslaar virksomhed, projekt og dokumenttype.
4. Brugeren bekraefter placering.
5. Systemet flytter filen til korrekt case-mappe og indekserer.

Se [docs/drag-drop-ingestion-agent.md](docs/drag-drop-ingestion-agent.md).

## Testmiljoe

Der er et separat testmiljoe, som spejler den rigtige mappestruktur:

```text
funding-assistant-test/
```

Laeg testfiler i:

```text
funding-assistant-test/system/inbox
```

List testfiler:

```bash
./scripts/test-ingest.sh --list
```

Indekser en testfil:

```bash
./scripts/test-ingest.sh --file eksempel.md --company company-01 --document-type clinical
```

Se [docs/testmiljoe.md](docs/testmiljoe.md).

Uploadede dokumenter auto-indekseres kun, hvis test-agenten er mindst 95% sikker paa baade virksomhed og dokumenttype. Ellers skal allokationen bekraeftes i dashboardet.

Start test-dashboard:

```bash
./scripts/run-test-app.sh
```

Stop test-dashboard:

```bash
./scripts/stop-test-app.sh
```

Dashboardet koerer paa:

```text
http://localhost:3000
```

## Validering og tests

Projektet har en foerste let testbase for policy- og path-regler.

Koer tests:

```bash
python3 -m pytest
```

Krav og validation loops:

- [docs/requirements/software-requirements.md](docs/requirements/software-requirements.md)
- [docs/validation-loops.md](docs/validation-loops.md)

## Foerste tekniske milepaele

1. Korrekt lokal service-stack med PostgreSQL og Qdrant.
2. Ingestion-worker for Word og Excel.
3. API-usage tracking og approval flow.
4. Lokalt dashboard.
5. Mac control app til start/stop og budgetstyring.
