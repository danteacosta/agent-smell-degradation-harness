# Thesis and Product Boundary

This repository contains two deliberately separate layers.

## Thesis protocol

The thesis layer is the planned confirmatory experiment. Its conditional claim is limited to the observable boundary of material constraint-preservation failure induced by requirement defects in acceptance-criteria/test generation. The primary H2 label is human/adjudicated severity 2–3 versus 0–1; ordinal severity and executability, coverage, traceability, and verifiability are secondary. Traceability is an independent validation task. Only native ARP 3.0 `agent-smell-degradation/v1` lifecycle events through T0–T3 may enter deployable features. Oracle verdicts, terminal validators, final artifacts, requirement defect metadata, labels, and upper-bound metadata remain in the T4 label plane and outside the primary model. The current seven-source seed and all stub, prompted-snapshot, replay, and oracle outputs are non-confirmatory until the external data-acquisition gate passes.

The scientific estimands are:

- `H1.ordinal_delta`: mean clean-minus-defective ordinal severity delta, clustered by source intent, with intent-cluster bootstrap 95% CI and paired sign-flip permutation p-value;
- `H2.pre_final_pr_auc`: held-out PR-AUC for pre-final human labels under fixed nested models: B0=static+operational and B1/B2/B3=B0 plus cumulative provenance through T1/T2/T3. There is no in-sample family selection. Threshold fitting uses calibration and test projects remain untouched. The primary effect is B3−B0, with a frozen `ΔPR-AUC ≥ 0.05` margin, project-cluster bootstrap CI, and leave-one-project-out stability report.

Replications are repeated measures and variants stay together. The 12×2×5 design is a structured pre-pilot; 24 intents/6 projects is only a pilot floor. Confirmatory project generalization requires a frozen outcome-blind precision plan, never fewer than 60 intents/12 projects or 6 test projects/24 test intents. The current conservative candidate is 220 intents/36 projects with a 50/20/30 project split; it is not a commitment because the weak-signal sensitivity scenario fails. A manifest that reaches a count by duplicating source intents fails closed.

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
