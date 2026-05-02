# Ekstern adgangspolitik

Eksterne personer maa ikke have almindelig adgang til systemet.

Hvis ekstern adgang senere aktiveres, skal den vaere begrænset til:

- En navngiven ekstern bruger.
- Et invitation link oprettet af owner.
- Verificeret email-kode sendt til den inviterede email.
- Owner approval foer kontoen bliver aktiv.
- En specifik scoped mappe under `Codex Access`.
- Et tildelt flow, fx upload eller besvarelse af afklaringsspørgsmaal.
- Owner review foer noget flyttes, indekseres eller bruges i drafts.

## Grundregel

Eksterne kan kun foelge flowet. De maa ikke styre systemet.

Ingen ekstern bruger maa blive aktiv alene ved at have et link. Linket er kun trin 1.

Aktivering kraever alle disse trin:

```text
owner creates invite
  -> invite link opens external portal
  -> email verification code is sent
  -> user enters code
  -> owner approves access
  -> scoped flow becomes available
```

Hvis et af trinene mangler, skal adgangen blokeres.

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

## Invite og email verification

Invite-regler:

- Kun owner kan oprette invite.
- Invite skal vaere knyttet til en email.
- Invite skal vaere knyttet til en scoped root folder.
- Invite skal vaere knyttet til et konkret flow.
- Invite udloeber automatisk.
- Invite link maa ikke give adgang uden email-kode.

Email verification-regler:

- Koden sendes til den inviterede email.
- Koden maa kun bruges én gang.
- Koden udloeber efter kort tid.
- For mange fejlede forsoeg skal revoke eller blokere invite.
- Verificeret email giver stadig ikke aktiv adgang uden owner approval.

Owner approval:

- Owner skal manuelt godkende aktivering efter email-verifikation.
- Owner kan revoke adgang naar som helst.
- Al aktivitet logges.

## Portal-ruter

Ekstern portal maa kun bruge ruter under:

```text
/external/
```

Admin- og owner-ruter maa ikke kunne naas fra ekstern portal-session.

## Current status

Ekstern adgang er ikke aktiveret i den nuværende test-app.

Den nuværende app binder til:

```text
127.0.0.1
```

Det betyder lokal adgang paa Mac'en, ikke ekstern adgang.
