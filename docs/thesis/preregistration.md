# Confirmatory Preregistration: Agent-Requirement Smell Degradation

Status: protocol freeze candidate, version `confirmatory-thesis-v3`.

The current checked-in manifest remains blocked: it is a seven-source local
development seed with no project IDs or external provenance. The 12×2×5
configuration is a structured pre-pilot; the confirmatory claim requires the
larger design and collection criteria in
docs/research/confirmatory-data-acquisition.md.

## Hypotheses and estimands

- **H1 (`H1.ordinal_delta`)**: clean-minus-defective ordinal severity differs from zero. The estimand is the mean paired delta, clustered by source intent; the interval is an intent-cluster bootstrap 95% CI and the p-value is a paired sign-flip randomization test at the intent-cluster level.
- **H2 (`H2.pre_final_pr_auc`)**: pre-final runtime-observed evidence detects material constraint-preservation failure on held-out source-intent/project groups. The primary binary label is human/adjudicated severity 2–3 versus severity 0–1; ordinal severity is secondary. The fixed nested models use the same ranker and preprocessing: `B0 = static + operational`, `B1 = B0 + provenance through T1`, `B2 = B0 + provenance through T2`, and `B3 = B0 + provenance through T3`. No model or family is selected from in-sample performance. The primary effect is `ΔPR-AUC = PR-AUC(B3) − PR-AUC(B0)`, with a frozen practical margin of `ΔPR-AUC ≥ 0.05`; B1 and B2 form the planned temporal-boundary analysis. Calibration and threshold fitting use calibration only, and final PR-AUC is computed once on untouched test projects. The interval is a project-cluster bootstrap with 2,000 draws and a frozen seed; degenerate resamples and leave-one-project-out stability are reported. The claim requires both the margin and a 95% interval excluding zero. Repeated grouped folds, alternative estimators, and isolated feature-family results are exploratory.

Replications are repeated measures, not independent sampling units. All variants of an intent remain in the same split.

## Confirmatory design

The structured pre-pilot design is exactly 12 independent source intents × 2 variants × 5 replications. A 24-intent/6-project corpus is a pilot floor, not a confirmatory sample-size justification. Confirmatory execution requires a frozen `h2-precision-plan/v2` produced before confirmatory outcomes are inspected, at least 60 independent intents, at least 12 projects, at least 4 intents per project, at least 2 projects in train/calibration, and at least 6 projects/24 intents in the untouched test partition. The corrected conservative candidate is 220 intents across 36 projects with a 50/20/30 project split; it passes candidate thresholds under a moderate simulated provenance increment of 0.50 but fails the power target under the weaker 0.35 scenario. It therefore remains unfrozen. The final design must be chosen from an outcome-blind grid updated with pre-pilot prevalence/variance estimates and frozen before confirmatory collection. A dataset manifest records source URLs, project, defect family, canonical text hash, approved-paraphrase exceptions, and dataset hash. Duplicate or near-clone source intents fail closed.

The grouped split is deterministic and disjoint by source intent and project: train for model selection, calibration for threshold fitting, and test for the final estimate. No terminal artifact, oracle value, label, or post-cutoff event may enter deployable features.

The checkpoint boundary analysis reports B1, B2, and B3 on the untouched test
rows. It is a planned cumulative boundary map, not three opportunities to
select the most favorable result; H2 remains the frozen B3-versus-B0 contrast.

Each episode may emit a versioned `episode_handoff/v1` JSON sidecar and semantic-lint report. These are auditability and quality-control artifacts only. The staged provider runtime now emits T1 and T2 as bounded external provider responses, invokes a deterministic T1→T2 semantic-plan coverage validator for T3, and requests the terminal artifact only afterward, all within one episode. T3 reports schema/contract errors, uncovered interpreted constraints, and unacknowledged unresolved references, assumptions, or contradictions without reading T4, an oracle, or a label. `runtime_native` means emitted by the instrumented runtime while the episode is active; it does not mean chain-of-thought, hidden activations, or retrospective prompting. Provider/model/version/configuration identifiers, stage request/response hashes, source event IDs, and monotonic timestamps preceding T4 are mandatory. The implementation is protocol-eligible but not empirically qualified until two real provider/model configurations pass the runtime qualification suite. `LiveAgent.observe_checkpoints()` remains `prompted_snapshot` and is ineligible. A `pre_final` handoff is fail-closed to T0–T3 facts; a `post_eval` handoff may contain labels and outcomes only in the label plane.

## Exclusions and missingness

No post-hoc exclusions are permitted. Missing provider output, missing traceability, invalid ARP envelope, missing human label, or failed provenance hash is recorded as missing and blocks the affected confirmatory estimate. No imputation is used for the primary estimands.

## Labels and annotation

Primary labels are human/adjudicated according to the versioned annotation rubric; executable oracle results are independent validation evidence, not the H2 label source. Annotators are blinded to variant, defect family, model/provider, oracle result, terminal artifact, pre-final features, and detector predictions. Exactly 20% of episodes are double-coded. Krippendorff's alpha with 2,000-draw bootstrap CI is primary IRR; alpha <0.60 triggers adjudication and claim narrowing, while ≥0.70 is the target. Missing labels are never imputed.

Secondary LLM judges are exploratory only and cannot replace primary labels.

## Analysis freeze

The preregistration, precision plan, runtime producer, ARP compatibility matrix, feature schema, annotation rubric, split algorithm, and analysis code are frozen in a hash manifest before any provider run. The checked-in manifest is intentionally `candidate`; a confirmatory provider run is refused unless it is marked `confirmed` and every hash matches. Pilot/stub runs are explicitly labelled and never pooled with real-provider confirmatory runs.

## Related-work positioning and novelty boundary

Requirements smells, smell taxonomies, and their effects on LLM-supported software engineering are established research areas. Prior work has already measured requirements-smell effects on automated traceability with multiple models and projects, reporting mixed task-dependent outcomes. This thesis therefore does not claim novelty from detecting smells or merely showing that prompt wording can matter.

The contribution is narrower: a leakage-resistant paired protocol for measuring the incremental value of provider-produced pre-final provenance for constraint-preservation failures, with independent labels, project holdout, calibration, cluster uncertainty, and an explicit boundary between detectable and silent degradation. Recent prefix-monitor work is treated as a direct comparator and motivates reporting operational utility in addition to ranking metrics.

References: [On the Impact of Requirements Smells in Prompts](https://arxiv.org/abs/2501.04810), [Characterizing Requirements Smells](https://arxiv.org/abs/2404.11106), [ClarifyGPT](https://doi.org/10.1145/3660810), and [PrefixGuard](https://arxiv.org/abs/2605.06455).
