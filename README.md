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

Agenten maa ikke bruge kortoplysninger, koebe noget, oprette abonnementer, acceptere vilkaar, underskrive aftaler, indsende ansøgninger eller sende email paa brugerens vegne. Eksternt output er som udgangspunkt kun korte Slack-beskeder til brugeren.

Se [docs/eksterne-handlinger-og-pengepolitik.md](docs/eksterne-handlinger-og-pengepolitik.md).

## Drag-and-drop ingestion

Planlagt brugerflow:

1. Traek filer ind i dashboardet.
2. Systemet kopierer dem til `funding-assistant/system/inbox`.
3. Systemet foreslaar virksomhed, projekt og dokumenttype.
4. Brugeren bekraefter placering.
5. Systemet flytter filen til korrekt case-mappe og indekserer.

Se [docs/drag-drop-ingestion-agent.md](docs/drag-drop-ingestion-agent.md).

## Foerste tekniske milepaele

1. Korrekt lokal service-stack med PostgreSQL og Qdrant.
2. Ingestion-worker for Word og Excel.
3. API-usage tracking og approval flow.
4. Lokalt dashboard.
5. Mac control app til start/stop og budgetstyring.
