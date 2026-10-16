# Offline evidence diagnostic qualification packet

`eval.evidence_diagnostic_qualification.assess_evidence_diagnostic(packet)` scores
already reviewed decisions. It neither creates labels nor calls a provider.
Reports remain product diagnostics: `confirmatory_eligible` is always false.

The `evidence-diagnostic-qualification/v1` packet contains a frozen project split,
a calibration-selected threshold, a blind-review manifest, a `frozen_labels`
inventory, and the separately supplied `records` containing detector predictions.
The inventory belongs to the post-hoc label plane; keep it hidden from the detector.

Every inventory entry has exactly these nonempty string fields:

- `record_id`
- `pair_id`
- `project_id`
- `constraint_id`
- `family`
- `expected_decision`

Freeze the inventory before attaching predictions. Its receipt is
`label_review.frozen_labels_sha256`: SHA-256 of
`{"project_split": project_split, "labels": frozen_labels}` serialized by
`json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)`
and encoded as UTF-8. Object keys are sorted; inventory list order is preserved.
The actual digest must match, rather than merely having valid hexadecimal syntax.
The rubric receipt is a separate external artifact reference; this function does
not receive or verify rubric bytes.

`records` must contain every frozen identity exactly once, including development
and calibration identities. Their six label fields must equal the frozen entries.
The receipt also binds project assignments, so a failed evaluation project cannot
be reclassified as development after the freeze. Result order may differ, and
predictions do not enter the label digest. Missing,
inserted, duplicated, or changed records reject the packet before any metric is
returned. Missing or failed detector decisions are rejected under the existing
complete-decision contract; they cannot produce a partial score or a smaller
denominator. Preserve the incomplete packet for diagnosis, without dropping rows.

Only evaluation-project entries enter the reported denominator. The three control
families remain separate: wrong-binding rejection, valid-alternative retention,
and insufficient-evidence abstention. Development and calibration results never
enter evaluation metrics. A pair cannot cross projects or constraints.

The review manifest requires at least two distinct reviewer IDs, hidden predictions,
and labels completed before scoring. A matching digest proves consistency with the
supplied inventory; it does not prove reviewer independence, authorship, or when the
receipt was frozen. External trusted custody and independent review of real pairs
remain human gates. Rewriting the inventory and its receipt together cannot be
detected without that custody. Synthetic tests are contract checks, not field-utility
estimates or H1/H2 evidence.


## Safe authoring helper

Use `freeze_label_inventory(project_split, labels)` from
`eval.evidence_diagnostic_packet` to create the inventory and canonical receipt
before detector predictions exist. The helper accepts exactly the six label-plane
fields listed above, rejects prediction fields and invalid family decisions, and
returns a deep copy so later authoring changes do not silently mutate the frozen
inventory.

Attach the returned `frozen_labels` and `frozen_labels_sha256` to the
qualification packet. Add `diagnostic_decision` and `baseline_decision` only to
the separate result records after review. The evaluator remains the authority:
the helper reduces authoring mistakes but does not establish external custody,
reviewer independence, or freeze timing.

The authoring helper also rejects cross-project/cross-constraint pair identities
and missing evaluation control families before issuing a receipt. This avoids
collecting predictions for an inventory the evaluator would later reject.

## Human review handoff: applicability is not reward

This is a proposed product-only review worksheet, not a change to a frozen
thesis endpoint or the tau2 operator-sensitivity analysis. Prepare the review
view before joining detector decisions or benchmark rewards.

Keep one row per `run_id / replication_id / constraint_id`, with stable
project, task, variant and trajectory-receipt references. Store these review
fields outside the six-field qualification inventory:

| Field | Allowed values / required evidence |
| --- | --- |
| obligation_source | Exact original-policy version, location and text; distinguish it from the agent's mutated input. |
| applicability | applicable / not_applicable / uncertain; cite scenario and trajectory steps establishing the precondition. |
| observation_status | complete / technical_failure / incomplete; missing evidence is not compliance. |
| semantic_verdict | violated / satisfied / uncertain / not_applicable; quote the decisive action and rule, or explain uncertainty. |
| alternative_interpretation | Record valid alternative behavior, residual mentions, exceptions and conflicting policy passages. |
| reviewer_id | Independent reviewer identifier; preserve each first-pass judgment before adjudication. |
| adjudication | Agreement or adjudicated verdict with rationale; never overwrite the original judgments. |
| eval_response | Join reward and detector decisions only after the semantic verdict is frozen. |

Review in two passes. First, two reviewers independently see the original rule,
scenario and trajectory, but not reward, detector output, model identity or
operator name when these can be masked without removing needed evidence.
Document unavoidable unblinding (the trajectory itself may reveal treatment).
Second, freeze and receipt those judgments, resolve disagreements under the
approved rubric, then join the evaluation response.

A candidate silent violation requires **applicability established + complete
evidence + independently validated violation + evaluation acceptance**.
Acceptance without a violation is not a coverage gap. Non-applicability is not
a true negative; missing/technical records remain scheduled and separately
reported. Operator reward sensitivity and semantic violation detection must
have separate tables and denominators. These fields are a worksheet proposal,
not yet an implemented validator or completed annotation.

Illustrative example only: a policy requires confirmation before a consequential
action. A successful final state does not establish that confirmation occurred.
Review the preceding turns and the action boundary. If the precondition never
arose, mark not_applicable; if turns are missing, mark uncertain. Only a complete
trace establishing an applicable violation can support a candidate missed eval.

Related implementation reference: [OmissionBench authors' repository](https://github.com/composo-ai/omission-bench).
Its published construction map separates blind fact-sheet extraction, omission
site verification, pair ground-truth gates and clinician review. This is an
adjacent clinical-domain workflow, not evidence for H1/H2 or a validated tau2
rubric. The paper's full text was inaccessible on 2026-10-15; only its abstract
and the complete author-released README were read. Human approval of this
worksheet and access to frozen real trajectories remain prerequisites.

## Executable review-view preparation

`eval.blind_semantic_review.prepare_blind_review(records)` now prepares an
allowlisted `review_view` and a separate `private_join_key`. Give reviewers
only `review_view`, never the enclosing object. The join key retains source
metadata and must remain in coordinator-controlled storage.

Inputs require nonempty `run_id`, `replication_id`, `constraint_id`,
`original_rule`, `scenario` and `trajectory`. The helper preserves every
supplied row in order, rejects duplicate identities and fails on missing
evidence instead of silently reducing the denominator. Missing trajectories
must remain in the coordinator's scheduled inventory and exception log;
this helper cannot recover records absent from its input.

The review view contains only a sequential blind ID and the three evidence
texts. Structured reward, model and variant fields cannot enter that view.
This is **metadata masking, not automatic content de-identification**:
trajectory text may reveal treatment, model identity or rewards, so a human
disclosure screen is required before release. This function neither samples
by outcome nor creates semantic labels, and `confirmatory_eligible` stays false.
Keep full original evidence available; do not truncate away exceptions or
confirmation turns merely to improve blinding.

Implementation reference read on 2026-10-16:
[OmissionBench independent-clinician pack](https://github.com/composo-ai/omission-bench/blob/main/sittings/second_clinician_sitting.py),
module documentation and setup (lines 1–90), plus the author-clinician pack's
sampling/masking helpers. The authors explicitly distinguish independent
assessment from agreement and disclose incomplete checklist coverage. This
informs the release gate, not H1/H2, clinical claims or a claim that our exporter
implements their complete method. Code was inspected, not executed.
