# Matchmaking scoring-framework

Dette framework bruges af matchmaking-agenten til at vurdere, hvilke funding calls der passer bedst til hvilke portefoljevirksomheder og projekter.

## Output pr. match

Hvert match mellem et funding call og en virksomhed/projekt skal give:

- `overall_score`: samlet score fra 0 til 100.
- `priority`: `high`, `medium`, `low`, `watch`.
- `rationale`: kort forklaring paa hvorfor matchet findes.
- `missing_requirements`: konkret liste over manglende krav.
- `recommended_action`: naeste bedste handling.
- `confidence`: hvor sikkert systemet er paa vurderingen.

## Standardvaegte

| Dimension | Vaegt | Formaal |
| --- | ---: | --- |
| Strategisk fit | 20% | Passer call'et til virksomhedens fokus, roadmap og fundingbehov? |
| Eligibility | 20% | Opfylder casen de formelle krav? |
| Evidensniveau | 15% | Er teknisk, klinisk og markedsmaessig evidens staerk nok? |
| IP-fit | 10% | Passer IP-status til call'ets krav og risikoappetit? |
| Kommercielt potentiale | 10% | Er marked, reimbursement, kunder og go-to-market tydelige? |
| Historisk funder-fit | 10% | Ligner casen tidligere succesfulde ansoegninger? |
| Arbejdsindsats | 10% | Kan ansoegningen realistisk samles foer deadline? |
| Deadline urgency | 5% | Er timing og deadline relevante nok til prioritering? |

Samlet score:

```text
overall_score =
  strategic_fit_score * 0.20 +
  eligibility_score * 0.20 +
  evidence_score * 0.15 +
  ip_score * 0.10 +
  commercial_score * 0.10 +
  historical_funder_fit_score * 0.10 +
  effort_score * 0.10 +
  deadline_urgency_score * 0.05
```

## Score-definitioner

### Strategisk fit

| Score | Betydning |
| ---: | --- |
| 90-100 | Call'et passer direkte til et aktivt prioriteret projekt. |
| 70-89 | Godt match, men projektvinklen skal skærpes. |
| 50-69 | Delvist match med mulig omformulering. |
| 0-49 | Svagt match eller uden strategisk relevans. |

### Eligibility

| Score | Betydning |
| ---: | --- |
| 90-100 | Alle formelle krav er opfyldt. |
| 70-89 | Kun mindre bilag eller afklaringer mangler. |
| 50-69 | Et eller flere vigtige krav mangler, men kan muligvis loeses. |
| 0-49 | Casen er sandsynligvis ikke eligible. |

### Evidensniveau

Vurderes ud fra teknisk dokumentation, klinisk evidens, markedsdata og validering.

| Score | Betydning |
| ---: | --- |
| 90-100 | Solid evidens og tydelig dokumentation. |
| 70-89 | God evidens, men enkelte underbyggende dele mangler. |
| 50-69 | Lovende, men evidensgrundlaget er ujævnt. |
| 0-49 | For tyndt eller usikkert evidensgrundlag. |

### IP-fit

| Score | Betydning |
| ---: | --- |
| 90-100 | Patent/IP-status er klar, relevant og dokumenteret. |
| 70-89 | IP-position er god, men mangler enkelte detaljer. |
| 50-69 | IP-status er uklar eller delvist afhængig af tredjeparter. |
| 0-49 | IP-risiko kan svække ansoegningen væsentligt. |

### Kommercielt potentiale

| Score | Betydning |
| ---: | --- |
| 90-100 | Klar kunde, marked, betalingslogik og adoption pathway. |
| 70-89 | God kommerciel case med enkelte huller. |
| 50-69 | Markedspotentiale findes, men go-to-market er svag. |
| 0-49 | Kommerciel vinkel er ikke tydelig nok. |

### Historisk funder-fit

Vurderer om casen ligner tidligere godkendte ansoegninger eller fondens kendte stoetteprofil.

