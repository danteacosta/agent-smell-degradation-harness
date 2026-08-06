# Confirmatory Preregistration: Agent-Requirement Smell Degradation

Status: protocol freeze candidate, version `confirmatory-thesis-v2`.

## Hypotheses and estimands

- **H1 (`H1.ordinal_delta`)**: clean-minus-defective ordinal severity differs from zero. The estimand is the mean paired delta, clustered by source intent; the interval is an intent-cluster bootstrap 95% CI and the p-value is a paired sign-flip randomization test at the intent-cluster level.
- **H2 (`H2.pre_final_pr_auc`)**: pre-final provider-produced evidence detects material constraint-preservation failure on held-out source-intent/project groups. The primary binary label is human/adjudicated severity 2–3 versus severity 0–1; ordinal severity is secondary. The primary protocol is one deterministic grouped train/calibration/test split: family selection and best-baseline selection are fit on train, calibration and threshold fitting use calibration, and final PR-AUC is computed once on untouched test groups. The primary effect is `ΔPR-AUC = PR-AUC(provenance) − PR-AUC(best deployable baseline)`, with a frozen practical margin of `ΔPR-AUC ≥ 0.05`. The interval is a source-intent-cluster bootstrap with 2,000 draws, seed frozen in the run manifest, and degenerate resamples retained/reported. The confirmatory claim requires both the margin and a 95% interval excluding zero; repeated grouped folds are exploratory sensitivity analyses only. AUROC is secondary. Static and operational baselines are reported separately.

Replications are repeated measures, not independent sampling units. All variants of an intent remain in the same split.

## Confirmatory design

The structured pre-pilot design is exactly 12 independent source intents × 2 variants × 5 replications, spanning at least 3 projects. It is not confirmatory. The minimum confirmatory design is 24 independent source intents across at least 6 projects, with at least 4 intents per project and at least 8 intents in each train/calibration/test partition after project holdout. A frozen precision simulation may increase these minima but may not reduce them. A dataset manifest records source URLs, project, defect family, canonical text hash, approved-paraphrase exceptions, and dataset hash. Duplicate or near-clone source intents fail closed.

The grouped split is deterministic and disjoint by source intent and project: train for model selection, calibration for threshold fitting, and test for the final estimate. No terminal artifact, oracle value, label, or post-cutoff event may enter deployable features.

Each episode may emit a versioned `episode_handoff/v1` JSON sidecar and semantic-lint report. These are auditability and quality-control artifacts only: they are not generation inputs, deployable H2 features, labels, or analysis outcomes. A confirmatory provider must emit genuine provider-produced T1 interpretation, T2 plan, and T3 execution summaries with provider/model/version/configuration identifiers, request/response hashes, source event IDs, and timestamps preceding T4. A `pre_final` handoff is fail-closed to those T0–T3 facts and source references bound to the pre-final event sequence; a `post_eval` handoff may contain labels and outcomes but is label-plane data. Strict lint failure marks the episode invalid before confirmatory analysis; it does not trigger post-hoc exclusion or alter the estimand.

## Exclusions and missingness

No post-hoc exclusions are permitted. Missing provider output, missing traceability, invalid ARP envelope, missing human label, or failed provenance hash is recorded as missing and blocks the affected confirmatory estimate. No imputation is used for the primary estimands.

## Labels and annotation

Primary labels are human/adjudicated according to the versioned annotation rubric; executable oracle results are independent validation evidence, not the H2 label source. Annotators are blinded to variant, defect family, model/provider, oracle result, terminal artifact, pre-final features, and detector predictions. Exactly 20% of episodes are double-coded. Krippendorff's alpha with 2,000-draw bootstrap CI is primary IRR; alpha <0.60 triggers adjudication and claim narrowing, while ≥0.70 is the target. Missing labels are never imputed.

Secondary LLM judges are exploratory only and cannot replace primary labels.

## Analysis freeze

The preregistration, ARP compatibility matrix, feature schema, annotation rubric, split algorithm, and analysis code are frozen in a hash manifest before any provider run. A confirmatory provider run is refused unless the manifest is marked `confirmed` and all hashes match. The dataset manifest hash, code SHA, environment lock, split manifest, threshold version, feature manifest, and analysis version are exported before inspecting confirmatory outcomes. Pilot/stub runs are explicitly labelled and never pooled with real-provider confirmatory runs.

## Related-work positioning and novelty boundary

Requirements smells, smell taxonomies, and their effects on LLM-supported software engineering are established research areas. Prior work has already measured requirements-smell effects on automated traceability with multiple models and projects, reporting mixed task-dependent outcomes. This thesis therefore does not claim novelty from detecting smells or merely showing that prompt wording can matter.

The contribution is narrower: a leakage-resistant paired protocol for measuring the incremental value of provider-produced pre-final provenance for constraint-preservation failures, with independent labels, project holdout, calibration, cluster uncertainty, and an explicit boundary between detectable and silent degradation. Recent prefix-monitor work is treated as a direct comparator and motivates reporting operational utility in addition to ranking metrics.

References: [On the Impact of Requirements Smells in Prompts](https://arxiv.org/abs/2501.04810), [Characterizing Requirements Smells](https://arxiv.org/abs/2404.11106), [ClarifyGPT](https://doi.org/10.1145/3660810), and [PrefixGuard](https://arxiv.org/abs/2605.06455).
