# Requirement-smell mapping for the exploratory experiments

The current A/B/C E2Es share one controlled treatment: **remove one
obligation from a source-grounded requirement**. The literature alignment is
semantic incompleteness or partial content, as summarized by
[Alemneh and Berhanu](https://doi.org/10.2478/cait-2024-0037).
The subtype below describes *what was removed* and is our interpretation,
not an independently validated natural-smell label. [Femmer et al.](https://arxiv.org/abs/1611.08847)
explain why semantic completeness needs domain knowledge. The definitions of
`incomplete condition` and `incomplete requirement` in
[Paska](https://arxiv.org/pdf/2305.07097) are narrower than deleting an entire
clause; those exact labels are **not** assigned here. See the
[research catalog](../research/2026-09-26-smell-mapping-for-e2e.md).

| Experiment | Removed obligation in C | Literature-aligned family and subtype | Observed E2E status |
| --- | --- | --- | --- |
| [TodoMVC focus](../research/focus-chain-results-20260922.md) | Focus new-item field on opening | Partial content: missing UI response clause | Selective C failure, 6/6 direct-source C |
| [RealWorld author visibility](e2e-evidence-matrix-20260925.md) | Restrict Delete Article to its author | Partial content: missing actor/authorization condition | Model-dependent contrast; no uniform effect |
| [Kanboard subtask completion](e2e-evidence-matrix-20260925.md) | Complete unfinished subtasks when closing parent task | Partial content: missing cascade response clause | Selective C failure under Luna; one unknown |
| [Paperless drop anywhere](e2e-evidence-matrix-20260925.md) | Accept document drop anywhere in UI | Partial content: missing interaction-scope clause | Selective C failure under Sol; Luna recovered |
| [Nextcloud restore](e2e-evidence-matrix-20260925.md) | Return a restored file to the visible list | Partial content: missing restore response clause | Selective C failure under Sol; Luna recovered |
| [OpenProject Work copy](e2e-evidence-matrix-20260925.md) | Copy Work into Remaining work on save | Partial content: missing field-update response clause | Selective C failures in both models |
| [OpenProject Remaining derivation](../research/openproject-remaining-pilot-20260926.md) | Derive Remaining work from Work and % Complete | Partial content: missing calculation response clause | Selective C failure, 6/6 |
| [Kanboard duplicate title](../research/kanboard-duplicate-title-qualification-20260926.md) | Preserve task title in duplicate | Partial content: missing copied-property clause | Replication: 2/6 selective C failures; first run had unknowns |
| [Paperless duplicate consumption](../research/paperless-duplicate-consumption-20260926.md) | Consume same-checksum copy by default | Partial content: missing default/exception clause | Qualified successor: 4/6 selective C failures |
| [RealWorld favorites](../research/realworld-favorites-20260926.md) | Populate Favorites from favorited articles | Partial content: missing route-specific selection clause | Qualified successor: 0/6 C failures |
| [TodoMVC edit-state persistence bridge](../research/todomvc-persistence-bridge-20260926.md) | Do not persist editing mode | Partial content: missing persistence constraint | Replication: 0/5 evaluable C failures; one interface error |
| [OpenProject invalid Remaining work](../research/openproject-invalid-remaining-20260926.md) | Reject saving Remaining work greater than Work | Partial content: missing validation constraint | 6/6 selective C failures; A/B 12/12 passes |
| [Paperless nested tags](../research/paperless-nested-tags-20260927.md) | Add parent tag when assigning a child tag | Partial content: missing propagation clause | C 6/6 target failures; B 6/6 passes; A 4 passes, 1 target failure, 1 browser error |
| [Kanboard Closed tasks filter](../research/kanboard-closed-filter-20260927.md) | Retrieve an already closed task through Closed tasks | Partial content: missing filter-retrieval clause | Qualified successor: A/B/C 6/6 passes each; first lot instrument failure |

These rows are separate exploratory strata. The same broad family does not
make their prompts, scaffolds, tasks, models, or outcomes exchangeable. The
first six rows established the six-project spread; seven later rows add new
obligations; the TodoMVC bridge is a replication, not new diversity.

The non-browser [12-requirement criteria pilot](../research/criteria-expansion-results-20260921.md)
and [StrictDoc SRS-163](../research/criteria-consensus-results-20260921.md)
also remove a source obligation and map to this broad family. The original
[discount/access/token pilots](../research/codex-original-demo-results-20260914.md)
do likewise. The [coordination and pronoun language controls](../research/codex-language-controls-results-20260914.md)
instead manipulate **syntactic/referential ambiguity**, aligned with
[Paska's coordination ambiguity](https://arxiv.org/pdf/2305.07097) and the
anaphoric or vague-pronoun classes in [Alemneh and Berhanu](https://doi.org/10.2478/cait-2024-0037).
They must not be pooled with the omission family.

Before calling any C variant a naturally occurring smell, an independent
reviewer must assess its plausibility and taxonomy fit without seeing the
generated outcome. The present browser pilots establish effects of deliberate
**clause deletion**, not detector precision, natural-smell prevalence, formal
H1 ordinal severity, or H2 early-warning performance.
