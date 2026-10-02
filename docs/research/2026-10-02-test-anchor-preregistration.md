# Test-anchor experiment: pre-registration

Frozen on 2026-10-02, before any tester call. Script:
[`scripts/test_anchor_experiment.py`](../../scripts/test_anchor_experiment.py).
Runner: [`eval/fixtures/test-anchor/runner.cjs`](../../eval/fixtures/test-anchor/runner.cjs).

## Question

When a coding agent's implementation has lost a requirement condition, does a
generated browser test suite notice? And does the answer depend on what the
test writer reads?

Automated QA tools for pull requests typically infer what to test from the
change itself: the diff and the PR description. If the rule never reached the
code, there is nothing in the change that points at it. This experiment
measures that blind spot on artifacts whose ground truth is already known.

## Material

The three October replication packets (2026-10-01): RealWorld Favorites,
OpenProject invalid Remaining work and Paperless duplicate consumption. From
each, the A (complete requirement) and C (one condition omitted) artifacts
whose frozen, qualified oracle verdict is `pass` or `target_only_failure`.
That is 12 artifacts per case, 36 in total, of which 11 are C artifacts with a
target failure (OpenProject 6, Paperless 5) and 25 pass the oracle.

The oracle verdicts were recorded before this study was designed and are
never shown to the test writer.

## Strategies

All three receive identical instructions and output contract and differ only
in the inputs:

| Strategy | Requirement shown | Implementation shown | Suites |
| --- | --- | --- | --- |
| `code_request` | the request the coding agent received (C text for C artifacts) | yes | one per artifact |
| `code_spec` | the complete requirement (A text) | yes | one per artifact |
| `spec_only` | the complete requirement (A text) | no, scaffold only | three per case, each run on all 12 artifacts |

`code_request` models a diff-reading QA tool. `code_spec` models a tool that
also reads the ticket. `spec_only` writes tests from the ticket alone, as an
independent oracle would.

One tester model is used for every call; it is recorded in the frozen
manifest. 81 calls in total, in a seeded random order, no retry or repair.

## Outcomes

Each suite runs in the qualified network-disabled image against its target
artifacts. A suite **alarms** on an artifact when any of its tests throws.
`assertion_alarm` (an explicit assertion failed) is reported separately from
`error_alarm` (a timeout, missing element or other exception).

* **Detection**: alarms on oracle-failure artifacts.
* **False alarm**: alarms on oracle-pass artifacts.

Primary analysis is intention-to-test: every planned suite/artifact pair stays
in the denominator, and a suite that is invalid or not generated counts as no
alarm. A usable-only analysis is secondary. All counts are reported per case.

## Predictions

1. `spec_only` detects more oracle failures than `code_request`.
2. `code_spec` detects fewer than `spec_only`: reading the implementation pulls
   tests toward what was built even when the rule is available.
3. A strategy is only preferred if its detection minus its false-alarm rate is
   higher, so noisy suites do not win by failing everything.

Prediction 1 is close to expected by construction, since `code_request` never
sees the rule for C artifacts; it quantifies the blind spot rather than
discovering it. Prediction 2 is the informative one.

## Runner qualification

Before generated suites run, `controls` mode executes one authored suite on
three authored OpenProject artifacts: rule kept (expected quiet), rule lost
(expected assertion alarm) and save broken (expected assertion alarm). Any
mismatch stops the study.

## Limits

Three requirements, two coding models, eleven oracle failures, and repetitions
nested in cases: the counts are descriptive, not population estimates. The
tester model and the implementation models come from one provider family.
`code_request` and `code_spec` receive the same requirement text for A
artifacts. This is not part of the H1/H2 confirmatory protocol.

## Commands

One shot, from the repository root on the collection machine:

```sh
bash scripts/run_test_anchor.sh            # tester model defaults to gpt-6-astra
```

The script locates each private packet by matching both its frozen receipt and
final collection receipt hashes with the public summary. Replications may reuse
a frozen receipt, so that receipt alone does not identify a collection. Missing
or duplicate matches stop the script before tester calls. Step by step:

```sh
python scripts/test_anchor_experiment.py controls --out RUN/controls
python scripts/test_anchor_experiment.py prepare --out RUN/study --model MODEL \
  --packet realworld-favorites=PACKET --packet openproject-invalid-remaining=PACKET \
  --packet paperless-duplicate-consumption=PACKET
python scripts/test_anchor_experiment.py generate --out RUN/study
python scripts/test_anchor_experiment.py execute --out RUN/study
```
