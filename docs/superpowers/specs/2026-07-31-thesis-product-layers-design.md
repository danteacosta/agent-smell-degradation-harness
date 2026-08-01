# Thesis and Product Layers Design

## Goal

Close the validity gaps identified in the proposal while creating a product-facing reliability gate that consumes the same neutral protocol without changing the thesis estimands.

## Thesis layer

The agent-smell harness remains the scientific reference implementation. Its actual thesis run emits the canonical ARP `2.0.5` `RunManifest` and ordered T0–T3 events; `protocol_next` is fixture-only and guarded against runtime imports. It will keep feature and label planes independent, execute acceptance-criteria and traceability tasks, and export grouped splits and estimands that match the proposal. Deployable features, experimental metadata upper-bound features, and labels are separate schemas with an allowlist and temporal cutoff. The primary estimand is the mean paired ordinal delta (clean severity minus defective severity), clustered by intent with project as a higher-level descriptive stratum; its 95% CI is an intent-cluster bootstrap and its paired randomization p-value flips signs within intent. H2 primary is held-out PR-AUC of pre-final labels, with model selection on train groups, calibration/threshold fitting on calibration groups, and evaluation only on test groups. Replications are repeated measures, never independent sample units.

The dataset manifest will distinguish source intent, project, controlled defect family, natural variant, and replication. It will validate unique source/project/defect/variant/replication keys before counts, reject near-clones using canonicalized Unicode/whitespace/token hashing plus a declared similarity threshold, record an explicit exception for approved paraphrases, require project holdouts, enforce the 12×2×5 design, and fail closed when counts or provenance are incomplete. Checkpoints T0-T3 are provider-produced lifecycle events; heuristic summaries are retained only as explicit experimental metadata. Traceability labels resolve claim spans to hashed target artifact spans and reject missing, stale, tampered, or self-reported links. Human annotation uses blinded annotator IDs hiding variant, defect family, oracle, model, and terminal artifacts; a prespecified duplicate subset is double-coded after rubric training; Krippendorff’s alpha with bootstrap CI is primary, target ≥0.70, <0.60 triggers adjudication and claim narrowing. Raw labels, disagreement, missing-label handling, and adjudication provenance are exported; secondary LLM judges can never replace the primary label.

## Product layer

The RAG harness becomes a reference product adapter rather than a thesis evidence source. It will consume the shared ARP models/events, expose a deterministic versioned policy gate (`approve`, `warn`, `block`) with precedence `block > warn > approve`, exit codes 0/10/20, hard-contract error 30, stable reason/evidence IDs, and SARIF severities note/warning/error respectively. Product decisions are namespaced separately from neutral ARP pass/fail. Invalid protocol envelopes hard-fail. Product metrics such as latency, cost, coverage, and false-alert rate are operational diagnostics and are structurally excluded from H1-H3 artifacts.

## Boundaries and failure modes

- No feature may read oracle values, final artifacts, terminal validation, or labels.
- Deployable extraction uses an explicit allowlist and rejects nested or serialized terminal fields.
- A static import guard forbids `feature_plane` from importing label/oracle modules; upper-bound features are rejected by model-selection/training APIs.
- All variants and replications for an intent remain in one split; train/calibration/test source-intent and project groups are disjoint.
- Product policy must not change thesis labels or estimands.
- Thesis code never imports RAG policy/report modules; product decisions consume only ARP plus deployable/operational evidence.
- A missing/invalid shared event envelope is a hard contract error, not a warning.
- Incomplete dataset provenance blocks confirmatory analysis rather than silently imputing independence.

## Verification

Contract tests run against both consumers, protocol serialization round-trips, lifecycle ordering and schema-negotiation failures, grouped-statistics tests cover the estimands, split-manifest tests prove no overlap, and each repository retains its own test suite plus a cross-repository fixture check. Product isolation tests prove product metrics cannot enter thesis artifacts.
