# The complete-requirement advantage survives an assertion-only sensitivity

This **post-hoc, descriptive audit** separates assertion alarms from error
alarms in the three published shared-omission tester packets. It reuses the
same 25 requirements, eight projects and saved browser verdicts; it adds no
independent requirements or executions. Registered scores and MA1/MA2 remain
unchanged. Sonnet 5.5 and Opus 5.5 are outside this report.

## Method and result

First require exact schedule/target coverage, identity and role correspondence,
including failure placeholders. Recompute each frozen published analysis and
require equality. Then count only `assertion_alarm` as a kill, retaining the
original suite-usability/reference-quiet gate. Average two suites within each
requirement, then give requirements equal weight. Error-only kills lose credit;
failed, unusable and reference-rejecting suites retain zero in the planned
denominator. No new significance test or threshold is selected.

| Tester | Source | Registered score | Assertion-only score | Assertion / error kills among eligible mutant pairs | Eligible mutant pairs |
| --- | --- | ---: | ---: | --- | ---: |
| Astra | Complete requirement | 0.760 | 0.660 | 109 / 9 | 118 |
| Astra | Incomplete request | 0.100 | 0.100 | 13 / 0 | 123 |
| Astra | Incomplete + mutant code | 0.040 | 0.040 | 6 / 0 | 66 |
| Sonnet 4.6 | Complete requirement | 0.400 | 0.360 | 59 / 7 | 87 |
| Sonnet 4.6 | Incomplete request | 0.050 | 0.050 | 9 / 0 | 74 |
| Sonnet 4.6 | Incomplete + mutant code | 0.000 | 0.000 | 0 / 0 | 57 |
| Opus 4.6 | Complete requirement | 0.800 | 0.760 | 126 / 6 | 149 |
| Opus 4.6 | Incomplete request | 0.085 | 0.085 | 13 / 0 | 110 |
| Opus 4.6 | Incomplete + mutant code | 0.000 | 0.000 | 0 / 0 | 51 |

Each source has 50 planned suites and 162 planned confirmed-mutant pairs per
tester. The last column is conditional on eligibility, **not** the score's
denominator. Pair counts do not receive equal weight across requirements.

The observed advantage of complete text is not entirely explained by error
alarms: the point-score contrast remains positive for each tester. This is a
robustness check on the selected implementations, not a new independent
replication. Rejecting a correct reference still disqualifies a suite even if
it contains assertions; no reference error is converted into eligibility.

## What remains unknown

The suite-level `assertion_alarm` verdict indicates at least one assertion
failed. It does not identify the checked `constraint_id`, prove that the
target journey was exercised, or exclude another assertion/error in that
suite. `error_alarm` likewise does not establish a crash in production code.
The existing [blind test audit](../preregistration/2026-10-06-shared-omission-test-audit.md)
must inspect the actual test condition and expected behavior before claiming
semantic target detection. Its private suites are not published by this script.

These questions are motivated by Du et al. (ISSTA 2023,
[DOI](https://doi.org/10.1145/3597926.3598090)), who distinguish killing reasons,
and Hamidi et al. ([preprint](https://arxiv.org/abs/2609.09315)), who distinguish
triggering a fault from detecting it. See credibility and transfer limits in
the [literature matrix](literature-matrix.md#2026-10-07--what-killed-the-mutant).

Next dependency: two independent coders and adjudication of the existing
blind suite audit. A product should report the tested condition and failure
reason rather than present these scores as global correctness. H1/H2 and
the confirmatory human gates remain unresolved.

## Reproduce without providers or browser reruns

Run from the repository root, choosing a **fresh** output path:

```bash
python scripts/mutation_alarm_sensitivity.py data/shared-omission-e2e/v1 --output /tmp/astra-sensitivity.json
python scripts/mutation_alarm_sensitivity.py data/shared-omission-e2e/claude-evaluation-v1/claude-sonnet-4-6 --output /tmp/sonnet-sensitivity.json
python scripts/mutation_alarm_sensitivity.py data/shared-omission-e2e/claude-evaluation-v1/claude-opus-4-6 --output /tmp/opus-sensitivity.json
```

[Versioned outputs](../../data/shared-omission-e2e/alarm-sensitivity-v1/) retain
input SHA-256 hashes and per-requirement scores. Their hashes bind the public
JSON inputs; they do not independently certify private evidence custody.
