# Prospective multi-obligation E2E expansion protocol

Status: **candidate protocol before oracle implementation, qualification, prompt
freeze, or model dispatch**. This document defines the next evidence block; it
does not add an outcome to the six-project evidence matrix.

The [independent screening panel](multi-obligation-screening-panel-20260925.md)
subsequently accepted 3 of these 12 candidates unanimously. The resulting
pre-qualification ceiling is 54 positions; the 216-position design below
remains the target only after deferred candidates are narrowed or replaced.

## Research contract

The current pilots show that deleting one requirement obligation can produce a
visible defect, but they contain only one observed obligation per project. The
next block tests whether that result survives new obligations within the same
six projects. The unit that increases external evidence is the independently
sourced obligation. Repetitions measure generation variability and are not
treated as independent requirements.

The candidate design contains 12 obligations, two per project. If every
candidate passes admission, the collection has 216 positions:

`12 obligations × 3 arms (A/B/C) × 2 model configurations × 3 repetitions`.

Each position generates one self-contained browser application or bounded UI
replica in a fresh context. The generator receives one requirement variant and
one common interface only. It cannot read sibling variants, oracle code,
mutants, expected values, prior outputs, or this protocol.

Acceptance criteria for admitting the collection are:

1. every source byte and license/reuse basis is revision- and hash-bound;
2. A contains the target obligation, B preserves it in a meaning-equivalent
   rewrite, and C deletes exactly that obligation without repairing it;
3. one deterministic browser endpoint observes the target through the user
   interface, while separate assertions protect at least two non-target
   behaviors;
4. two structurally different correct implementations pass, a target-only
   mutant fails only the target, and a non-target mutant does not become a
   target failure;
5. duplicate IDs, missing action preconditions, malformed observations, console
   failures, and unexercisable interfaces fail closed as invalid or unknown;
6. an independent three-judge LLM panel unanimously accepts the
   source-to-assertion mapping and prompt-leakage review. Any disagreement
   defers the candidate before dispatch;
7. the final eligible set, prompts, runtime image, schedule, model settings,
   seeds, assertion IDs, settling limits, and hashes are frozen together.

The LLM panel reviews the instrument only. It does not label generated outcomes.
Pass, target failure, non-target failure, mixed failure, invalid, and unknown
come solely from frozen browser observations.

## Candidate obligations

These are screened candidates, not admitted cases. Line references use the
checked-in source bytes and are accompanied by their SHA-256 digest.

