# Ekstern portal flow

Dette dokument beskriver den stramme invite-only adgang for eksterne brugere.

## Flow

```text
1. Owner opretter invite
2. Systemet genererer invite link
3. Ekstern bruger aabner link
4. Systemet sender kode til inviteret email
5. Ekstern bruger indtaster kode
6. Systemet markerer email som verificeret
7. Owner godkender adgang
8. Ekstern bruger faar adgang til scoped flow
9. Uploads lander i external scoped inbox
10. Owner reviewer alt foer videre brug
```

## Required gates

Ekstern adgang kraever:

- Valid invite
- Ikke-udloebet invite
- Email-kode verificeret
- Owner approval
- Scoped root path
- Assigned flow

Hvis noget mangler, skal systemet vise en neutral adgangsfejl og logge eventet.

## Ekstern bruger maa kun se

- Egen uploadside
- Egen flow-status
- Egne uploadede filer i flowet
- Spørgsmaal fra owner/systemet i samme flow

## Ekstern bruger maa aldrig se

- Portfolio dashboard
- Funding radar
- Match scores
- Drafts
- Dokumenter fra andre cases
- Dokumenter fra andre eksterne
- API usage
- Audit logs
- System settings

## Owner review queue

Alt ekstern input skal ende i en review queue:

```text
external/{external_user_id}/inbox
  -> owner review
  -> approve/reject
  -> if approved: copy/move to relevant case intake
```

Eksternt materiale maa ikke auto-indekseres ind i case knowledge base.

## Security defaults

- External access default: off
- Downloads default: off
- Deletes default: off
- Reallocation default: off
- API access: blocked
- Agent controls: blocked
- Cross-company access: blocked
