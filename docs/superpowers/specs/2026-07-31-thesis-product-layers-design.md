# Thesis and Product Layers Design

## Goal

Close the validity gaps identified in the proposal while creating a product-facing reliability gate that consumes the same neutral protocol without changing the thesis estimands.

## Thesis layer

The agent-smell harness remains the scientific reference implementation. It will use the ARP 2.0.5 lifecycle envelope end-to-end, keep feature and label planes independent, execute acceptance-criteria and traceability tasks, and export grouped splits and estimands that match the proposal. Deployable features, experimental metadata upper-bound features, and labels are separate schemas with an allowlist and temporal cutoff. The primary estimands are ordinal paired degradation with intent-clustered uncertainty and pre-final PR-AUC against deployable baselines; calibration, false-alert rate, warning coverage, lead time, and utility are secondary. Replications are repeated measures, never independent sample units.

The dataset manifest will distinguish source intent, project, controlled defect family, natural variant, and replication. It will validate unique source/project/defect/variant/replication keys, reject near-cloned source artifacts, require project holdouts, enforce the 12×2×5 design, and fail closed when counts or provenance are incomplete. Checkpoints T0-T3 are provider-produced lifecycle events; heuristic summaries are retained only as explicit experimental metadata. Traceability labels resolve claim spans to hashed target artifact spans and reject missing, stale, tampered, or self-reported links. Human annotation exports raw blinded labels, duplicate-sample IRR, confidence intervals, disagreement policy, and adjudication provenance; secondary LLM judges can never replace the primary label.

## Product layer

The RAG harness becomes a reference product adapter rather than a thesis evidence source. It will consume the shared ARP models/events, expose a deterministic versioned policy gate (`approve`, `warn`, `block`) with documented exit codes, stable reason/evidence IDs, and provide a stable JSON/SARIF-compatible report for CI. Invalid protocol envelopes hard-fail. Product metrics such as latency, cost, coverage, and false-alert rate are operational diagnostics and are structurally excluded from H1-H3 artifacts.

## Boundaries and failure modes

- No feature may read oracle values, final artifacts, terminal validation, or labels.
- Deployable extraction uses an explicit allowlist and rejects nested or serialized terminal fields.
- All variants and replications for an intent remain in one split; train/calibration/test source-intent and project groups are disjoint.
- Product policy must not change thesis labels or estimands.
- Thesis code never imports RAG policy/report modules; product decisions consume only ARP plus deployable/operational evidence.
- A missing/invalid shared event envelope is a hard contract error, not a warning.
- Incomplete dataset provenance blocks confirmatory analysis rather than silently imputing independence.

## Verification

Contract tests run against both consumers, protocol serialization round-trips, lifecycle ordering and schema-negotiation failures, grouped-statistics tests cover the estimands, split-manifest tests prove no overlap, and each repository retains its own test suite plus a cross-repository fixture check. Product isolation tests prove product metrics cannot enter thesis artifacts.
