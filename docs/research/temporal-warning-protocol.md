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
proof that machine labels are correct. They cover only supplied rows; execution-plan reconciliation below reports
entirely missing episodes separately without assigning labels.
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
selection remains unfrozen: the proposed source pairs below are drafts, not admitted cases or fabricated approvals.

Use the existing pinned sources as a search pool, not as admitted cases. Review
prior run registries, near clones and exposure logs before assigning fresh IDs.
Select on source eligibility and auditable constraints before observing generated
outcomes; retain null cases and failed admissions. Record source/revision/license,
constraint IDs, A/B-equivalence where a rewrite is used, single-condition deletion,
reviewer identity and prior exposure. This temporal candidate retains its original
human-review admission fields. The user-approved exploratory screening workflow
uses two LLM judges plus a third adjudicator (`scripts/run_llm_screening.sh`).
Machine decisions may support exploratory selection, but must not be entered as
human reviews or confirmatory approvals. The screening amendment retains a 20%
human audit before confirmatory claims. A `no_go` from this temporal candidate
applies only to its unfrozen collection, not to all exploratory collection. Never
expose the complete counterpart or rubric to the generator.

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

After alerts are sealed, independently double-annotate T4 under the f…392 tokens truncated…e recorded span. A proposed constraint ID and a testable obligation
are recorded per pair. These are assistant-prepared materials, not reviewed
scientific labels. The selection and project partition remain unfrozen.

| Project | Candidate comparison | Removed condition |
| --- | --- | --- |
| StrictDoc | SDOC-SRS-151 / SDOC-SRS-110 | Default presentation view / document classification |
| CASS | SRCH-002 / SRCH-006 | Maximum search size / exclusion of unreadable objects |
| TodoMVC | Counter / Clear completed | Exact pluralization examples / hide button when no completed todos remain |
| RealWorld | Feed Articles / Unfollow user | Newest-first ordering / no extra parameters |
| Kanboard | Cross-project duplication, two omissions | Destination membership restriction / destination assignee |
| Paperless-ngx | Public share links, two omissions | Expired/deleted link redirect / access without login |

The bounded audit checks prior recorded input strings, not titles or outcomes.
Its hashed inventory contains 898 JSON/JSONL files. It found no complete-clean
input match after whitespace normalization. Paraphrases, overlapping clauses,
previous private experiments, source familiarity and pretraining remain
unresolved. In particular, TodoMVC retains “pluralized form” and an example;
CASS retains “KBAC access control”. These cues may let a model reconstruct the
removed condition. The independent manipulation review must decide whether
each omission is suitable. Reject or revise candidates **before** generation,
not after seeing which ones cause failures. Sibling omissions sharing an
excerpt are related observations; keep them in the same project partition.
This two-arm engineering pilot has no rewrite-control and cannot disentangle
all length/phrasing effects. It does not amend the confirmatory corpus.

Reproduce the source checks with:

```sh
python -m eval.temporal_cohort_candidate \
  --candidate data/prepilot/temporal-warning-source-drafts.json \
  --output /tmp/temporal-warning-exposure-audit.json
```

`runtime_prefix_features` now accepts typed runtime-native checkpoint
observations and maps interpretation → T1, plan → T2, execution/tool → T3.
It reads registered activity names and observation times only, without
traversing semantic payloads. Already isolated prefixes are required; future,
reconstructed and ambiguous-clock observations fail closed. Production clock
behavior and the actual collector adapter still require qualification.

The supplementary comparison runner accepts a prediction table and a
**separate** outcome table. Predictions carry episode/project/intent/run/
replication identities for joining and grouping, not as detector features.
Each prediction has ordered T1–T3 observations with availability times and
scores from B0, B3 and S-structure. Each outcome has episode ID, the predeclared target constraint ID, a resolved
binary terminal label and terminal time. Prediction/outcome constraint IDs must
match. This supplementary comparison analyzes one target per episode; it does
not replace the primary per-constraint analysis or non-target diagnostics. Incomplete or mismatched cohorts,
project overlap (including case/whitespace aliases), cross-project related
intents and observations at/after T4 fail closed. Unresolved labels require
resolution or an explicitly preregistered missing-label analysis; do not
silently discard them to make the runner pass.

