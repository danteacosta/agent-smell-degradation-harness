# Advisor meeting — 8 September 2026

## The finding to lead with

We have completed instrument-development results, not a semantic-preservation
estimate. The corrected pre-pilot ran end to end. Later source-derived controls
showed why its machine labels cannot yet support H1/H2: the evaluators confused
missing context with omission and sometimes supplied unusable evidence.

The latest comparison completed its entire development block. It did not stop
because of an unresolved charge. Its predeclared gate failed, so evaluation and
main-cohort generation stayed locked.

V4 made evidence outputs usable in 24/24 calls, versus 10/24 for quote-based v3.
It matched 23/24 constructed answers, but answered `uncertain` on one deliberate
long omission. That abstention, not a false `clean` response, failed the required
omission criterion. We fixed an observed interface problem without establishing
that the evaluator is ready for the main study.

## Evidence available

| Study | Completed work | Defensible result | Usage-priced cost |
| --- | --- | --- | ---: |
| Corrected exploratory pre-pilot | 120 variant-specific slots per provider; 240 artifacts; 1,296 calls | Operational execution and substantive T1/T2 fields; 279 `clean` / 9 `uncertain` are machine judgments, not preservation rates | US$0.194731 |
| Source diagnostic | 96/96 calls; 48 per provider | Both detected 6/6 constructed long omissions but abstained on 0/6 partial excerpts; invalid responses: OpenAI 3/48, DeepSeek 16/48 | US$0.030728 |
| Scope-aware v2/v3 development | 48/48 calls; 12 per configuration | Valid and construction-matching: v2 5/12 for each provider; v3 OpenAI 6/12, DeepSeek 5/12. Gate failed | US$0.023175 |
| Artifact-addressed v3/v4 development | 48/48 calls; 12 per configuration | V4: 24/24 valid and 23/24 exact construction matches; v3: 10/24 valid and exact. One v4 abstention on a long omission failed the gate; no evaluation dispatch | US$0.028024 |
| Executable contracts | Four contracts; 16 test-vector executions; four mutants detected | Checks the formal implementation, not its translation from natural requirements | No provider calls |
| Temporal analysis | T1, T1+T2 and T1–T3 analysis implemented and tested | Retains partial costs and bounds missing-checkpoint effects; empirical early-warning benefit remains unmeasured | No new collection |

The parent pilot ledger also contains 72 screening calls costing US$0.031817.
Parent plus both auxiliary studies therefore totals **264 calls / US$0.113744**. This
subtotal excludes the earlier pre-pilot and other comparison studies. Prices are
frozen accounting inputs, not invoices. The earlier unresolved US$0.000218
reservation remains held; no ambiguous call was retried.

## What the latest failure means

The v4 gate required every response to be valid, at least 10/12 exact matches
per provider, and perfect matches on specified omission and partial-scope
operations. Its aggregate result was high, but provider slot 1 matched only
1/2 long-omission controls. That operation-level failure keeps all 96 evaluation
calls locked. The two development locators provide dependent variants, not a
population sensitivity estimate.

Of the ten v3/v4 pairs valid in both arms, nine were exact in both and one was
exact only in v3. The larger planned-denominator gain primarily reflects usable
evidence responses. It does not demonstrate better semantic decisions among
jointly scorable pairs or validate the AI-assisted construction answers.

## Earlier failure that motivated the interface

In the preceding v2/v3 study, twelve v3 responses copied excerpts longer than
the 120-character contract. All came from one source locator. Two DeepSeek responses instead quoted reference
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

Preserve the negative studies and stop collecting this version. The segment-ID
interface has now been implemented and tested with providers; it establishes
where a citation came from, not whether it entails the obligation. Inspect the
remaining omission abstention and the construction rationale as post-hoc
diagnosis, without changing the gate or rescoring the study.

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
- [Artifact-addressed comparison results](addressed-comparison-results.md) and [live execution contract](addressed-comparison-live.md)

Only redacted aggregate evidence is public. Raw sources, responses, run identities,
configuration hashes and append-only ledgers remain in approved private storage.
