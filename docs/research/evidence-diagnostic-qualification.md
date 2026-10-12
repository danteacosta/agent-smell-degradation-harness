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
