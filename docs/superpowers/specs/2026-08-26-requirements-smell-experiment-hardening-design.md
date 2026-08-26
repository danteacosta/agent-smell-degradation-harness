# Requirements-smell experiment hardening design

Date: 2026-08-26

## Goal

Harden the requirements-smell discovery experiment so that its next offline
bundle is technically correct, auditable, and explicit about what it does and
does not establish. The immediate run must correct known detector and artifact
defects, report uncertainty without inflating evidence from repeated
deterministic fixtures, and leave a clean seam for later live-model runs.

This work is still discovery-stage. It must not present the deterministic stub
as an LLM evaluation or claim production latency, cost, sandbox isolation, or
generalization to unseen requirements.

## Decisions and alternatives

### Recommended: correctness fixes plus an honest repeated-pipeline run

The verifier and artifact materializer remain the owners of their current
responsibilities. We add small, public measurement helpers rather than
introducing a new framework:

- the verifier uses word-bounded matching for completeness markers;
- the materializer normalizes generated source and diff input to final-newline
  terminated text;
- efficacy output contains Wilson 95% intervals for the unique eligible
  behavior cases and separately records repetition stability;
- offline run metadata names its repetitions as deterministic pipeline
  repeats, not independent model replications;
- live provider metadata continues to record provider, model, latency, cost,
  parse failures, and prompt/configuration identity without secrets.

This is recommended because it fixes the observed false negative and malformed
evidence with minimal coupling, while avoiding fabricated randomness.

### Alternative A: add synthetic randomness to the stub

Rejected for the main result. It would increase the number of rows but would
not create independent evidence about model behavior; it could make the
experiment look more robust while measuring an invented failure distribution.

### Alternative B: wait for the API key before changing anything

Rejected for this iteration. The offline pipeline has correctness defects that
can and should be fixed independently of provider credentials. Live-model
evaluation remains a follow-up run after the key, model configurations, budget,
and Linux/CI sandbox are supplied.

## Scope

### In scope

1. Add a regression test showing that `shall consider anticipated user
   requests` emits `incomplete_completeness_scope`, while the clean form with
   `both anticipated and unanticipated` does not.
2. Fix the detector regex using explicit word boundaries.
3. Add artifact tests for final-newline-safe generated source and unified diffs.
4. Add uncertainty helpers and output for recall, precision, specificity, and
   paired discrimination. The primary interval unit is one unique
   intent/task-family decision or pair, not duplicated deterministic rows.
5. Add metadata that distinguishes unique eligible behavior cases,
   non-behavior decisions (`test_gen`), deterministic repeated-pipeline
   observations, and independent live-provider replications.
6. Rerun the offline discovery experiment with five deterministic repetitions
   under a new immutable run id and verify the complete artifact bundle.
7. Update the experiment-facing README/report text to explain the denominator,
   confidence intervals, the Mac `trusted_fixture` limitation, and the
   follow-up live-model design.

### Out of scope for this iteration

- API calls or use of an API key that has not yet been provided;
- claiming that the stub generalizes to reformulated or unseen requirements;
- expanding the corpus with unreviewed smell labels;
- changing the smell taxonomy or threshold policy;
- implementing the intervention arms (agent without verifier, with alert, and
  with alert plus revision). Those require a real agent contract and are the
  next confirmatory design step.

## Architecture and data flow

The flow remains:

```text
pair corpus
  -> discovery runner (clean/smelly × task family × repetition)
  -> episodes + pre-final observable traces + terminal behavior reports
  -> verifier freezes decisions before labels are joined
  -> efficacy metrics and uncertainty summary
  -> immutable artifact bundle
```

The verifier must continue to consume only the observable allowlist and
pre-final trace. Terminal labels and generated artifacts are joined only after
decisions are frozen. The experiment runner owns repetition metadata; the
verifier owns decision metrics and their uncertainty; the materializer owns
portable evidence files and diffs.

For the v7 offline run, all five repetitions use the same deterministic stub.
The aggregate efficacy view is therefore deduplicated by the exact key
`(intent_id, variant, task_family)`. Every key must have one value in each
repetition. The deduplicated value is the first repetition's row, and a
separate stability section verifies that risk score, decision, and terminal
label are identical in every later repetition. The run may demonstrate
pipeline repeatability, but its intervals remain descriptive and are not
evidence of independent model-sample uncertainty.

The 48-row shape at one repetition remains understandable: 24 `test_gen`
decisions are observability-only and 24 `behavior_codegen` decisions are
eligible for the binary efficacy matrix. With five repetitions, those counts
scale to 240 total decisions, 120 non-behavior decisions, and 120 raw eligible
rows, while the unique efficacy denominator remains 24.

## Measurement definitions

