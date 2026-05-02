# Mac control app og API-budgetstyring

Dette dokument beskriver en lokal Mac-app, der starter, stopper og overvåger hele funding assistant-systemet. Appen fungerer som kontrolpanel, dashboard og sikkerhedslaag for API-forbrug.

## Formaal

Brugeren skal ikke skulle arbejde direkte med terminal, Docker eller Git for at bruge systemet i dagligdagen.

Mac-appen skal kunne:

- Starte og stoppe alle lokale services.
- Vise dashboardet direkte i appen.
- Vise status for database, vektorindeks, workers og scheduler.
- Tracke API-forbrug og estimerede omkostninger.
- Kraeve manuel godkendelse foer dyre API-opgaver koeres.
- Give et prisestimat foer store handlinger som dokumentindeksering, dyb matchanalyse eller draft-generering.

## Anbefalet arkitektur

```text
Mac App
  |
  |-- Embedded dashboard view
  |-- Start/stop/status controls
  |-- API budget panel
  |-- Approval dialogs
  |
Local services
  |
  |-- dashboard web app
  |-- API/backend service
  |-- worker/scheduler
  |-- PostgreSQL
  |-- Qdrant
```

## Teknologivalg

### Anbefaling: Tauri

Tauri anbefales til Mac-appen, fordi den giver en lettere native app end Electron.

Fordele:

- Lille app-stoerrelse.
- God adgang til lokale kommandoer.
- Kan pakke dashboardet ind som en rigtig macOS-app.
- Kan starte/stoppe lokale services via scripts.
- Bedre egnet til en lokal appliance-lignende Mac Mini-loesning.

Alternativ: Electron.

Electron er lettere for mange webudviklere, men bruger mere RAM og foeles tungere. Det kan stadig vaere fint, hvis udviklingshastighed prioriteres over ressourceforbrug.

## Start og stop

Mac-appen skal kalde lokale scripts:

```text
scripts/start.sh
scripts/stop.sh
scripts/status.sh
scripts/restart.sh
```

Foerste version kan bruge Docker Compose:

```text
docker compose up -d
docker compose down
docker compose ps
```

Senere kan systemet saettes op med macOS `launchd`, saa det starter automatisk, naar Mac Mini'en taender.

## Services

| Service | Rolle | Koerer hele tiden |
| --- | --- | --- |
| Dashboard | Lokal brugerflade | Ja |
| Backend API | Orkestrerer opgaver | Ja |
| Worker | Indeksering, matching, drafts | Ja, men idle det meste af tiden |
| Scheduler | Planlagte scanninger | Ja |
| PostgreSQL | Metadata og status | Ja |
| Qdrant | Vektorsoegning | Ja |

## Dashboard i appen

Appen skal vise dashboardet som hovedview.

Minimum views:

- Portfolio
- Documents
- Funding radar
- Matches
- Drafts
- Notifications
- API usage
- System status

## API usage tracking

Alle API-kald skal logges i databasen.

Ny tabel:

```sql
CREATE TABLE api_usage_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider text NOT NULL,
  model text NOT NULL,
  task_type text NOT NULL,
  company_id text,
  project_id uuid,
  input_tokens integer NOT NULL DEFAULT 0,
  cached_input_tokens integer NOT NULL DEFAULT 0,
  output_tokens integer NOT NULL DEFAULT 0,
  web_search_calls integer NOT NULL DEFAULT 0,
  estimated_cost_usd numeric NOT NULL DEFAULT 0,
  actual_cost_usd numeric,
  status text NOT NULL DEFAULT 'completed',
  created_at timestamptz NOT NULL DEFAULT now()
);
```

Eksempler paa `task_type`:

- `document_classification`
- `document_summary`
- `funding_call_analysis`
- `match_scoring`
- `draft_generation`
- `notification_summary`

## Budgetpanel

Dashboardet skal vise:

- Forbrug i dag.
- Forbrug denne uge.
- Forbrug denne maaned.
- Forbrug pr. virksomhed.
- Forbrug pr. opgavetype.
- Estimeret maanedsforbrug ved nuvaerende tempo.
- Seneste dyre API-opgaver.

Brugeren skal kunne saette:

- Dagligt budgetloft.
- Maanedligt budgetloft.
- Makspris for en enkelt opgave.
- Om dyre opgaver kraever manuel godkendelse.

## Approval flow

Foer en opgave koeres, laver systemet et estimat.

Eksempel:

```text
Opgave: Generer draft til Innovationsfonden call for company-03
Forventet input: 85.000 tokens
Forventet output: 12.000 tokens
Model: GPT-5.4 mini
Estimeret pris: $0.12
Web search: 0 kald

Vil du koere opgaven?
```

Brugeren kan vaelge:

- Approve once
- Approve all tasks under selected cost today
- Cancel

## Cost estimator

Estimatet beregnes ud fra:

- Antal relevante dokumentchunks.
- Forventet prompt-stoerrelse.
- Forventet output-laengde.
- Valgt model.
- Eventuelle web search-kald.
- Cache-rabat hvis samme call/dokumenter allerede er behandlet.

Foerste estimator kan bruge konservative standarder:

| Opgave | Input tokens | Output tokens | Noter |
| --- | ---: | ---: | --- |
| Klassificer dokument | 2.000-8.000 | 300-800 | Per dokument |
| Opsummer dokument | 5.000-30.000 | 800-2.500 | Afhaenger af laengde |
| Analyser funding call | 5.000-20.000 | 1.000-3.000 | Per call |
| Match call mod 8 cases | 20.000-80.000 | 4.000-12.000 | Batch-opgave |
| Generer ansøgningsdraft | 50.000-150.000 | 8.000-25.000 | Stor opgave |

## Modelstrategi

Brug billig model til rutineopgaver:

- Klassificering
- Metadataudtræk
- Kort opsummering
- Første screening

Brug stærkere model til:

- Endelig matchanalyse
- Ansøgningsdrafts
- Risikoanalyse
- Vigtige strategiske anbefalinger

## API safety rules

- Ingen API-opgave maa sende hele datarummet.
- API-opgaver skal bruge retrieval: kun relevante chunks sendes.
- Slack/email maa ikke indeholde fortrolige uddrag.
- API-loggen maa gemme tokenforbrug og opgavetype, men ikke fulde prompts med fortroligt indhold som default.
- Alle store opgaver skal have cost estimate foer afsendelse.
- Brugeren skal kunne slukke API-kald globalt fra dashboardet.

## Global API modes

Dashboardet skal have en tydelig API mode-kontrol:

| Mode | Betydning |
| --- | --- |
| `Off` | Ingen API-kald. Kun lokal database/dashboard. |
| `Ask first` | Systemet estimerer pris og beder om godkendelse. |
| `Auto under limit` | Opgaver under brugerens prisgrænse koerer automatisk. |
| `Auto` | Alle planlagte opgaver koerer, saa laenge maanedsbudget ikke overskrides. |

Anbefalet default: `Ask first`.

## Foerste MVP

Foerste version af Mac control appen skal kunne:

1. Starte services.
2. Stoppe services.
3. Vise service-status.
4. Vise dashboard.
5. Vise API mode: `Off` eller `Ask first`.
6. Vise manuelt beregnede cost estimates foer draft-generation.
7. Logge API usage events i databasen.

## Senere udbygning

- Automatisk launch ved boot.
- macOS menu bar status.
- Native notifications.
- Budgetadvarsler.
- Per-company cost reporting.
- One-click export af maanedsrapport.
