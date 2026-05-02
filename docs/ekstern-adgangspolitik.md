# Ekstern adgangspolitik

Eksterne personer maa ikke have almindelig adgang til systemet.

Hvis ekstern adgang senere aktiveres, skal den vaere begrænset til:

- En navngiven ekstern bruger.
- En specifik scoped mappe under `Codex Access`.
- Et tildelt flow, fx upload eller besvarelse af afklaringsspørgsmaal.
- Owner review foer noget flyttes, indekseres eller bruges i drafts.

## Grundregel

Eksterne kan kun foelge flowet. De maa ikke styre systemet.

De maa ikke:

- Se dashboard admin.
- Se andre virksomheder.
- Se andre eksterne brugeres mapper.
- Bruge agents.
- Starte scraping.
- Bruge API-kald.
- Bruge skriveagenten.
- Ændre systemindstillinger.
- Slette eller flytte filer uden for deres scoped flow.
- Kontakte tredjeparter via systemet.
- Se funding matches, drafts, index records eller audit logs.

## Folder-scope

Ekstern bruger maa kun have adgang til egen mappe:

```text
funding-assistant/external/{external_user_id}/
```

Eksempel:

```text
funding-assistant/external/partner-acme/
  inbox/
  submitted/
  rejected/
```

Alle paths skal valideres med:

```text
resolved_path starts with scoped_root_path
resolved_path starts with allowed_root
```

Hvis en path falder uden for scope, skal handlingen blokeres og audit-logges.

## Tilladte handlinger

| Handling | Status |
| --- | --- |
| Se assigned flow | Tilladt |
| Uploade filer til egen scoped inbox | Tilladt |
| Svare paa flow-spoergsmaal | Tilladt |
| Submitte til owner review | Tilladt |

## Forbudte handlinger

| Handling | Status |
| --- | --- |
| Cross-company access | Forbudt |
| Admin dashboard | Forbudt |
| Agent controls | Forbudt |
| API-kald | Forbudt |
| Scraper adgang | Forbudt |
| Skriveagent adgang | Forbudt |
| Downloads | Forbudt som default |
| Sletning | Forbudt som default |
| Reallocation | Forbudt som default |

## Owner review

Alt ekstern input skal gennem owner review.

Flow:

```text
external upload
  -> scoped inbox
  -> owner review
  -> owner approves/rejects
  -> only then can file move into case knowledge base
```

Eksternt uploadet materiale maa aldrig auto-indekseres direkte i en virksomheds vidensbase.

## Current status

Ekstern adgang er ikke aktiveret i den nuværende test-app.

Den nuværende app binder til:

```text
127.0.0.1
```

Det betyder lokal adgang paa Mac'en, ikke ekstern adgang.
