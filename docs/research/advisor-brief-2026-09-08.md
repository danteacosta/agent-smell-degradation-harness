# Advisor meeting — 8 September 2026

## The finding to lead with

We have completed instrument-development results, not a semantic-preservation
estimate. The corrected pre-pilot ran end to end. Later source-derived controls
showed why its machine labels cannot yet support H1/H2: the evaluators confused
missing context with omission and sometimes supplied unusable evidence.

The latest comparison completed its entire development block. It did not stop
because of an unresolved charge. Its predeclared gate failed, so evaluation and
main-cohort generation stayed locked.

## Evidence available

| Study | Completed work | Defensible result | Usage-priced cost |
| --- | --- | --- | ---: |
| Corrected exploratory pre-pilot | 120 variant-specific slots per provider; 240 artifacts; 1,296 calls | Operational execution and substantive T1/T2 fields; 279 `clean` / 9 `uncertain` are machine judgments, not preservation rates | US$0.194731 |
| Source diagnostic | 96/96 calls; 48 per provider | Both detected 6/6 constructed long omissions but abstained on 0/6 partial excerpts; invalid responses: OpenAI 3/48, DeepSeek 16/48 | US$0.030728 |
| Scope-aware v2/v3 development | 48/48 calls; 12 per configuration | Valid and construction-matching: v2 5/12 for each provider; v3 OpenAI 6/12, DeepSeek 5/12. Gate failed | US$0.023175 |
| Executable contracts | Four contracts; 16 test-vector executions; four mutants detected | Checks the formal implementation, not its translation from natural requirements | No provider calls |
| Temporal analysis | T1, T1+T2 and T1–T3 analysis implemented and tested | Retains partial costs and bounds missing-checkpoint effects; empirical early-warning benefit remains unmeasured | No new collection |

The parent pilot ledger also contains 72 screening calls costing US$0.031817.
Parent plus auxiliary study therefore totals **216 calls / US$0.085720**. This
subtotal excludes the earlier pre-pilot and other comparison studies. Prices are
frozen accounting inputs, not invoices. The earlier unresolved US$0.000218
reservation remains held; no ambiguous call was retried.

## What the latest failure means

Twelve v3 responses copied excerpts longer than the 120-character contract. All
came from one source locator. Two DeepSeek responses instead quoted reference
text that was absent from the artifact; one overlaps the length failures.
There are thirteen invalid v3 responses, not fourteen.

Length compliance and evidence grounding are different problems. Increasing the
quote limit would not fix a citation to an obligation absent from the artifact.
Post-hoc inspection found more intended raw statuses than strict valid responses,
but that inspection does not repair the evidence or change the gate.

The development block has only two source locators with dependent variants.
It is not an estimate of general model sensitivity, and all construction answers
remain AI-assisted rather than independently validated human labels.

## Keep the counting units separate

The corrected pre-pilot has 12 intents × 2 variants × 5 repetitions = 120 slots
per provider. Across two providers there are 240 artifacts and 120 clean/smelly
contrasts, not 120 independent requirements. Its 288 consolidated judgments
include duplicated annotation occurrences and are not an artifact count.

The proposed main pilot has 24 intent IDs across six project IDs, 240 slots per
provider and 480 provider-specific trajectories. **None has been generated.**
The IDs and project count do not establish statistical or semantic independence.

## Recommended next decision

Preserve the negative studies and stop tuning this version. Review a separate
evidence-interface proposal: let the model select immutable artifact-segment IDs
and have the harness resolve them to text. Keep reference and artifact namespaces
distinct. A valid segment ID would establish where evidence came from, not whether
it entails the obligation.

Before another paid study, register the revised interface, comparator, cases,
validity and sensitivity criteria, uncertainty handling and joint cost envelope.
Do not reuse the four locked evaluation locators as development examples. A new
diagnostic decision must precede any main-cohort release; no launch date is yet
scientifically justified.

The advisor decision is methodological: retain H1/H2 pending independent outcome
validation, or explicitly revise the thesis's primary claim toward instrument
behavior under construction-based tests. LLM consensus alone cannot make that
decision or supply human validity. A small random human audit, distinct from a
difficult-case queue, remains a future calibration option. Product usefulness and
investigation time remain a separate roadmap study.

## Meeting materials and audit trail

- [Current proposal](https://docs.google.com/document/d/1sio6UiAciypbKGu7mbs8nlQJv2xvc3t888SvaShmB2w/edit)
- [Operational report](https://docs.google.com/document/d/1wSv-khPmRusFKwk4PO02qmbY6eg1MTjJ0QGHTlZuzuI/edit)
- [Ten-slide presentation with speaker notes](https://docs.google.com/presentation/d/1x1KonwCvIogtr4b3puGrIUDOoa7KkBLwcFmRO_b1vbc/edit)
- [Source diagnostic results](source-diagnostic-results.md)
- [Scope-aware development results](scoped-judge-results.md) and [frozen design](../plans/2026-09-07-scoped-judge-study.md)

Only redacted aggregate evidence is public. Raw sources, responses, run identities,
configuration hashes and append-only ledgers remain in approved private storage.