```sh
python -m eval.temporal_comparison_report \
  --predictions /private/sealed-prefix-scores.json \
  --outcomes /private/independent-outcomes.json \
  --max-fpr 0.05 --output /private/temporal-comparison.json
```

The supplementary threshold is fitted to the **maximum prefix score per
calibration episode**, implementing the policy “alert in any T1–T3 prefix”.
This requires a comparable score scale across prefixes for each detector,
fixed before calibration. Three independently budgeted checkpoint thresholds
would not constrain the episode false-alarm rate. The output includes stage
average precision, episode maximum-score average precision, test recall/FPR,
first-alert stage, lead time separately identified for true/false positives,
and B3-minus-B0 / B3-minus-S-structure deltas using the existing project
bootstrap gates. The proposed two-test-project pilot remains descriptive.
An empirical calibration bound is not a guarantee of held-out FPR.

The runner does not train detectors or prove that supplied scores were sealed
before T4. Freeze train-only models, score scaling, project/clone groups,
input hashes, schedule and calibration policy separately. Verify the complete
scheduled cohort and independent annotation lineage before running it.
Score-file hashes in the report support custody, not proof of blinding or
causal validity. Primary H2 B0/B3 definitions and the existing F1 threshold
policy are unchanged. No provider-backed episodes were collected for this
preparation, and no synthetic test fixture is experimental evidence.

### Readiness audit: keep the 120- and 144-episode plans separate

The historical `eval.prepilot_readiness` gate is intentionally fixed to its
120-episode design. It cannot admit this proposed 144-episode cohort. The
candidate now references `eval.temporal_warning_readiness` for an offline
readiness audit and preserves the old launch-plan path as historical context.
The new check verifies the cohort/source/audit hashes, declared design,
selection and project partition, source-bound review metadata, two distinct
runtime-native provider identities, annotation/blinding, prefix clocks,
feature/score policy, schedule and finite cost envelope. It does not modify
the historical gate or authorize provider execution.

```sh
python -m eval.temporal_warning_readiness \
  --plan data/prepilot/temporal-warning-plan.candidate.json \
  --output /private/temporal-warning-readiness.json
```

A blocked candidate returns exit code 2 while preserving the report. Even
when all prerequisites are declared, the result is `prerequisites_declared`,
not scientific validation or launch authority. Review metadata and hashed
qualification references in this candidate require independent authenticity checks;
this declarative check cannot prove independence or competence.

For this candidate, freeze the feature definitions and comparable score policy
before training collection. Fit detector weights only on the training
partition after independent training labels become available; then seal those
weights before calibration/test scoring. Freeze thresholds on calibration
only. Do not require fitted weights before collecting the data needed to fit
them, and do not fit on held-out outcomes to fill that gap.

Before releasing review packets, freeze the ordered candidate IDs and preserve
the packet's `candidate_inventory_sha256` in an external decision record. A
matching digest detects inventory replacement; it does not admit candidates or
validate their semantics, rights, independence, labels or representativeness.

## Proposed manipulation-admission check: dependent omissions (2026-10-20)

For the next prospective source review, record for each candidate deletion:

1. The exact removed span and target `constraint_id`.
2. Whether another clause depends on that span, becomes dangling, or changes scope.
3. Whether retaining the rest leaves a plausible specification and preserves all
   non-target obligations; record surviving cues separately from dependencies.
4. Independent reviewers' judgments and an adjudicated admission/exclusion reason.

If a realistic deletion requires removing another independently testable
obligation, do not admit it as a single-condition intervention. Retain it in
the candidate/exclusion log or propose a separately designed compound treatment.
Do not rewrite the remaining text merely to rescue the candidate, or use generated
failures to decide admission. An exact byte-span deletion check cannot certify
these semantic properties.

