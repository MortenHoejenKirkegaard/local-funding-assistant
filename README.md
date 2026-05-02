# Lokal Funding Assistant

Dette projekt er fundamentet for en lokal AI-baseret funding assistant paa en Mac Mini. Systemet skal organisere portefoljedata, overvage funding-muligheder, matche calls mod medtech-cases, generere drafts og give Slack/email-notifikationer med budgetkontrol for API-forbrug.

## Status

Projektet indeholder nu:

- Mappestruktur til 8 portefoljevirksomheder.
- PostgreSQL core schema.
- Datamodel og indeksdesign.
- Matchmaking scoring-framework.
- Design for Mac control app og API-budgetstyring.
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

## Foerste tekniske milepaele

1. Korrekt lokal service-stack med PostgreSQL og Qdrant.
2. Ingestion-worker for Word og Excel.
3. API-usage tracking og approval flow.
4. Lokalt dashboard.
5. Mac control app til start/stop og budgetstyring.
