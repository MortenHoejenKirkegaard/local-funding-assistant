# Eksterne handlinger og pengepolitik

Dette dokument definerer en haard sikkerhedsgraense for systemet: Agenten maa gerne analysere, foreslaa og generere udkast, men den maa ikke bruge penge, indgaa aftaler eller sende bindende materiale paa brugerens vegne.

## Grundregel

Systemet er en lokal funding assistant, ikke en autonom indkoeber, juridisk aktor eller ekstern repræsentant.

Agenten maa:

- Læse og indeksere godkendte lokale dokumenter.
- Analysere funding calls.
- Lave match-analyser.
- Generere drafts og anbefalinger.
- Sende korte Slack-resumeer til brugeren.

Agenten maa ikke:

- Bruge betalingskort eller gemte betalingsoplysninger.
- Koebe produkter, services, API credits eller abonnementer.
- Opgradere softwareplaner eller acceptere betalte vilkaar.
- Oprette konti hos tredjeparter.
- Acceptere terms, underskrive dokumenter eller indgaa aftaler.
- Indsende ansøgninger, formularer eller bindende materiale til eksterne parter.
- Sende email paa brugerens vegne.
- Kontakte fonde, partnere, virksomheder eller personer direkte.

## Output-kanal

Eksternt output skal som udgangspunkt kun ske via Slack.

Slack-beskeder skal vaere korte og ikke-bindende:

- Status
- Deadline
- Matchscore
- Vigtigste mangler
- Link eller reference til dashboard
- Anbefalet naeste handling

Slack-beskeder maa ikke indeholde:

- Fulde patenttekster
- Fuld ansøgningstekst
- Fortrolige dokumentuddrag
- Kortoplysninger, loginoplysninger eller secrets
- Juridisk bindende formuleringer sendt til tredjeparter

## API-forbrug

API-kald er tilladt som analysevaerktoej, men kun efter budgetreglerne.

Default mode:

```text
Ask first
```

Foer en opgave bruger API, skal systemet vise:

- Opgavetype
- Valgt model
- Estimerede input tokens
- Estimerede output tokens
- Estimeret pris
- Om web search bruges
- Om opgaven indeholder fortrolig kontekst

Brugeren skal godkende opgaven, medmindre opgaven ligger under en eksplicit brugerdefineret auto-grænse.

## Forbudte handlinger

Disse handlinger skal blokeres teknisk:

| Handling | Status |
| --- | --- |
| Betaling med kort | Forbudt |
| Checkout | Forbudt |
| Subscription/upgrade | Forbudt |
| Accept af terms | Forbudt |
| Underskrift/signatur | Forbudt |
| Kontraktindgaaelse | Forbudt |
| Kontooprettelse | Forbudt |
| Ekstern formularindsendelse | Forbudt |
| Email-afsendelse | Forbudt |
| Direkte besked til ekstern part | Forbudt |

## Tilladte handlinger

| Handling | Status |
| --- | --- |
| Slack-besked til brugerens egen kanal | Tilladt |
| Dashboard-output | Tilladt |
| Lokal filindeksering | Tilladt |
| Lokal databaseopdatering | Tilladt |
| GitHub push af kode efter brugerens godkendelse | Tilladt |
| Funding-call laesning | Tilladt |

## Implementeringskrav

Foer en agent udfører en handling, skal den klassificeres:

```text
local_read
local_write
api_analysis
slack_output
external_submission
purchase
agreement
account_creation
email_send
```

Kun disse maa koere automatisk:

```text
local_read
local_write
slack_output
```

`api_analysis` maa kun koere efter budgetgodkendelse.

Alle andre kategorier skal blokeres og logges.

## Audit

Blokerede handlinger skal logges med:

- Agent
- Handlingstype
- Aarsag til blokering
- Tidspunkt
- Relevante interne referencer

Der maa ikke logges fulde kortoplysninger, passwords, secrets eller fortrolige dokumentuddrag.