| ID | Project and source | Deleted obligation to test | Browser endpoint | Main admission risk |
| --- | --- | --- | --- | --- |
| `todo-clear-master` | TodoMVC `app-spec.md`, lines 90–92; `5bf3ac…1094` | Clear the master checkbox state after **Clear completed**. | Complete all items with the master, clear them, and observe that a remaining visible master is unchecked; a removed master is a distinct valid empty-state outcome. | Familiar TodoMVC handles may cue recovery; duplicated or unrelated checkboxes must not substitute for the master. |
| `todo-edit-state-not-persisted` | TodoMVC `app-spec.md`, lines 116–118; `5bf3ac…1094` | Editing mode must not persist. | Enter edit mode in one page, open a fresh page at the same origin, and observe the saved todo outside edit mode. | Opening the second page must not blur or save the first; missing todo persistence makes the target unassessable. |
| `realworld-follow-no-extra-input` | RealWorld `endpoints.md`, lines 82–88; `b1aecb…08e7` | Following a user requires no additional parameters. | An authenticated viewer follows an existing user with no body or query fields and sees the profile change to `following=true`. | A common interface must not reveal that the body is optional; authentication and response shape remain non-target controls. |
| `realworld-comment-auth-required` | RealWorld `endpoints.md`, Add Comments subsection; `b1aecb…08e7` | Adding a comment requires authentication. | An anonymous UI submission cannot create a comment; a separate authenticated submission creates exactly one visible comment. | Error text is not the target; a state read must distinguish rejection from a hidden write. |
| `kanboard-close-hides-task` | Kanboard `tasks.md`, Closing Tasks subsection; `281c39…f081` | Closing a task hides it from the board. | Close a visible task, verify it leaves the board, then verify it is still reachable through the closed-task filter. | The oracle must distinguish hidden from deleted and keep retrieval as a non-target preservation check. |
| `kanboard-duplicate-preserves-properties` | Kanboard `tasks.md`, Duplicating Tasks subsection; `281c39…f081` | Duplicating in the same project creates a new task with the original properties. | Duplicate a task and observe two distinct rows with equal visible title, description, assignee, category, and due date. | Identity must differ while copied fields match; autogenerated IDs and timestamps cannot be exact-equality gates. |
| `paperless-accept-duplicate` | Paperless-ngx `usage.md`, lines 299–304; `78fc96…1c94` | By default, a same-checksum document is still consumed. | Upload the same fixture twice and observe two document records plus a visible duplicate warning/task flag. | The replica must predeclare default configuration and avoid exposing the accept/reject target through its upload API. |
| `paperless-suggestion-decisions` | Paperless-ngx `usage.md`, lines 316–320; `78fc96…1c94` | A shown suggestion can be accepted or rejected by the user. | Open a document with frozen suggestions; accepting one changes metadata, while rejecting another removes it without applying it. | Suggestion generation itself is fixture data; only the user-visible decision behavior is scored. |
| `nextcloud-restore-name-conflict` | Nextcloud `deleted_file_management.rst`, lines 22–25; `9e8218…106f` | A restored item receives a unique name when the original name already exists. | With an active name collision, restore the deleted file and observe both files with distinct visible names. | The source does not prescribe the suffix; the oracle must accept any unique, nonempty name. |
| `nextcloud-delete-permanently` | Nextcloud `deleted_file_management.rst`, lines 9–20; `9e8218…106f` | **Delete permanently** removes an item from Deleted files. | Permanently delete one trashed file, refresh both views, and observe that it is absent while an unrelated trashed file remains. | Absence must survive refresh; a missing action or failed precondition is invalid rather than a pass. |
| `openproject-invalid-remaining-not-saved` | OpenProject `progress-tracking.md`, lines 105–107; `9aec06…1f9` | Remaining work greater than Work cannot be saved. | With Work=8h and stored Remaining work=7h, enter 9h, attempt to save, refresh, and observe that stored Remaining work remains 7h. | Only prevention of the invalid save is scored. Work and reload are controls; error feedback is not asserted. |
| `openproject-derive-remaining` | OpenProject `progress-tracking.md`, lines 97–103; `9aec06…1f9` | With Work set, entering % Complete derives Remaining work. | Save Work=10 and % Complete=40 and observe Remaining work=6. | Numeric formats may vary; the endpoint compares normalized quantities and separately preserves entered values. |

The source files are:

- `data/criteria-expansion/sources/todomvc/app-spec.md`
- `data/criteria-expansion/sources/realworld/docs__src__content__docs__specifications__backend__endpoints.md`
- `data/e2e-six-projects/sources/kanboard/tasks.md`
- `data/e2e-six-projects/sources/paperless-ngx/usage.md`
- `data/e2e-six-projects/sources/nextcloud/deleted_file_management.rst`
- `data/e2e-six-projects/sources/openproject/progress-tracking.md`

## Prospective analysis

The primary outcome for an evaluable generation is whether at least one frozen
target assertion fails while every non-target assertion passes. A failure of a
non-target assertion is reported separately and never counted as a target-only
effect. Invalid and unknown outputs remain in the denominator ledger and are
bounded rather than silently discarded.

Report A, B, and C counts for every `(obligation, model)` cell. The primary
contrast is C−A; B−A is the rewrite-control diagnostic. Summaries first average
within obligation, then within project and model so three repetitions cannot
outvote a new requirement. Report all obligation-level results, including null
effects and recovery of deleted information. Do not pool these rows with the
earlier six pilots because their selection, scaffolds, and collection dates
differ.

With only 12 purposively selected obligations, the block remains an
intermediate pilot. It can show replication across obligations and estimate
heterogeneity inside this bounded corpus. It cannot by itself estimate the
population prevalence of requirement smells or confirm H1/H2.

## Execution order

1. Preserve exact excerpts, deletion spans, revisions, licenses, and full
   source hashes in a machine-readable candidate register.
2. Implement each common UI scaffold and browser oracle without any provider
   output.
3. Add two reference implementations, a target-only mutant, and non-target
   mutants; qualify them in the final browser runtime and preserve screenshots.
4. Run the three-judge instrument review and defer every non-unanimous case.
5. Freeze A/B/C prompts and one randomized blocked schedule, stratified by
   obligation, arm, model, and repetition.
6. Dispatch once, preserving provider errors and raw artifacts privately.
7. Validate all public rows against receipts, then publish aggregate results
   and representative original screenshots.

No provider call is authorized by this candidate protocol alone. Dispatch
becomes eligible only after steps 1–5 produce a complete, hash-bound freeze.
