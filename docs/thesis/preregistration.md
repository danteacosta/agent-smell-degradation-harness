# Confirmatory Preregistration: Agent-Requirement Smell Degradation

Status: protocol freeze candidate, version `confirmatory-thesis-v1`.

## Hypotheses and estimands

- **H1 (`H1.ordinal_delta`)**: clean-minus-defective ordinal severity differs from zero. The estimand is the mean paired delta, clustered by source intent; the interval is an intent-cluster bootstrap 95% CI and the p-value is a paired sign-flip randomization test at the intent-cluster level.
- **H2 (`H2.pre_final_pr_auc`)**: pre-final provider-produced evidence detects terminal degradation on held-out source-intent/project groups. The primary protocol is one deterministic grouped train/calibration/test split: family selection is fit on train, calibration and threshold fitting use calibration, and final PR-AUC is computed once on untouched test groups. The primary effect is `ΔPR-AUC = PR-AUC(provenance) − PR-AUC(best deployable baseline)`, with a frozen practical margin of `ΔPR-AUC ≥ 0.05`. The confirmatory claim requires both the margin and a 95% cluster-bootstrap interval over held-out source-intent/project groups that excludes zero; repeated grouped folds are exploratory sensitivity analyses only. AUROC is secondary. Static and operational baselines are reported separately.

Replications are repeated measures, not independent sampling units. All variants of an intent remain in the same split.

## Confirmatory design

The design is exactly 12 independent source intents × 2 natural variants × 5 replications, spanning at least 3 projects. A dataset manifest records source URLs, project, defect family, canonical text hash, approved-paraphrase exceptions, and dataset hash. Duplicate or near-clone source intents fail closed.

The grouped split is deterministic and disjoint by source intent and project: train for model selection, calibration for threshold fitting, and test for the final estimate. No terminal artifact, oracle value, label, or post-cutoff event may enter deployable features.

## Exclusions and missingness

No post-hoc exclusions are permitted. Missing provider output, missing traceability, invalid ARP envelope, missing human label, or failed provenance hash is recorded as missing and blocks the affected confirmatory estimate. No imputation is used for the primary estimands.

## Labels and annotation

Primary labels are human/oracle adjudicated according to the versioned annotation rubric. Annotators are blinded to variant, defect family, model/provider, oracle result, and terminal artifact. A prespecified duplicate subset is double-coded. Krippendorff's alpha with bootstrap CI is primary IRR; alpha <0.60 triggers adjudication and claim narrowing, while ≥0.70 is the target.

Secondary LLM judges are exploratory only and cannot replace primary labels.

## Analysis freeze

The dataset manifest hash, code SHA, environment lock, split manifest, threshold version, and analysis version are exported before inspecting confirmatory outcomes. Pilot/stub runs are explicitly labelled and never pooled with real-provider confirmatory runs.
