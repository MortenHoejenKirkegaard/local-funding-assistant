# Validation loops

Dette dokument beskriver de praktiske loops, der skal koere for at kontrollere, at systemet placerer, indekserer og genererer korrekt.

## Loop 1: Policy gate

Koeres foer alle agenthandlinger.

```text
proposed action
  -> classify action
  -> validate against policy
  -> allowed / requires_approval / blocked
  -> log decision
```

Pass criteria:

- Ukendte handlinger blokeres.
- API-analyse kraever approval.
- Betalinger, aftaler, data sharing, email og tredjepartsbeskeder blokeres.
- Slack er kun tilladt til brugeren selv og kun som kort ikke-fortroligt resume.

## Loop 2: Path gate

Koeres foer enhver filoperation.

```text
input path
  -> resolve absolute path
  -> reject symlink escape
  -> verify path starts with allowed root
  -> allow file operation
```

Pass criteria:

- Path inden for `Codex Access` accepteres.
- Path uden for `Codex Access` afvises.
- Symlink der peger ud af projektmappen afvises.

## Loop 3: Drag-and-drop ingestion

Koeres naar brugeren dropper en fil i dashboardet.

```text
drop file
  -> copy to funding-assistant/system/inbox
  -> create ingestion_job
  -> compute sha256
  -> suggest company/project/document type
  -> wait for user confirmation
  -> move to selected case folder
  -> parse file
  -> create documents and document_chunks
  -> index in correct company collection
  -> mark job indexed
```

Pass criteria:

- Ingen fil flyttes direkte til case-mappe uden brugerbekraeftelse.
- Valgt virksomhed matcher destination path.
- Dokumenttype matcher destination folder.
- Sha256 gemmes foer indeksering.
- Parserfejl giver `failed` status og sletter ikke originalfilen.

## Loop 4: Index verification

Koeres efter parsing og chunking.

```text
document record
  -> verify source file exists
  -> verify sha256 matches file
  -> verify company_id exists
  -> verify chunks exist
  -> verify vector payload has matching company_id
```

Pass criteria:

- Dokumentet kan spores tilbage til en lokal fil.
- Chunks refererer til korrekt document_id.
- Vektorindeks maa ikke blande company_id paa tvaers.

## Loop 5: Output validation

Koeres foer drafts eller Slack-beskeder vises/sendes.

```text
generated output
  -> check target channel
  -> check confidentiality
  -> check citations/source references
  -> check assumptions
  -> approve dashboard output or Slack summary
```

Pass criteria:

- Drafts i dashboardet har kilder eller antagelsesmarkering.
- Slack indeholder kun kort summary.
- Slack indeholder ikke fulde dokumentuddrag, patentclaims eller fulde drafts.
- Outputs med usikre udsagn markeres som antagelser.

## Minimum automated checks now

Foerste testpakke skal indeholde:

- Unit tests for action policy.
- Unit tests for path validation.
- Unit tests for Slack-output restrictions.

Naeste testpakke skal indeholde:

- Integration test for ingestion job flow.
- Integration test for document placement.
- Integration test for duplicate hash handling.
- Output validation test for Slack summary vs dashboard draft.
