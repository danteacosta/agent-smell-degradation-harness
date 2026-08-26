# Verification efficacy report

This is a discovery-only, oracle-separated benchmark.
The verifier reads only `decisions.jsonl` inputs derived from pre-final observations;
`labels.jsonl` is written after decisions and contains the independent behavior labels.
Only `behavior_codegen` decisions with a terminal behavior label enter the binary efficacy matrix;
`test_gen` decisions are observability-only and are not efficacy cases.

- Status: `descriptive_only`
- Raw eligible behavior rows: `120`
- Unique eligible behavior cases: `24`
- Recall/warning coverage: `0.9166666666666666`
- Clean false-alert rate: `0.0`
- Paired discrimination: `0.9166666666666666`
- Confidence interval method: `wilson` at `0.95`
- Interval unit: `unique_behavior_case_or_pair`
- Interval support status: `inconclusive`
- Repeated observations agree: `True`
- Mean lead time before artifact completion (ms): `0.07733333333333334`

Five offline repetitions of the deterministic stub are pipeline-stability checks,
not independent model samples; their duplicate rows are deduplicated for primary metrics.
On macOS, `trusted_fixture` executes checked-in reference functions in the parent process
with restricted builtins. It is not production subprocess isolation against hostile code.

The thresholds are frozen in the run output. `descriptive_only` means that this
versioned offline pilot produced a complete, auditable controlled result. Its
point estimates are development diagnostics; they are not a population-level
claim or evidence that the detector generalizes to new requirements.
