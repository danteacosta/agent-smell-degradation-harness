# Thesis and Product Layers Design

## Goal

Close the validity gaps identified in the proposal while creating a product-facing reliability gate that consumes the same neutral protocol without changing the thesis estimands.

## Thesis layer

The agent-smell harness remains the scientific reference implementation. It will use the ARP lifecycle envelope end-to-end, keep feature and label planes independent, execute acceptance-criteria and traceability tasks, and export grouped splits and estimands that match the proposal. Deployable features, experimental metadata upper-bound features, and labels are separate schemas. The primary estimands are ordinal paired degradation with intent-clustered uncertainty and pre-final PR-AUC against deployable baselines; calibration, false-alert rate, warning coverage, lead time, and utility are secondary.

The dataset manifest will distinguish source intent, project, controlled defect family, natural variant, and replication. The harness will reject a pre-pilot manifest that reaches its count by duplicating source intents. Checkpoints T0-T3 are provider-produced lifecycle events; heuristic summaries are retained only as explicit experimental metadata.

## Product layer

The RAG harness becomes a reference product adapter rather than a thesis evidence source. It will consume the shared ARP models/events, expose a policy gate (`approve`, `warn`, `block`), and provide a stable JSON/SARIF-compatible report for CI. Product metrics such as latency, cost, coverage, and false-alert rate are operational diagnostics and are not used as H1-H3 evidence.

## Boundaries and failure modes

- No feature may read oracle values, final artifacts, terminal validation, or labels.
- Product policy must not change thesis labels or estimands.
- A missing/invalid shared event envelope is a hard contract error, not a warning.
- Incomplete dataset provenance blocks confirmatory analysis rather than silently imputing independence.

## Verification

Contract tests run against both consumers, protocol serialization round-trips, grouped-statistics tests cover the estimands, and each repository retains its own test suite plus a cross-repository fixture check.
