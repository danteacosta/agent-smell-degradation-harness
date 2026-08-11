# Thesis and Product Hardening Design

## Goal

Close the remaining implementation gaps without inflating the master's thesis:
make the replay policy executable, provide a real trace-export-to-ARP bundle
boundary, validate product utility inputs, improve reproducibility, and state a
defensible scientific scope.

## Scope boundary

The thesis primary contribution is a leakage-resistant protocol and benchmark
for measuring when requirement-induced constraint loss becomes observable before
the terminal artifact. The primary workload is acceptance-criteria/test
generation. H1 and H2 are planned confirmatory claims, conditional on the
external data, provider, label, and preregistration gates below. Traceability is
an external validation task; the product gate is a demonstrator and is not a
second thesis.

The implementation will not manufacture confirmatory data, human labels,
provider results, or customer ROI. Those remain explicit external acceptance
gates: at least 24 independent intents across 6 projects, real provider
checkpoints from at least two configurations, blinded human labels/adjudication,
and a shadow pilot with outcome measurements.

## Architecture

1. `replay.policy` owns the executable gate policy. A policy document is a JSON
   object with exactly `schema_version: "constraint-policy/v1"`, a non-empty
   string `version`, and `block_when`/`warn_when` arrays of unique non-empty rule
   IDs from a frozen allowlist. Empty arrays are allowed; unknown top-level keys,
   duplicate rules, unknown rules, and non-string entries fail closed. Facts are
   typed counters/booleans (`constraint_count`, `validation_check_count`,
   `coverage_target_count`, `unresolved_reference_count`,
   `contradiction_count`, `error_count`) and rule predicates are explicit
   (`count > 0` for positive-count rules, `count == 0` for missing rules).
   Precedence is block before warn before approve. The CLI/API accepts a policy
   document through `--policy PATH` or `run_bundle(..., policy=...)`. The runner
   records a SHA-256 over compact sorted-key UTF-8 JSON of the normalized policy
   (no newline) as `policy_hash`.
2. `replay.integrations` keeps vendor-neutral normalization diagnostic-only and
   separate from `build_replay_bundle`. The builder requires a requirement,
   case ID, and explicit ARP identity context (`experiment_id`, `run_id`,
   `episode_id`, `replication_id`). Each source export must contain exactly one
   supported interpretation/plan/tool checkpoint after filtering; duplicates,
   missing timestamps, non-chronological events, missing parents, terminal
   labels, mutation markers, or unsupported attributes fail closed. All raw
   export records are scanned before filtering, including unknown lifecycle
   records and their top-level/metadata fields; a terminal artifact/label or
   mutation marker in any record is rejected rather than silently dropped. The
   builder maps the three canonical source names to the frozen ARP 2.0.5 envelope and
   pre-final/v1 payload, computes raw JSONL bytes with one trailing newline for
   the trace hash, and returns a bundle accepted by the existing validator. It
   never accepts terminal labels or mutation metadata. The builder is a product
   replay adapter, not a confirmatory-provider collector: it accepts only the
   explicit product identity/timestamp context and marks the resulting bundle
   `non_confirmatory_adapter_demo`. Provider/model/config IDs, source event IDs,
   request/response hashes, and cutoff timestamps remain required in the
   thesis-specific provider manifest and are not fabricated by this adapter.
   RAG's broader lifecycle
   stream remains a separate product adapter; it is not directly replayable by
   ASD's three-checkpoint gate.
3. The deployable bundle schema uses strict allowlists for manifest,
   requirement, and event fields. Terminal/mutation keys in requirement or
   manifest fail closed; audit metadata is allowed only in a separated
   non-deployable sidecar. Partial vendor normalization is diagnostic only:
   `build_replay_bundle` rejects missing fields and never fabricates T1/T2/T3
   defaults.
4. `replay.utility` validates `RunOutcome` at construction/aggregation time so
   ROI summaries cannot contain impossible decisions, negative durations/costs,
   non-finite values, or non-boolean flags.