The binary efficacy matrix is built only from `behavior_codegen` rows whose
terminal behavior label is available. `smelly` is the positive class
(`label=1`, target condition failed); `clean` is the negative class
(`label=0`, target condition passed). An alert is any verifier decision other
than `approve` (`warn` or `block`). The primary unique-case unit is one
`(intent_id, variant, task_family)` row after the repetition key above is
deduplicated. The paired unit is one complete
`(intent_id, task_family)` pair containing both variants.

| Metric | Formula | Denominator / unit |
| --- | --- | --- |
| Recall / warning coverage | `TP / (TP + FN)` | unique smelly behavior rows |
| Precision | `TP / (TP + FP)` | unique alerted behavior rows |
| Specificity | `TN / (TN + FP)` | unique clean behavior rows |
| False-alert rate | `FP / (FP + TN)` | unique clean behavior rows |
| Paired discrimination | smelly risk score `>` clean risk score | complete unique intent×task pairs; ties are not wins |

Wilson intervals are two-sided 95% intervals for recall, precision,
specificity, false-alert rate, and paired discrimination. The interval unit is
the unique row or unique pair stated in the table; repeated deterministic
rows are never included as additional independent observations. If a
denominator is zero, both interval bounds are `null` and the metric is
inconclusive.

## Contracts and failure handling

- A detector regression must fail before the regex fix and pass after it.
- A generated source string is materialized as UTF-8 text with LF line endings
  and exactly one final `\n`; existing internal content is otherwise preserved
  after CRLF/CR normalization and removal of trailing blank lines.
- A comparison file must contain a parseable fenced unified diff whose lines do
  not accidentally concatenate at a source boundary.
- Wilson intervals must be emitted only for non-empty denominators. Empty
  strata receive `null` bounds and an explanatory status, never a fabricated
  zero-width interval.
- Repeated deterministic rows must not be silently treated as independent
  samples. Run metadata and the metric section must make the limitation
  machine-readable and human-readable.
- Configuration identity is a SHA-256 hash of canonical JSON with sorted keys,
  compact separators, and no credentials, prompts, generated artifacts, or
  terminal labels. The exported field is `configuration_id` and its value is
  the hash; prompt identity is a separate SHA-256 hash of the exact prompt
  bytes when a live provider records it.
- Live mode must continue to fail closed when credentials/dependencies are
  absent and must never serialize API keys, prompts, or terminal artifacts into
  provider manifests.
- Existing leakage checks, trusted-fixture safety checks, and CI gates must
  remain green.

## Test-first acceptance criteria

### Detector behavior

Given a smelly requirement containing `shall consider anticipated user
requests`, when the observable verifier derives signals, then it emits the
completeness-scope signal.

Given a clean requirement containing `shall consider both anticipated and
unanticipated user requests`, when the verifier derives signals, then it does
not emit that completeness-scope signal.

### Artifact behavior

Given generated source without a final newline, when the bundle is materialized,
then the generated file ends in a newline and its comparison diff preserves
separate added/removed lines.

### Measurement behavior

Given five identical offline repetitions of the 12-case corpus, when the
bundle is verified, then run metadata reports five deterministic pipeline
repeats, the raw decision count is 240, `test_gen` remains outside the binary
efficacy denominator, and unique eligible behavior cases remain 24.

Given non-empty unique binary rows, when efficacy is computed, then recall,
precision, specificity, and paired discrimination expose 95% Wilson interval
bounds with the correct denominators.

### Regression safety

Given the existing repository test suite and CI environment, when the focused
tests and full CI gates run, then leakage rejection, trusted-fixture safety,
artifact verification, and existing provider metadata contracts remain green.

## Verification plan

1. Run the new focused tests and observe the detector test fail before the
   production fix.
2. Apply the minimal fixes and rerun the focused tests.
3. Run the full available test suite in the supported CI Python versions; note
   the local Python-version limitation if the workstation interpreter cannot
   import the project.
4. Run the offline v7 bundle with five repetitions.
5. Run artifact verification and the repository's eval/replay/wedge checks.
6. Inspect `run.json`, `metrics.json`, `verification/metrics.json`, a generated
   source file, and a comparison file for the expected metadata and newline
   behavior.
7. Record the remaining scientific limitations and the exact inputs needed for
   the later live-model run.

On macOS, `trusted_fixture` means the generated reference function is checked
against the hidden tests in the parent Python process with a restricted
builtins mapping; it is not a subprocess boundary and cannot claim containment
against hostile code. The subprocess evaluator may be used only when its
platform controls are available and must report its own execution mode.

## Expected result

The corrected offline detector should no longer miss the PEERING completeness
mutation solely because `all` appears inside `shall`. The ERTMS omission case
may remain difficult because the missing scope is absent from the final text;
that is a genuine generalization limitation, not a regex failure. The v7
bundle is a pipeline-quality and discovery result, not a confirmatory claim
about LLM efficacy.