| Score | Betydning |
| ---: | --- |
| 90-100 | Meget tydelig lighed med tidligere succesfulde cases. |
| 70-89 | Flere positive mønstre genfindes. |
| 50-69 | Nogle matchende mønstre, men ingen stærk historik. |
| 0-49 | Svag eller modstridende historisk profil. |

### Arbejdsindsats

Her betyder høj score lavere praktisk risiko.

| Score | Betydning |
| ---: | --- |
| 90-100 | Næsten alle nødvendige dokumenter findes. |
| 70-89 | Realistisk at samle med moderat arbejde. |
| 50-69 | Kræver betydelig koordinering eller nye bilag. |
| 0-49 | Ikke realistisk inden deadline uden stor indsats. |

### Deadline urgency

| Score | Betydning |
| ---: | --- |
| 90-100 | Deadline inden for 3-14 dage og call'et er relevant. |
| 70-89 | Deadline inden for 15-30 dage. |
| 50-69 | Deadline inden for 31-60 dage. |
| 0-49 | Lang tid til deadline eller ukendt timing. |

## Prioritet

| Overall score | Priority | Handling |
| ---: | --- | --- |
| 85-100 | `high` | Send dashboard + Slack/email notifikation og foreslaa draft. |
| 70-84 | `medium` | Vis i dashboard og lav gap-liste. |
| 55-69 | `low` | Gem som potentiel mulighed. |
| 0-54 | `watch` | Overvaag, men prioriter ikke aktivt. |

## Hard blockers

Disse forhold skal kunne sænke eller blokere et match, selv hvis tekstlig lighed er høj:

- Virksomheden opfylder ikke formelle eligibility-krav.
- Deadline er passeret.
- Krævet partner mangler og kan ikke realistisk skaffes.
- Krævet TRL/modenhed ligger væsentligt over virksomhedens status.
- Krævet klinisk evidens findes ikke.
- IP-status er uforenelig med fondens krav.
- Budgetrammen ligger langt under eller over projektets reelle behov.

Hvis et hard blocker findes, skal `priority` normalt sættes til `watch` eller `low`, og `missing_requirements` skal forklare hvorfor.

## Gap-analyse

Matchmaking-agenten skal altid producere en gap-liste med status.

```yaml
missing_requirements:
  - requirement: Partner letter
    severity: high
    owner: user
    can_be_fixed_before_deadline: true
    suggested_action: Request signed LOI from clinical partner.
  - requirement: Updated budget
    severity: medium
    owner: application_agent
    can_be_fixed_before_deadline: true
    suggested_action: Draft budget narrative from milestone plan.
```

## Confidence

Confidence beskriver hvor paalidelig vurderingen er, ikke hvor stærkt matchet er.

| Confidence | Betydning |
| ---: | --- |
| 0.80-1.00 | Godt datagrundlag og tydelige call-kriterier. |
| 0.60-0.79 | Brugbar vurdering, men enkelte datamangler. |
| 0.40-0.59 | Indikation, kræver manuel validering. |
| 0.00-0.39 | For usikkert til aktiv prioritering. |

## Dashboard-kort

Et match-kort i dashboardet skal vise:

- Funder og call-navn.
- Deadline og tid tilbage.
- Virksomhed og projekt.
- Overall score og priority.
- De tre stærkeste fit-argumenter.
- De tre vigtigste mangler.
- Anbefalet handling: `draft`, `collect_documents`, `monitor`, `ignore`.

## Slack/email-regel

Slack og email maa kun sendes ved:

- `priority = high`
- `overall_score >= 85`
- ingen uløste hard blockers
- deadline inden for 30 dage eller ny opportunity med meget stærkt match

Slack/email-beskeder maa ikke indeholde fuld ansøgningstekst, patentdetaljer eller fortrolige dokumentuddrag. Beskeden skal pege tilbage til dashboardet.

## Første standardbesked

```text
Relevant funding opportunity fundet:

Call: {funding_call_title}
Deadline: {deadline_at}
Match: {company_name} / {project_name}
Score: {overall_score}/100

Hvorfor den passer:
{top_rationale_points}

Vigtigste mangler:
{top_missing_requirements}

Anbefalet handling:
{recommended_action}
```
