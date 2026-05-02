# Adgangsrestriktioner

Systemet maa kun arbejde inden for denne lokale rodmappe:

```text
/Users/mortenkirkegaard/Desktop/Codex Access
```

Det betyder, at agenter, workers, dashboard og fremtidig Mac control app som standard skal afvise laesning og skrivning uden for denne mappe.

## Praktiske regler

- Ingen agent maa scanne hele computeren.
- Ingen agent maa bruge brugerens Desktop, Downloads, Documents eller iCloud direkte.
- Drag-and-drop filer kopieres foerst ind i systemets egen dropzone.
- Filer maa kun flyttes videre til `funding-assistant/cases/...` efter brugerens valg af virksomhed og projekt.
- Symlinks maa ikke kunne bruges til at snyde systemet ud af rodmappen.
- Eksterne API-kald skal fortsat kraeve godkendelse, medmindre brugeren specifikt har sat en auto-mode.

## Tilladt datarum

```text
Codex Access/
  config/
  db/
  docs/
  funding-assistant/
  scripts/
```

## Fortrolige dokumenter

Fortrolige Word-, Excel-, PowerPoint-, PDF- og billedfiler skal ligge under:

```text
funding-assistant/cases/company-*/...
funding-assistant/applications/historical/...
```

Disse filer er udelukket fra Git via `.gitignore`.

## Dropzone

Drag-and-drop agenten bruger denne interne dropzone:

```text
funding-assistant/system/inbox
```

Flow:

1. Brugeren dropper en fil i dashboardet.
2. Systemet kopierer filen til dropzone.
3. Systemet viser forslag til virksomhed, projekt og dokumenttype.
4. Brugeren bekraefter eller retter valget.
5. Systemet flytter filen til korrekt case-mappe.
6. Systemet udtraekker tekst, metadata og hash.
7. Systemet opdaterer database og indeks.

## Implementeringsregel

Alle file paths skal normaliseres og valideres med en helper-funktion foer brug:

```text
resolved_path must start with allowed_root
resolved_path must not resolve through a symlink outside allowed_root
```

Hvis validering fejler, skal opgaven stoppes og logges i `audit_events`.
