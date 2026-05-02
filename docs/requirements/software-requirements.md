# Software requirements for MVP validation

Dette er en let kravbase for unit tests og validation loops. Kravene er ikke en fuld regulatory pakke, men de giver sporbarhed mellem sikkerhedsregler, systemadfaerd og tests.

| ID | Requirement | Verification |
| --- | --- | --- |
| SREQ-001 | Systemet maa kun laese og skrive filer inden for `Codex Access` rodmappen. | Unit test: path validation |
| SREQ-002 | Ukendte action-typer skal blokeres som default. | Unit test: policy validation |
| SREQ-003 | Lokale laese- og skrivehandlinger maa tillades. | Unit test: policy validation |
| SREQ-004 | API-analyse maa kraeve eksplicit cost approval. | Unit test: policy validation |
| SREQ-005 | Betaling, koeb, abonnementer og checkout skal blokeres. | Unit test: policy validation |
| SREQ-006 | Aftaler, signaturer, konto-oprettelse og terms acceptance skal blokeres. | Unit test: policy validation |
| SREQ-007 | Ekstern data sharing, filupload, email og tredjepartsbeskeder skal blokeres. | Unit test: policy validation |
| SREQ-008 | Slack-output maa kun sendes til brugeren selv. | Unit test: policy validation |
| SREQ-009 | Slack-output maa ikke indeholde fortroligt indhold, fulde dokumenter eller fulde drafts. | Unit test: policy validation |
| SREQ-010 | Drag-and-drop filer skal placeres i intern inbox foer brugerbekraeftet destination. | Integration validation loop |
| SREQ-011 | Ingestion maa foerst flytte fil til case-mappe efter valgt virksomhed og dokumenttype. | Integration validation loop |
| SREQ-012 | Indeksering skal gemme source path, sha256, dokumenttype og company_id. | Integration validation loop |
| SREQ-013 | Generated outputs skal have kildehenvisninger eller markeres som antagelse. | Output validation loop |