Rationale: [Arora et al. (EMSE 2019)](https://doi.org/10.1007/s10664-019-09693-x)
explicitly model dependencies among removable segments. Our checklist is a
prospective design proposal, not their detector or a retrospective label change.
The matrix records the evidence limits. Approval is still required before adding
fields to a frozen rubric; B0/B3, H1/H2 and existing candidate materials remain
unchanged. A conceptual-domain-coverage comparator would require its own design
and information-access audit, not automatic admission as a baseline.

`eval/manipulation_admission.py` now prepares this review gate for human
adjudication. It requires exact coverage of a separately frozen candidate
inventory, at least two distinct reviewers per candidate, explicit dependency
and non-target-preservation judgments, and rejects outcome/treatment fields.
The v1 packet accepts only the declared typed review fields; unknown metadata
and alternate outcome-field spellings are rejected rather than copied through.
This structural check cannot establish that free-text evidence is outcome-blind
or that distinct reviewer identifiers represent independent people.
It does not admit candidates automatically and always marks the packet as
non-confirmatory until human adjudication and rubric approval.
The packet also reports agreement separately for removed span, target
`constraint_id`, dependency set, non-target preservation, remainder plausibility
and recommendation. Any disagreement or blocking judgment sets
`requires_adjudication`; reviewer disagreement is retained rather than collapsed.


## Concrete source-draft handoff — 2026-10-27

This is an engineering review queue, not a selected or admitted confirmatory
corpus. The existing public file
[`temporal-warning-source-drafts.json`](../../data/prepilot/temporal-warning-source-drafts.json)
was audited at repository revision `66712467cd093b412d4787c80fed428c00ae3d60`.
The existing `validate_candidate` implementation verified **12 source-span
deletion pairs across six projects**, including source/license file hashes,
source excerpt offsets, exact deletion reconstruction and target identity.
It does not establish source rights, semantic validity, reviewer independence,
lack of contamination, or confirmatory eligibility.

Canonical JSON content digest (UTF-8, sorted object keys, compact separators,
Unicode unescaped):
`2ec1b291c24cffe61bf6fad1c99ffa6a4013de6f679ca82d9de1004e3e60016b`.

Ordered candidate-ID digest (the admission-packet convention):
`fbcce00ccb12dc3d8591a45309601de3bdd9d25c664de08be7ef3ec5b228bb92`.

These are snapshot identifiers, **not an externally attested pre-review freeze**.
The full-content digest and the ID-list digest bind different objects. Preserve
both, together with the exact source revision and rubric, in the eventual
external decision record; do not replace a content commitment with an ID hash.

| Candidate ID | Project | Source locator | Proposed target ID |
| --- | --- | --- | --- |
| `prospective-sdoc-srs-151` | strictdoc | SDOC-SRS-151 STATEMENT | `prospective-sdoc-srs-151-c01` |
| `prospective-sdoc-srs-110` | strictdoc | SDOC-SRS-110 STATEMENT | `prospective-sdoc-srs-110-c01` |
| `prospective-cass-srch-002` | CASS | SRCH-002 requirement table text column | `prospective-cass-srch-002-c01` |
| `prospective-cass-srch-006` | CASS | SRCH-006 requirement table text column | `prospective-cass-srch-006-c01` |
| `prospective-todomvc-counter` | todomvc | ### Counter | `prospective-todomvc-counter-c01` |
| `prospective-todomvc-clear-completed-button` | todomvc | ### Clear completed button | `prospective-todomvc-clear-completed-button-c01` |
| `prospective-realworld-feed-articles` | realworld | ### Feed Articles | `prospective-realworld-feed-articles-c01` |
| `prospective-realworld-unfollow-user` | realworld | ### Unfollow user | `prospective-realworld-unfollow-user-c01` |
| `prospective-kanboard-destination-membership` | kanboard | Duplicate a task to another project | `prospective-kanboard-destination-membership-c01` |
| `prospective-kanboard-destination-assignee` | kanboard | Duplicate a task to another project | `prospective-kanboard-destination-assignee-c01` |
| `prospective-paperless-share-expiry` | paperless-ngx | Share Links | `prospective-paperless-share-expiry-c01` |
| `prospective-paperless-share-no-login` | paperless-ngx | Share Links | `prospective-paperless-share-no-login-c01` |

There are **10 distinct source-excerpt groups**, not 12 independent excerpts:
the Kanboard destination-membership/destination-assignee pair shares one source
span, and the Paperless share-expiry/share-no-login pair shares another.
All candidate siblings remain in their project's partition. Different excerpts
also do not establish independent semantic obligations or source families.
No item is excluded here based on generated behavior.

**Next executable human handoff.** Before any new outcomes, the custodian
approves selection, rights and the rubric; records the above commitments
externally; assigns two genuinely independent reviewers; and gives both the
same pinned source/variant materials without generated outputs or model
identities. Each reviewer supplies the fields required by
`prepare_manipulation_admission`. Adjudicate dependency, source-faithfulness
and non-target-preservation disagreements; retain every exclusion and reason.
Current state remains `selection_frozen=false`, `human_approvals=0`,
`confirmatory_eligible=false`.

A single deletion can be syntactically valid without being an atomic or useful
intervention. Related mutations can distort assessment when counted repeatedly
([Papadakis et al., ISSTA 2016](https://discovery.ucl.ac.uk/1508136/1/ISSTA16.pdf)).
This is an analogy motivating explicit grouping, not proof that these omission
pairs subsume one another. Do not use future kill vectors or terminal labels to
select a more favorable confirmatory set; any outcome-based subsumption analysis
must be a separately labelled exploratory sensitivity analysis.


## Unfilled review forms — 2026-10-28

The [authoring template](../../data/prepilot/temporal-warning-manipulation-review-template.json)
contains two separate 12-row review slots for the existing candidate snapshot.
It is a preparation artifact with **24 unfilled forms**, not 24 observations,
human annotations, or approvals. Each row contains only the admission API's
declared review fields; only candidate IDs are filled. All judgments and actual
reviewer identities remain null, so the admission API rejects the untouched file.

The custodian must give each reviewer only their own `reviews` list, the
same pinned source materials and the approved rubric. Keep responses separate
until both are complete. Slots A/B are routing labels, not reviewer identities.
Do not show generated outputs, provider identities or the other reviewer's
judgments. Verify content and ID commitments before distribution; a manifest
does not prove external custody or independent people.

After independent completion, combine both review lists and call
`prepare_manipulation_admission(reviews, expected_candidate_ids=...)`.
Record disagreement before adjudication and preserve original answers.
Do not replace null judgments with defaults to make validation pass.
Calibration examples and guideline revisions must be separate from scored
candidate judgments; approve the rubric before assigning the scored review.

[Paiva et al., Requirements Engineering 2026](https://doi.org/10.1007/s00766-026-00462-z)
provide a relevant caution: human-mean correlation is not the same as adequate
inter-rater agreement. Their linguistic-quality task is different from our
semantic manipulation-admission task, so neither their agreement values nor a
sample percentage is a transferable admission threshold.


## Isolated assignment export — 2026-10-30

The offline exporter avoids manually editing the combined authoring template.
From the repository root, prepare one assignment at a time:

```sh
python -m eval.manipulation_review_handoff \
  --template data/prepilot/temporal-warning-manipulation-review-template.json \
  --candidates data/prepilot/temporal-warning-source-drafts.json \
  --slot reviewer_A --output /PRIVATE/reviewer-A.json
```

Repeat with `reviewer_B` and a different private output path. The exporter checks
the full candidate-content digest, ordered inventory, both slots' coverage,
declared review fields and null judgments before exporting only the requested
slot. It rejects completed forms and extra fields in either slot, and refuses
to overwrite an existing file. It neither copies peer responses nor generates
human judgments. The packet includes content and inventory commitments; these
are not externally attested freezes.

The custodian must separately supply the same pinned sources and approved
rubric, verify rights and actual reviewer independence, and record distribution
and later adjudication privately. No email is sent and no provider is called.
Completed responses and identifiable staffing records must stay outside Git.

For each human-review task, retain recruitment/expertise, relevant language
proficiency, training/calibration, workload, compensation arrangements, rubric
version, independent pre-adjudication judgments and disagreement resolution.
Document unavailable information explicitly rather than infer it from filled
forms. [Kunilovskaya et al., EMNLP 2026](https://aclanthology.org/2026.emnlp-main.396/)
motivate task-level reporting; their reporting audit does not validate our labels
or supply an agreement/admission threshold.


## Temporal outcome accounting — 2026-10-31

The offline `temporal-diagnostics/v2` report now explicitly declares
`positive_class=terminal_defect=true`. At each cumulative horizon it reports
`defective_labeled_episodes`, `true_alerts`, `missed_defects`,
`nondefective_labeled_episodes`, `false_alerts` and
`nondefective_without_alert`. Recall is true alerts divided by complete-stage,
defective labeled episodes; false-alert rate uses complete-stage, nondefective
labeled episodes. An empty denominator yields null, never zero. The existing
`rate_scope` and missing-stage bounds remain mandatory context.

Episode diagnostics retain the supplied terminal label and classify the first
observed alert as true, false or unlabeled; no observed alert is reported
separately and does not imply a complete negative prefix. Lead time remains an
observed interval, with `first_alert_prefix_complete` retained. Do not pool
false-alert lead times into true-warning antecedence.

These outputs carry `output_plane=label_joined_diagnostics_not_features`.
Labels are joined only after alert freezing; none of these joined fields may
enter a T1–T3 predictor. The analyzer does not authenticate the supplied labels,
fit H2, generate PR-AUC/calibration, or perform project-clustered inference.
Aggregate rates are descriptive episode counts, not independent-project estimates.

[Jin and Chen](https://doi.org/10.1007/s10515-026-00638-5) motivate two-sided
error reporting; their positive class is correct code, the opposite of the
defect-positive convention here. Their percentages and error names are not
transferred. Six offline regressions protect polarity, both denominators,
missing/unlabeled cases, observed lead-time classes and input immutability.


## Execution-plan reconciliation — 2026-11-01

An episode that produces no diagnostic row must not disappear from execution
accounting. Supply the ordered JSON array of episode IDs derived from the
separately frozen execution plan:

```sh
python -m eval.temporal_diagnostics --episodes PRIVATE.jsonl \
  --expected-episode-ids PRIVATE-planned-ids.json --output PRIVATE-report.json
```

The analyzer rejects duplicate/noncanonical planned IDs and observed IDs outside
the plan. At each horizon, `planned_episodes` counts the supplied plan,
`supplied_episodes` counts received rows, `missing_stage_episodes` counts partial
rows and `missing_entire_episodes` counts planned IDs with no row at all.
Complete-stage + partial-stage + entirely absent counts equal the planned count.
`cohort_reconciliation` retains missing IDs in plan order and an ordered-list
SHA-256 commitment. It does not authenticate or externally freeze that plan;
the custodian must verify it against the approved run/replication ledger.

No synthetic row, label, alert, timestamp or cost is generated for an absent
episode. Total cost stays null when any planned episode is absent, while measured
subtotals remain visible. Recall, false-alert rate and missing-stage bounds keep
their existing supplied-label/complete-stage scopes; absence is not a negative
label. Without a plan, coverage remains explicitly `supplied_rows_only`,
and missing IDs/counts are null rather than an asserted zero.

[WebStep](https://arxiv.org/pdf/2606.15673) provides adjacent process-evaluation
context, not evidence for H1/H2. Its task-oracle semantic states and post-hoc
bifurcations must not enter deployable T1–T3 features. Its safe-pass convention
can count an unissued final commit as terminal success (Appendix C.3); do not
transfer that convention to our target-obligation labels. The reconciliation
change follows the explicit missing-row counterexample, not an effect estimate
or threshold imported from WebStep. Seven new offline tests cover the plan and
CLI boundary; no provider execution or confirmatory eligibility is authorized.


## Source materials in isolated assignments — 2026-11-02

Use `--include-materials` with the existing assignment exporter to attach a
strict projection of the bound candidate snapshot: candidate/project IDs,
source/license/notice locators and hashes, the reference excerpt and proposed
remainder. Default exports remain form-only. Each reviewer receives the same
materials with only their own blank forms.

The projection excludes proposed target answers, candidate smell classifications,
exposure metadata, review status, generated outputs and peer judgments. Nested
payloads in source locator fields are rejected. The full candidate-content
commitment still binds the source snapshot, and returned objects do not alias
the input. Without `--source-root`, the packet declares proposals, `source_files_reverified=false`
and `confirmatory_eligible=false`; it does not re-open source/license bytes or
approve rights. Before distribution, the custodian must independently verify
the pinned files, surrounding context, notices, rights and rubric.

[BenchGuard](https://arxiv.org/pdf/2604.24955) motivates inspecting coupled
artifacts rather than treating a reference implementation as unquestioned truth.
Every oracle obligation must be supported by authoritative project material;
reference-code behavior alone is insufficient. Its execution-informed audit
may inspect outcomes, so that mode must remain separate from blinded prospective
manipulation admission. We implement no automated semantic reviewer and import
no confidence threshold, scientific label or model-based approval.

## Offline source-file verification before review — 2026-11-03

The custodian can now re-open the pinned local files before exporting either
assignment:

```sh
python -m eval.manipulation_review_handoff \
  --template data/prepilot/temporal-warning-manipulation-review-template.json \
  --candidates data/prepilot/temporal-warning-source-drafts.json \
  --slot reviewer_A --include-materials --source-root . \
  --output PRIVATE-assignment-A.json
```

`--source-root` requires material export. Verification checks source and license
SHA-256 values, any declared NOTICE path/hash pair, source excerpt bounds and
text, the declared single deletion and target constraint identity. Resolved paths,
including symlinks, must stay inside the supplied root. Missing files, drift or
invalid metadata fail before output creation. Existing responses remain protected
by exclusive creation. Target answers are checked internally and remain excluded
from reviewer materials. The default form-only/unverified modes are unchanged.

A passing packet sets `source_files_reverified=true` with a bounded scope;
`confirmatory_eligible` stays false and every human judgment remains null.
This verifies the supplied local snapshot, not its upstream authenticity,
completeness of notices, reuse rights, pretraining novelty or semantic validity.
An attacker changing both bytes and expected hashes is outside this check;
independent custody and comparison with the authoritative revision remain required.

Validation on 2026-11-03: 18 offline unittest cases passed, including eight new
verification cases. Both isolated assignments verified all 12 existing proposed
pairs across six projects against freshly retrieved pinned source/license/NOTICE
files. These are preparation checks, not reviewed corpus entries or H1/H2 evidence.

[Cleland-Huang and Vierhauser (Requirements Engineering, 2026)](https://doi.org/10.1007/s00766-026-00479-4)
provide dataset-lineage context, not H1/H2 evidence. Hash matching cannot
establish non-exposure. Existing project holdouts and independent exposure
controls remain required; no classification baseline or perturbation protocol
is adopted.

## Pre-adjudication agreement diagnostics — 2026-11-04

Before adjudication, retain the original independent responses. The optional
offline reporter consumes those responses and the separately approved review
inventory; it never fills missing reviews or supplies an admission decision:

```sh
python -m eval.manipulation_review_agreement \
  --reviews PRIVATE-independent-reviews.json \
  --expected-candidate-ids PRIVATE-approved-review-ids.json \
  --output PRIVATE-pre-adjudication-agreement.json
```

The existing admission validator rejects incomplete coverage, duplicate/aliased
candidate-reviewer identities, malformed judgments and extra/outcome fields.
The reporter additionally requires exactly the same two recorded reviewer
identities across every candidate. It does not silently select complete cases
from a changing reviewer pool. It binds the ordered inventory digest, not
independent custody or the candidate/rubric content; these remain external gates.

For every checklist field it reports agreeing candidates, the full candidate
denominator and raw agreement. Dependency lists are compared as sets while
the input responses remain untouched. For the nominal decisions
`admit`, `exclude`, `uncertain`, it reports a 3-by-3 table with explicit reviewer
orientation, row/column marginals, observed agreement and the marginal-based
expected agreement. Unweighted Cohen's kappa is `(Po - Pe) / (1 - Pe)`;
when `Pe=1`, kappa is null with `degenerate_marginals`, even if raw agreement
is perfect. Category imbalance and small samples must be interpreted with the
table, not hidden by a single coefficient.

These are descriptive pre-adjudication diagnostics, not project-clustered
confidence intervals, population estimates, a reliability threshold or validity
evidence. The reporter cannot authenticate human status, blinding, independence,
rights or whether the supplied responses preceded adjudication. Metric choice,
adequacy criteria, calibration rounds and the rubric still require human
approval before confirmatory use. Original private responses and adjudication
history must be retained separately; exclusive output creation prevents overwriting.
Blank authoring templates cannot produce an agreement report. No real review
scores are reported because the independent reviews remain pending.

[Baltes et al., EMSE, online 2026-11-03](https://doi.org/10.1007/s10664-026-10922-3)
provide reporting guidance: agreement alone is not validity. Their illustrative
thresholds are not adopted here. Their recommendation for an open-model baseline
also requires an explicit design decision or justified limitation; no model,
provider runtime or budget is added by this change.

Validation: seven new synthetic pytest cases plus 39 existing admission cases
passed. The hand-computed table yields `Po=3/4`, `Pe=5/16`, `kappa=7/11`;
other tests cover negative kappa, degenerate consensus, reviewer/coverage drift,
field-level disagreement, input immutability, CLI rejection and no overwrite.

## Bind agreement diagnostics to the original responses — 2026-11-05

The reporter now includes `review_content_sha256`, in addition to the ordered
candidate-inventory digest. Previously, two batches with identical decisions
and agreement counts but different written reasons produced identical reports.
The new commitment binds every validated review field, including reasons,
removed spans, original reviewer identifiers and dependency lists, without
copying private responses into the aggregate report.

Canonicalization is explicit: use the supplied candidate-inventory order, then
sort each candidate's reviews by NFKC/casefold reviewer identity; retain original
field values and list order; serialize with sorted object keys,
`ensure_ascii=False`, compact comma/colon separators and UTF-8; hash with SHA-256.
Input row order and JSON object-key order do not affect the digest. Changes to
original text, identity spelling or dependency-list ordering do affect it, even
where aggregate statistics are unchanged. This is not a raw-file checksum.

The custodian must retain the original private responses and recompute this
digest when checking which batch a report describes. The digest cannot establish
authorship, collection time, independence or pre-adjudication custody, nor bind
the rubric or candidate-source content. Those commitments remain separate gates.
Do not publish hashes of private judgments without considering linkage and
guessability; this report belongs with the private review evidence. No review
score, scientific label or approval is supplied by this change.

[Curto et al., EMSE, online 2026-11-03](https://doi.org/10.1007/s10664-026-10981-6)
offer adjacent evidence about prevalence-sensitive agreement. Their binary
elicitation judgments differ from our nominal manipulation decisions. A new
synthetic regression checks that raw agreement of 0.80 can coexist with
`Pe=0.82` and negative kappa; it reproduces no published observations. No AC1,
binary recoding, cutoff or similarity-based correctness label is adopted.

Validation on 2026-11-05: 49 targeted pytest cases passed, including three new
cases for prevalence, changed reasons and canonical content binding. The CLI
round-trip test also checks that the written digest matches the input responses.
Original review objects remain untouched and confirmatory eligibility remains false.





## Reject ambiguous review JSON before hashing — 2026-11-06

The agreement CLI rejects repeated JSON object member names before schema validation
or digest computation, including names that become identical after JSON escape
decoding. For example, two `decision` members must not be reduced to the last
value and then treated as an unambiguous review snapshot. This is a local input
rule informed by [RFC 8259, Section 4](https://www.rfc-editor.org/rfc/rfc8259#section-4).
The Python API accepts already-decoded objects and cannot detect keys discarded
by a caller's parser. Keep original private exports and use the strict CLI for
file intake. No review, rubric approval or confirmatory evidence is inferred.

Validation: 50 targeted pytest tests passed, including the new CLI regression
with two duplicate-name subtests (literal and escaped); neither creates a report.


## Qualification receipt files must match their references — 2026-11-07

The temporal engineering-pilot readiness audit now opens each declared provider
qualification report and verifies its SHA-256 before counting that provider.
Previously only the path/hash metadata and declaration flags were checked;
a nonexistent report with a syntactically valid hash could count. Missing,
unreadable, changed or out-of-root files (including symlinks) now leave the
provider unqualified and preserve no-go when two providers cannot be counted.

This is a byte-integrity check, not semantic validation of the report, provider
execution, configuration-to-report identity, authentic qualification or external
approval. A report may still be forged together with its hash. External review
must validate the configuration binding and runtime-native T1–T3 evidence.
The synthetic test receipt is explicitly not provider qualification evidence.
The historical 120-episode gate and candidate scientific design are unchanged.

Validation: 28 targeted pytest cases passed, including five new receipt-file
failure cases. The current real candidate still returns exit code 2/no_go:
12 source pairs verified, zero reviewed intents, zero qualified providers,
12 pending blockers, collection authorization false.

[Bjarnason et al., On Randomness in Agentic Evals](https://arxiv.org/html/2602.07150v2)
is adjacent repeated-run evidence, not a justification for promoting this gate
or treating temperature zero as deterministic. No repetition count, power
assumption or published variance estimate is transferred to our pilot. File
verification follows the missing-receipt counterexample, not a result from that
paper.


## Preserve readiness reports and input plans — 2026-11-08

Readiness CLI output now uses exclusive file creation. An existing output,
including the input plan itself, is rejected with a nonzero exit and remains
byte-for-byte intact. Previously `--output` could silently overwrite it.
Choose a new report path for each retained assessment. No report is printed
as a successful export after a creation error; ordinary no-go exports to a new
path still return exit code 2 and preserve the no-go report.

Validation: 31 targeted pytest cases passed, including three new cases for an
existing evidence file, output equal to the input plan, and a repeated export.
This prevents accidental replacement; it is not immutable storage or custody
authentication and does not authorize providers or confirmatory collection.

## Bind the exposure audit to the candidate — 2026-11-09

The generator records `candidate_content_sha256` over the parsed candidate
manifest (sorted keys, compact JSON, ASCII escapes encoded as UTF-8, no non-finite
numbers). The readiness gate checks it in addition to the plan's existing
artifact byte hashes and intent coverage. A missing or different digest adds
`exposure_audit_not_bound_to_candidate`, even if all intent IDs are unchanged.

Regenerate from the exact checkout and draft under review, in a new directory:

```bash
audit_dir="$(mktemp -d)"
python -m eval.temporal_cohort_candidate \
  --candidate data/prepilot/temporal-warning-source-drafts.json \
  --output "$audit_dir/exposure-audit.json"
sha256sum "$audit_dir/exposure-audit.json"
```

Inspect the generated inventory and matches before adopting a versioned report.
Then point the plan's `exposure_audit` reference at the new repo-relative path
and record its byte SHA-256 and registry count. Preserve the historical report;
do not attach a digest to it after the fact. The checked-in plan still returns
`no_go` (13 blockers as of this check). The binding detects stale candidate
content; it does not prove that the registry was exhaustive, that paraphrases
were absent, or that a provider never saw either variant during training.
Independent review, project split freeze and authorization remain separate.

### Bound report for the 144-episode draft — 2026-11-10

The active plan now points to
[`temporal-warning-exposure-audit.bound.json`](../../data/prepilot/temporal-warning-exposure-audit.bound.json).
This is a fresh run of `audit()` for the current manifest using the explicit
path list in the [historical report](../../data/prepilot/temporal-warning-exposure-audit.json).
All 898 input files were verified against their historical byte hashes before
the run; the per-path inventory and match map agreed with the historical report.
Among 330 extracted input strings, there was no normalized exact or contained
complete clean-input match for any of the 12 draft intents across six projects.
The report does not cover registries beyond that pinned inventory.

To reproduce this scoped replay, read the historical report's `inventory`,
verify each file against its recorded SHA-256, and pass the listed paths and
parsed current source manifest to `eval.temporal_cohort_candidate.audit`. Compare
inventories by path, since the regenerated report sorts paths. A full-checkout
scan is a separate audit and may cover a different inventory.

The plan remains `no_go` with 12 blockers. This replay clears only the
manifest-binding blocker. It does not establish novelty, screen paraphrases
or partial clauses, qualify a provider, or replace independent exposure review.

[Chen et al. (ESEM 2026)](https://doi.org/10.4230/LIPIcs.ESEM.2026.28)
found that much of the largest observed gain in their vulnerability-detection
comparison was recoverable by replaying selected context. For H2, report the
eligible denominators and alert rates beside the B3–B0 comparison on the same
held-out observations. An incremental prediction gain does not establish a
causal explanation of the lost condition. Any diagnostic replay that uses
information unavailable at its cutoff remains outside the confirmatory
feature plane.

## Count completed reviews per intent — 2026-11-11

The 144-episode readiness audit now counts an intent as reviewed only when at
least two distinct reviewer identifiers each have a valid approval bound to the
current source manifest. The gate applies Unicode NFKC normalization, trims
surrounding whitespace and folds case before deduplication. Duplicate rows
and identifier spelling variants do not supply a second approval. This check
implements the existing manipulation-admission requirement at readiness; it
does not authenticate reviewers, verify independence or adjudicate disagreement.
The candidate remains unreviewed and collection remains blocked.

## Keep unresolved reviews visible at readiness — 2026-11-12

A current-manifest receipt with a valid reviewer identifier and any missing
or non-affirmative approval field prevents that intent from counting as
reviewed, even when two other approvals are present. Conflicting receipts from
the same normalized identifier also block readiness. Old-manifest receipts
cannot satisfy or veto a decision for the current manifest.

Do not delete or overwrite dissenting responses. Keep the original responses
and pre-adjudication agreement report in private custody. A human must resolve
the discrepancy or revise or exclude the candidate under the approved protocol
before preparing a fresh readiness plan. The gate does not adjudicate, infer
assent or issue scientific labels.
