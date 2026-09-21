# After the TodoMVC pilot: mechanism and next-case screening

Status: post-hoc diagnosis and source screening, 2026-09-21. No new model calls,
no admission approvals, and no change to the completed pilot's frozen evidence.
Acceptance-criteria generation remains the primary thesis task; repository code
generation remains a secondary extension.

## What the null result actually tells us

The nine unchanged generated responses passed the same 28-test inventory in the
supplementary execution: complete 3/3, rewrite 3/3, omission 3/3. The omission
therefore did not produce the targeted observable Escape defect in this pilot.
The reference/manual-mutant contrast validates the oracle's sensitivity to that
mutation; it does not demonstrate a requirement-induced defect.

Inspection of the retained omitted-condition component reveals an available
mechanism: `handleEscape` sets `editing.value = false`; `commitEdit` returns when
editing is false, so blur cannot save the draft; `startEdit` reloads the title
from props. The scaffold supplies behavior omitted from the treatment text.
This is a source-grounded explanation compatible with the observations, not a
separately randomized mediation experiment or proof of the model's reasoning.

Do not remove these guards and pool a new result with this pilot. A different
scaffold would define a different task. Do not repeatedly query this task until
a failure appears. Preserve all null, error and reverse outcomes. There are
three stochastic repetitions per arm, not three independent source requirements.

## StrictDoc: historical anchor recovered, admission still blocked

This follows the selection order already recorded in the
[repository screening](repository-e2e-candidate-screening-20260916.md), rather
than selecting a repository after seeing a favorable model outcome.

| Evidence | Exact binding / finding |
| --- | --- |
| Inspected source revision | `abf7be7daa2a25721a56980b5be15845336ea0b8` |
| Natural requirement | `docs/strictdoc_21_l2_high_level_requirements.sdoc`, `SDOC-SRS-110`: data model supports document UID, version, classification and authors |
| Requirement-to-code link | `strictdoc/backend/sdoc/models/document_config.py` declares a file relation to SDOC-SRS-110 and SDOC-SRS-151 |
| Historical feature commit | `67355ee3b80707639288a83d13f5d7bc5845319d`, introducing optional CLASSIFICATION across grammar, model, writer and HTML templates |
| Immediate predecessor | `e007ebb17950570cde5817a7f7ef6f2bc8489872` |
| Existing UI regression at inspected revision | `tests/end2end/screens/document/update_document_config/update_document_config_classification/test_case.py`: submit Restricted, observe the classification, compare saved fixture |

The current metadata requirement specifies model support. It does **not** by
itself specify editor save/reload plus static HTML export. That proposed journey
must be mapped to additional source requirements before it becomes a canonical
complete requirement; otherwise we would be silently adding researcher-authored
obligations. The existing UI regression is related to SDOC-SRS-57, reinforcing
that distinction. It does not establish reload/export coverage by itself.

The predecessor's `docs/strictdoc-3-requirements.sdoc` was read and did not contain
SDOC-SRS-110, the Document metadata heading, classification or authors. This
checks one historical file, not the entire historical corpus. A broader partial-
clone history search failed fetching a missing object; requirement-before-code
provenance remains unverified. Do not call the current SRS a pre-feature source.

The feature commit is not yet a qualified gold implementation. Its `has_meta`
method still checks UID/version only, while classification is added to HTML
rows. Before selecting it, test a classification-only document as well as one
with UID/version, and confirm the intended rendered visibility. A commit message
or added tests cannot replace an observed reference pass.

## Next bounded scientific step

Prepare an independent source-to-acceptance-criteria case from the pinned natural
metadata requirement first. Define the obligation inventory before generation,
retain a meaning-preserving rewrite control, and have mapping/manipulation and
outcome-rubric reviews completed independently. A missing field is an omission
intervention; it is not automatically a naturally occurring smell instance.
Do not reuse case-specific tuning material as held-out evaluation evidence.

For the optional repository extension, proceed only after (1) identifying source
obligations for the chosen public journey, (2) qualifying the historical base and
reference in an isolated runtime, (3) defining one common scaffold, (4) freezing
one shared oracle that fails a targeted mutant, and (5) completing the existing
independent mapping/manipulation/oracle/rights reviews. If provenance cannot be
recovered, label the task as retrospective reconstruction or record rejection;
do not quietly weaken the inclusion criteria. Sample and generation budgets
remain separate decisions; the earlier 96-episode figure is planning only.

## Sources and evidence trail

- [Pinned metadata requirement](https://github.com/strictdoc-project/strictdoc/blob/abf7be7daa2a25721a56980b5be15845336ea0b8/docs/strictdoc_21_l2_high_level_requirements.sdoc).
- [Pinned model and traceability relation](https://github.com/strictdoc-project/strictdoc/blob/abf7be7daa2a25721a56980b5be15845336ea0b8/strictdoc/backend/sdoc/models/document_config.py).
- [Historical feature diff](https://github.com/strictdoc-project/strictdoc/commit/67355ee3b80707639288a83d13f5d7bc5845319d).
- [Historical requirement file](https://github.com/strictdoc-project/strictdoc/blob/e007ebb17950570cde5817a7f7ef6f2bc8489872/docs/strictdoc-3-requirements.sdoc).
- [Pinned UI regression](https://github.com/strictdoc-project/strictdoc/blob/abf7be7daa2a25721a56980b5be15845336ea0b8/tests/end2end/screens/document/update_document_config/update_document_config_classification/test_case.py).
- [Pilot protocol and interpretation](../todomvc-exploratory-pilot.md).
- Original pilot receipt: `14ca7a6525b88a2f77e7a9ffbb2a53e359b67fcbb8510a5038a88884e328be7b`.
- Supplementary receipt: `d14402551ed8b9f3322e63b3974c8e31c4ed60d4efc238ca71166c407ffc1cd7`.
