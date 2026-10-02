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

Optional comparator (not a redefinition of B0): a semantics-free, structure-only
trace monitor (for example a finite-state or directly-follows model over tool/step
activity, as in [arXiv 2608.23670](https://arxiv.org/abs/2608.23670), a preprint)
may be run as an extra operational ablation with the same project-level split,
calibration-only thresholds and stage allowlists. It is fitted on training projects
only; the cited work splits by trace, which risks shared-project regularities
here. Whether it is preregistered is a human decision; see
`literature-matrix.md` (2026-10-02).

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


## Prefix access contract and supplementary comparator (2026-10-02)

The primary fixed B0/B3 model definitions and existing F1 threshold policy remain
unchanged. The following structural comparator and recall-at-FPR operating point
are supplementary candidates pending a prospective freeze, not new primary claims.
Full-trace classification (Automata's SWE-agent AUROC 0.799), prefix ranking
(rank-AUROC 0.66 near 25%) and simulated stopping are different evaluations.
CodeTracer's backward localization is post-outcome; its diagnosis inputs are not
admissible early-warning inputs. Diagnosis costs must be included in total cost.

| Detector | T0 input | Available T1–T3 prefix | Never accessible |
| --- | --- | --- | --- |
| B0 | Submitted requirement and frozen static features | Operational features available by the same cutoff | Provenance family, T4, oracle outputs, terminal labels, clean counterpart, removed-clause identity |
| B3 | Same submitted requirement/static input | B0 plus cumulative constraint provenance through the current stage; primary B3 uses T1–T3 | T4, oracle outputs, terminal labels, clean counterpart, removed-clause identity |
| S-structure (supplementary) | No requirement text | Registered activity types, order and monotonic availability timestamps; derived counts/transitions/repetition | Text/diffs, semantic payloads, constraint IDs, labels, total/future trace length, T4 |
| Content-only (supplementary) | Same static input | Same permitted stage content and budget as the provenance comparison with lineage links removed | Terminal information and privileged counterpart/label data |

No detector receives the arm name, project ID, run ID or replication ID as a
predictor. IDs join records and define splits only. A missing checkpoint is an
abstention/missing observation, not a missing requirement condition. Online
cutoffs use absolute elapsed time and stage completion, never a percentage of
future total trace length. Fit preprocessing, activity vocabulary and structural
models on training projects only. Choose thresholds on calibration only. Freeze
alerts, feature hashes and cutoff receipts before the label-plane join.

`eval.temporal_comparator.structural_features` is a bounded supplementary adapter
for already isolated prefix events. It admits only stage/time/registered activity;
rejects extra fields, future stages, future times and free-text activities; and
preserves ordered transition counts. It is not an implementation of the paper's
FSM and does not replace the hash-bound feature extractor. Before a real run,
qualify the runtime event-normalization mapping and bind its code/config hashes.
The staged runtime's small activity alphabet may offer little signal: this is a
measured limitation to report, not a reason to add semantic text to S-structure.

`fit_fpr_threshold` supplies a supplementary calibration-only operating point:
maximize recall under a prospectively specified empirical FPR budget. Equal recall
prefers the larger threshold; no useful feasible threshold returns null (abstain).
The candidate budget is 0.05, pending approval; it is not a guaranteed test FPR.
Report calibration negative counts and attained FPR/recall on test. Do not silently
replace the frozen primary F1 policy or select the budget after seeing outcomes.

## Next temporal cohort: candidate preparation and gates

The [candidate register](../../data/prepilot/temporal-warning-plan.candidate.json)
reuses the existing pre-pilot launch gate, but does not promote its old corpus to
unseen data. Proposed scale: 12 NEW independently reviewed intents from six
projects, clean/defective pairs, two distinct qualified providers, three runs per
variant/provider: 144 planned episodes if all gates pass. This is an engineering
and estimation pilot, not a sufficiently powered confirmatory H2 sample. Source
selection is currently empty: no fresh requirement or human approval is fabricated.

Use the existing pinned sources as a search pool, not as admitted cases. Review
prior run registries, near clones and exposure logs before assigning fresh IDs.
Select on source eligibility and auditable constraints before observing generated
outcomes; retain null cases and failed admissions. Record source/revision/license,
constraint IDs, A/B-equivalence where a rewrite is used, single-condition deletion,
reviewer identity and prior exposure. Two genuinely independent human reviewers
must resolve mapping/manipulation disagreements before admission. LLM votes do not
satisfy this gate. Never expose the complete counterpart or rubric to the generator.

Assign all intents/variants/repeats and near-clone-connected projects together with
`eval.splits`. Candidate allocation is 3 training / 1 calibration / 2 test projects;
the exact identities and seed require freeze before generation. One calibration
project and two test projects cannot support robust population inference; enlarge
for confirmation using the existing precision/sample gates. If either calibration
or test is one-class, affected metrics are undefined/blocked, not zero.

Collection uses the existing runtime-native staged producer with separate bounded
T1 interpretation, T2 plan, T3 externally materialized execution evidence and T4
acceptance criteria. Validate substantive checkpoints, identities, monotonic times,
request/configuration hashes, cost and stage receipts. Do not reconstruct timestamps
from final output or call retrospective E2E reports temporal trajectories. Qualify
two real configurations, the event adapter and private custody before collection.
Browser E2Es can qualify engineering controls; they do not replace blinded ordinal
acceptance-criteria labels, annotation agreement or the primary label manifest.

After alerts are sealed, independently double-annotate T4 under the frozen rubric,
adjudicate, and join by run_id/replication_id/constraint_id. Evaluate B0 and B3 on
identical eligible records; report comparator/window-specific missingness and paired
complete-case plus missing-stage sensitivity. Primary PR-AUC means the existing
average-precision implementation. Add supplementary recall/FPR and first observed
alert lead time to T4. Ranker scores are not probabilities: calibration/Brier/ECE
requires a separately frozen calibration-only probability mapping. Reuse the
existing project-cluster bootstrap and report descriptive-only intervals when the
small/one-class cluster design fails existing gates. Do not pool repeated generations
as independent requirements or claim causal recovery without a cue intervention.

Current dependencies: fresh corpus identities and reviews, exact split freeze,
annotation rubric/annotators, two qualified providers, runtime/event adapter and
budget authorization. This execution found neither Codex CLI nor Docker available;
no new provider episode or empirical comparison was performed.
