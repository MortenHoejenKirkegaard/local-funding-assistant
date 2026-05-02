# Production parity

Alt funktionelt flow, der bygges i testmiljoeet, skal have en tilsvarende implementering i det egentlige setup.

Det gaelder aktuelt:

- First-launch setup for en eller flere virksomheder.
- Navngivning, omdoebning, tilfoejelse og fjernelse af virksomheder.
- Aliaser, akronymer og projektforkortelser til foerste indexing pass.
- Upload, bulk upload, sletning og manuel rettelse af allokationer.
- Auto-index ved confidence paa mindst 95%.
- Manuel bekraeftelse ved confidence under 95%.
- Skriveagent for successfulde og unsuccessfulde funding applications.
- Kobling af applications til intern virksomhed, ekstern virksomhed eller ukendt.
- Lokal sproglig pattern-analyse uden API-kald.
- Weekly softfunding screening som default schedule.
- Ekstern collaborator access maa kun ske via scoped folder og assigned flow.
- Ekstern adgang kraever invite link, email-verifikationskode og owner approval.

Testmiljoeet maa gerne bruge simplere storage og parsere, men brugerflow og sikkerhedsregler skal svare til produktion.
