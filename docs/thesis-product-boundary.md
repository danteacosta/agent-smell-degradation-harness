# Thesis and Product Boundary

This repository contains two deliberately separate layers.

## Thesis protocol

The thesis layer is the confirmatory experiment. Its accepted claim is limited to the observable boundary of requirement-induced semantic degradation in LLM-based software-engineering agents. The primary task is acceptance-criteria generation; traceability is an independent validation task. Only ARP 2.0.5 lifecycle events through T0–T3 may enter deployable features. Oracle verdicts, terminal validators, final artifacts, requirement defect metadata, labels, and upper-bound metadata remain outside the primary model.

The scientific estimands are:

- `H1.ordinal_delta`: mean clean-minus-defective ordinal severity delta, clustered by source intent, with intent-cluster bootstrap 95% CI and paired sign-flip permutation p-value;
- `H2.pre_final_pr_auc`: held-out PR-AUC for pre-final labels, compared with deployable static and operational baselines; model selection uses train groups, calibration and threshold fitting use calibration groups, and test groups are untouched until evaluation.

Replications are repeated measures. Variants stay together. Project holdouts are required for claims of project generalization. A manifest that reaches 12×2×5 by duplicating source intents fails closed.

## Product protocol

The product layer is a CI reliability gate. It consumes ARP plus deployable/operational evidence and emits a deterministic policy result:

| Decision | Exit code | SARIF severity |
|---|---:|---|
| approve | 0 | note |
| warn | 10 | warning |
| block | 20 | error |
| invalid contract | 30 | error |

Policy precedence is `block > warn > approve`. Product metrics (latency, cost, coverage, false-alert rate) are operational diagnostics and are never written into H1–H3 artifacts. Product behavior must not alter thesis labels, estimands, or split manifests.

## Non-claims

The project does not claim that every requirement defect is detectable, that a product gate replaces tests or review, or that a local curated seed is representative of all software requirements. Results are valid only for the declared task, defect families, provider configuration, labels, and split protocol.
