# Prospective temporal-warning analysis

Status: executable analyzer and prospective measurement specification; no
empirical early-warning benefit has yet been measured. This document is dated
by its Git commit and must be frozen before new confirmatory outcomes are seen.
Existing exploratory outcomes have already been inspected; any analysis of
them under this specification is retrospective and exploratory.

Compare three cumulative observation windows: T1, T1+T2, T1+T2+T3. Preserve B0
and B3 as defined by the thesis. These windows are extra ablations, not a
redefinition of B1 or B2. Use identical project splits, preprocessing, model
family, tuning budget and threshold-selection policy across windows. Fit on
training projects, choose thresholds on calibration projects only, and evaluate
the held-out projects once. Compare paired episode outputs, clustering
uncertainty by project; do not count replications as independent requirements.

Freeze an alert policy ID, its code/configuration hash and stage-specific
feature allowlists before collection. For an initial deterministic lineage
diagnostic, alert on a missing required, hash-bound obligation link observed at
the current stage. Absence of a checkpoint is missing data, not a semantic
omission. T2 adds planned coverage and T3 adds executed checks/lineage. To claim
provenance adds value beyond more information, also compare a content-only
version with the same stage content and budget but lineage fields removed.
Do not use terminal results to construct any alert or tune the threshold.

`python -m eval.temporal_diagnostics --episodes PRIVATE.jsonl --output PRIVATE-report.json`
consumes one row per episode with:

- episode_id and intent_id for identity and clustering;
- terminal_ms, measured from the same monotonic origin as stage timestamps;
- terminal_defect: true, false or null, joined only after all alerts are frozen;
- stages: stage (T1/T2/T3), available_ms, alert (boolean), and incremental
  cost_microusd (integer or null). Missing stages are omitted, not fabricated.

Keep an accompanying manifest with source hashes, alert policy hash, stage
allowlists and outcome provenance (construction oracle, machine label or blinded
human label). The analyzer computes no alerts itself and cannot certify the
provenance of caller-supplied observations. It rejects duplicate episodes,
duplicate stages, nonmonotonic times and any observation at or after T4.

Report per window:

- planned, complete and missing-stage episode counts;
- alerts and outcome-labeled denominators;
- false alerts divided by independently nondefective labeled episodes, and
  the same rate per 100 eligible episodes;
- first observed alert stage, warning coverage and lead time to T4;
- cumulative observation cost, available-cost subtotal and missing-cost count;
- schema/transport failures, abstentions and missing checkpoints separately.

The first observed alert is not proven to be the earliest possible alert when
an earlier checkpoint is missing. A null lead time means no observed alert;
zero cost is valid only when measured (for example a local deterministic T3).
Report latency and instrumentation overhead separately from total generation
cost; extra delay caused by instrumentation needs an uninstrumented matched
comparison. Unlabeled episodes cannot supply false-alert or detection rates.

## Missing-stage sensitivity, not calibrated uncertainty

`temporal-diagnostics/v2` preserves the original complete-stage `false_alert_rate`
and labels its scope explicitly. In addition, `missing_stage_bounds` keeps every
supplied terminal-labeled episode, including those with missing checkpoints.
For each outcome group, let N be the supplied-label count, A the episodes with
an observed alert in the window, and U the incomplete episodes with no observed
alert. The possible alert-rate range is [A/N, (A+U)/N]. An observed alert makes
the OR policy true even if another checkpoint is missing. With N=0 the bounds
are null. Unknown terminal labels are counted separately and never imputed.

For nondefective labels this is a missing-stage false-alert range; for defective
labels it is a detection range. These are deterministic completion bounds, NOT
confidence intervals, conformal prediction intervals, population estimates or
proof that machine labels are correct. They cover only supplied rows: missing
entire episodes must still be reconciled against the frozen execution manifest.
Changing the alert policy requires a new derivation. No project-level inference
is performed here, and no new model training or H2 feature is introduced.

Example: one completely observed, nondefective no-alert episode and one
nondefective episode missing T2/T3 produce a complete-case false-alert rate of
0, but a possible rate from 0 to 0.5. Showing only the former conceals a real
observability limitation. This is an arithmetic fixture, not an empirical result.

The known-cost subtotal now retains every measured stage cost, even in partially
observed episodes or beside an unknown cost. The total remains null whenever a
required stage or cost is unknown. `missing_cost_episodes` counts episodes with
an observed stage whose cost is null; absent stages are counted separately.
`first_alert_prefix_complete` distinguishes a fully observed prefix from an
alert whose earlier checkpoints are missing; null means no observed alert.
V1 reports remain historical and must not be silently rewritten as v2.

[Sheng et al., EMNLP 2025](https://doi.org/10.18653/v1/2025.emnlp-main.569)
study calibrated judge intervals, which require reference labels and
exchangeability. We therefore defer conformal claims until an appropriate
independent calibration set exists. Our completion bounds are separate local
bookkeeping, not an implementation or replication of their method.

Historical empirical limitation: the original 72-call control run found poor deletion
sensitivity. Historical machine-clean labels cannot supply a trustworthy
false-alert denominator. Collection of new temporal/lineage observations and
valid terminal outcomes remains necessary before claiming early-warning value.
