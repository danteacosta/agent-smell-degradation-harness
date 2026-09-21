# Research quality corrections

## Scope and design

Audit the three linked research repositories: agent-smell-degradation-harness,
agent-reliability-protocol, and rag-reliability-harness. Preserve dirty checkouts
and immutable evidence. Each repository gets its own reviewed, CI-gated PR.

The harness has seven independently implemented average-precision paths. Tied
scores currently depend on label/order (some sort labels first), inflating or
changing results. Use one dependency-free protocol metric with score-threshold
aggregation. Keep existing import surfaces and the power simulation's explicit
no-positive error. This isolates a shared mathematical contract without a class
or strategy abstraction. Validation rejects mismatched lengths, non-finite
scores, and non-binary labels. Empty/no-positive AP remains 0 for compatibility.

`make analysis` is an offline synthetic demonstration. Add explicit scope and
claim eligibility to its JSON and documentation; retain legacy keys for readers,
with a warning that their H1/H2 names are not confirmatory estimands.

IRR corrections are independently investigated against primary methodological
sources. No historical artifacts are rewritten or human labels manufactured.

## Acceptance / BDD

- Given identical scores and mixed labels, AP equals positive prevalence,
  regardless of row order; all seven paths agree on threshold handling.
- Given tied and untied thresholds, AP equals the sum of recall increments
  times threshold precision; perfect/reversed rankings retain known values.
- Given malformed metric inputs, computation raises an actionable ValueError
  rather than silently truncating or sorting non-finite values.
- Given a synthetic analysis run, its serialized report declares synthetic,
  non-confirmatory scope, even when injected failures are detected.
- Given insufficient IRR evidence, no acceptable reliability claim is emitted.

## Execution and verification

- [x] Map repositories and inspect current sources / consumer contracts.
- [x] Add failing metric and public report regressions.
- [x] Implement common metric and route existing consumers to it.
- [x] Correct IRR with independent known-value regressions.
- [x] Update operator-facing guidance and historical-result impact notes.
- [x] Run focused tests, local suite, compile/build and diff checks; Linux CI pending.
- [x] Independently review correctness, scientific claims, SOLID/clean code.
- [ ] Open PRs and merge only reviewed exact heads after CI succeeds.

Reference: scikit-learn average_precision_score official documentation,
https://scikit-learn.org/1.5/modules/generated/sklearn.metrics.average_precision_score.html
(accessed 2026-09-21): AP sums precision weighted by recall increments at distinct
score thresholds. This is non-interpolated AP, not trapezoidal PR area.

## Verification record

Local stable environment: 1,608 passed, 12 skipped, four Linux resource-limit
checks deselected, nine subtests passed. The four checks fail in child resource
setup on this macOS host and remain enabled in Linux CI. Wheel/sdist and
compileall succeeded. The initial local runs exposed a missing subprocess
package installation and build-generated duplicate distribution metadata;
installing the exact pinned ARP package and removing generated egg-info restored
a consistent parent/child environment. No production check was weakened.

Keep source files and installed distributions unchanged during custody-sensitive
suite execution. Build before the final suite, remove generated metadata from the
source checkout, then freeze the environment until verification completes.

Independent review corrected one additional AP consumer and checked IRR against
1,000 exact-rational coincidence-matrix comparisons. Published-example oracles
and boundary tests passed. No historical metric or raw evidence was rewritten.
