# Thesis and Product Boundary

This repository contains two deliberately separate layers.

## Thesis protocol

The thesis layer is the planned confirmatory experiment. Its conditional claim is limited to the observable boundary of material constraint-preservation failure induced by requirement defects in acceptance-criteria/test generation. The primary H2 label is human/adjudicated severity 2–3 versus 0–1; ordinal severity and executability, coverage, traceability, and verifiability are secondary. Traceability is an independent validation task. Only ARP 2.0.5 lifecycle events through T0–T3 may enter deployable features. Oracle verdicts, terminal validators, final artifacts, requirement defect metadata, labels, and upper-bound metadata remain outside the primary model. The current seven-source seed and all stub/oracle/pre-pilot outputs are non-confirmatory until the external data-acquisition gate passes.

The scientific estimands are:

- `H1.ordinal_delta`: mean clean-minus-defective ordinal severity delta, clustered by source intent, with intent-cluster bootstrap 95% CI and paired sign-flip permutation p-value;
- `H2.pre_final_pr_auc`: held-out PR-AUC for pre-final human labels, compared with deployable static and operational baselines; best-baseline selection uses train groups, threshold fitting uses calibration groups, and test groups are untouched until evaluation. The primary effect is provenance minus best baseline, with a frozen `ΔPR-AUC ≥ 0.05` margin and source-intent-cluster bootstrap CI.

Replications are repeated measures. Variants stay together. The 12×2×5 design is a structured pilot only. Confirmatory project generalization requires at least 24 independent intents across 6 projects, at least 4 intents per project, and at least 8 intents per split after project holdout. A manifest that reaches a count by duplicating source intents fails closed.

## Product protocol

The product layer is a CI reliability gate. It consumes ARP plus deployable/operational evidence and emits a deterministic policy result:

| Decision | Exit code | SARIF severity |
|---|---:|---|
| approve | 0 | note |
| warn | 10 | warning |
| block | 20 | error |
| invalid contract | 30 | error |

Policy precedence is `block > warn > approve`. Product metrics (latency, cost, coverage, false-alert rate) are operational diagnostics and are never written into H1–H3 artifacts. Product behavior must not alter thesis labels, estimands, or split manifests.

The strict pre-merge implementation is `python -m replay`: it accepts a
fixture or an arbitrary bundle containing a requirement and ARP pre-final
trace, then emits JSON/SARIF constraint evidence. This is distinct from the
legacy `python -m wedge` compatibility command, which retains its historical
`clarify` decision for local demos. The replay gate never reads
`expected.json`, terminal labels, final artifacts, or output-only diagnostics.

## Novelty boundary

The project does not claim a new requirements-smell taxonomy or a first demonstration that smells affect LLM tasks. Its contribution is the reproducible, leakage-resistant measurement of when provider-produced pre-final provenance adds warning value for constraint-preservation failures, including negative boundaries where failures remain silent.

## Non-claims

The project does not claim that every requirement defect is detectable, that a product gate replaces tests or review, or that a local curated seed is representative of all software requirements. Results are valid only for the declared task, defect families, provider configuration, labels, and split protocol.
