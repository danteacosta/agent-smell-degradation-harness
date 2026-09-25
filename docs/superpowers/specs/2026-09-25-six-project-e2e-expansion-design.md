# Six-project E2E expansion design

## Decision

Extend the current TodoMVC and RealWorld browser evidence with one prospectively
selected UI obligation from each of Paperless-ngx, Kanboard, Nextcloud, and
OpenProject. The resulting six-project set is an intermediate pilot. It is not
a confirmatory sample and cannot by itself establish a population-wide H1.

The four new cases stay within the same defect family: omission of one explicit
obligation. Each generated artifact is a standalone browser application. A,
B, and C receive the same interface contract; C differs from A only by the
recorded deletion. B is a meaning-preserving rewrite control.

## ATDD contract

The preparation is accepted when:

1. Four distinct new project IDs bind immutable source revisions, exact source
   bytes, licenses, requirement excerpts, and one deletion span.
2. Each case defines a browser journey, target assertion, non-target assertions,
   invalid-interface state, and unknown state before generation.
3. The schedule contains exactly 72 opaque positions: four projects, three
   arms, two model configurations, and three repetitions.
4. Prompt bytes and every request file are hash-bound before any provider call.
5. A trusted browser oracle accepts valid alternative implementations, rejects
   the target mutant, separates non-target failures, and fails closed on an
   unusable interface.
6. Generation completes for the whole frozen packet before behavioral outcomes
   are analyzed. Failures, unknowns, invalid artifacts, and missing calls remain
   in the planned denominator.

## Cases and observable behavior

| Project | User action | Deleted obligation | Target observation |
| --- | --- | --- | --- |
| Paperless-ngx | Drop a file over the app | Accept drag-and-drop anywhere | A new document row becomes visible after the drop |
| Kanboard | Close a task with unfinished subtasks | Mark unfinished subtasks Done | Closed-task view visibly shows every former unfinished subtask as Done |
| Nextcloud | Delete and then restore a file | Allow later restoration | Restored file returns visibly to All files |
| OpenProject | Enter Work into an otherwise empty progress form | Copy Work to Remaining Work | After Save, Remaining Work visibly equals Work |

The required DOM handles identify neutral interface parts. They do not contain
the expected target verdict. Interface absence is invalid rather than a target
failure. Classification uses rendered, perceptible state and screenshots.

## Analysis

Report A, B, and C by project and model, then an equal-project-weighted
descriptive contrast. Report C-A as the primary causal contrast and B-A as the
wording-instability control. Repetitions are nested observations, not additional
projects. Preserve model interaction, cases with no effect, reverse effects,
and uncertainty from unknown or invalid outcomes. H2 remains a later held-out
detector experiment.

## Risks

The four projects were selected intentionally for licensed, bounded UI
obligations and are a convenience sample, not a representative sample of
software projects. The earlier TodoMVC and RealWorld protocols differ in their
fixtures and endpoints, so six project names do not imply six interchangeable
statistical units.

Standalone replicas measure whether the omitted obligation survives bounded
code generation; they do not establish upstream application compliance. Public
sources may have appeared in model training. Shared interface handles can cue
implementation and therefore remain identical across arms.