4. Reproducibility docs and the Makefile use the active Python interpreter.
   The lock/constraints file remains the source of truth, but because the ARP
   dependency is a direct VCS reference, a clean machine must first acquire and
   cache/build that dependency. The docs will not claim that `pip --no-index`
   alone can bootstrap ARP from an empty wheelhouse; the offline command is
   explicitly post-acquisition execution.
5. Thesis docs add a concise master's-scope and contribution statement and
   cross-link the confirmatory data gate, so descriptive oracle/stub analysis
   cannot be mistaken for evidence.

## Error handling and invariants

- Unknown or malformed policy facts fail closed with exit code 30.
- A policy rule change with the same version is allowed only as an explicit
  custom policy and must be observable in both decision behavior and policy
  hash; the default policy remains immutable.
- A normalized vendor export without explicit product identity/requirement
  context is rejected by the bundle builder; normalization alone is diagnostic
  only. Missing thesis-specific provider provenance does not make a product
  bundle pretending to be confirmatory; it remains explicitly non-confirmatory.
- Builder JSONL bytes are deterministic: each event is normalized with
  sorted keys, compact separators, UTF-8, and no embedded newline; events are
  joined in T1/T2/T3 order with exactly one final `\n`, and those exact bytes are
  returned as `_trace_raw` and hashed into `manifest.trace_sha256`.
- Every built bundle must pass ARP lifecycle validation, preserve exactly three
  ordered checkpoints, and have no terminal keys in deployable attributes.
- Utility summaries reject invalid records before computing any aggregate:
  decisions are `approve|warn|block`, flags are actual booleans (not integer
  coercions), all numeric values are finite and non-negative (excluding bool),
  and `failure_time_ms` is either `None` or finite/non-negative; a failure time
  is only meaningful for a true regression and a captured alert.
- Tests use synthetic fixtures only and label all resulting metrics
  non-confirmatory.
- Builder tests distinguish partial normalization (diagnostic data) from strict
  bundle construction (exactly one complete T1/T2/T3 set), scan unknown raw
  records before filtering, and reject terminal/mutation keys in raw spans,
  requirement, and manifest.
- Product policy is excluded from confirmatory feature manifests, labels,
  splits, and H1/H2 analysis outputs; policy changes cannot affect the thesis
  plane.

## Acceptance tests

- Given a custom policy that blocks on unresolved references, a warning fixture
  becomes `block`, and the report includes the custom version and `policy_hash`.
- Given an unknown policy rule, a malformed policy document, or a non-finite
  feature fact, the CLI emits a machine-readable invalid-contract report and
  exits 30.
- Given valid Phoenix, Langfuse, and Braintrust-shaped exports plus explicit
  context, the builder produces a bundle that replays to the expected decision.
- Given a partial export, duplicate checkpoint, or missing product identity/
  requirement context, normalization may remain diagnostic but bundle
  construction fails closed; missing thesis-specific provider provenance keeps
  an otherwise valid product bundle explicitly non-confirmatory and cannot emit
  a thesis claim.
- Given missing context, terminal fields, malformed timestamps, or unsupported
  checkpoint payloads, the builder fails closed.
- Given invalid `RunOutcome` values, construction or summarization raises a
  clear validation error.
- Given the documented quickstart with `PYTHON=.venv/bin/python`, ASD's
  `test`, `eval`, `simulate`, and `gate` targets run without relying on a
  globally installed `pytest` executable. RAG's existing `PYTHON` wrapper is
  preserved and tested separately.
- The thesis documentation states the planned H1/H2 estimands, the master's
  scope, the conditional novelty claim, and the external evidence still
  required. A documentation test links the confirmatory data-acquisition gate
  and asserts that pre-pilot/stub/oracle outputs remain non-confirmatory.

## Non-goals

- No vendor SDK installation or credentials.
- No automatic customer claims or fabricated ROI.
- No new requirements-smell taxonomy.
- No merge/push to canonical `main` before review and fresh verification.
