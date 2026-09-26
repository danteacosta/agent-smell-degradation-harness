# Kanboard duplicate-title pilot: pre-generation qualification

This is the second selected Kanboard obligation. The source is the pinned
Kanboard documentation revision `4455fd04fb48ed42817fc99402d4c1fb3bde1c0d`:
duplicating a task within the same project creates a new task with the original
properties, and `title` is listed among those properties. The checked-in source
and MIT license bytes are hash-bound by the freeze. A/B/C are controlled
reconstructions rather than verbatim source excerpts. The choice of this case
followed earlier pilot outcomes, so this is exploratory.

The final browser page keeps its visible task list and initial state fixed.
The generated code can register only the Duplicate behavior. Two independent
fixtures use different task titles and project IDs. After the visible Duplicate
action, the browser requires one distinct new task, checks its visible project
label and that the source and unrelated tasks remain unchanged, and scores
only whether the new visible title equals the source title. If no distinct
duplicate exists, the result is an interface error, not a title failure.

Eight authored controls passed in the immutable, network-disabled Chromium
image `sha256:00d1265095773b7f8a12aa73e81d0bab75563cbd672dd0b5d91783ea1b6d4400`:

| Control | Expected and observed category |
| --- | --- |
| Reference | pass |
| Alternative correct implementation | pass |
| Title-only mutant | target-only failure |
| Wrong-project mutant | non-target-only failure |
| Duplicate identity | interface error |
| Duplicate pre-created before the click | interface error |
| Missing behavior | interface error |
| Script error | browser error |

The first qualification attempt exposed two oracle problems before any model
generation: a blank duplicate title was treated as an unassessable element,
and a script error was masked by the missing-duplicate interface check. Both
were corrected. An independent review found that a duplicate pre-created in
hidden state could pass without a Duplicate handler; the runner now verifies
the pre-click state and registered handler. The final qualification was rerun
after this fix and after the project control was changed to read the visible
label. Earlier failed attempts remain private
diagnostics; only the final qualified bytes are frozen. Original final reports
and screenshots are in
`data/e2e-kanboard-duplicate-title/oracle-qualification-20260926/`.
The qualification also binds the classifier code hash, so scoring cannot
silently change after these controls pass.
The private full qualification receipt SHA-256 is
`499c6221f1c758b6cb6d89aa9e80cc15a74b38d96ff2a3817f93932e0d00581d`;
the 17-file public receipt is
`5907d3c461767321cab108ce6d60d919abe624dc920a3b4bf6962d3ba80e4337`.

Before generation, separate `gpt-6-sol`, `gpt-6-luna`, and `gpt-6-astra`
subscription calls all returned ACCEPT for the exact A/B/C texts and fixed
page: A/B preserve the same target, C deletes only title preservation, the
source supports the target, and the scaffold does not force the answer.
These are LLM instrument reviews, not human approval. The review prompt SHA-256
is `2eb67779af7249cd7af49f1c44c7e465810a732fc03d24a57844671b9199d872`;
the raw reviewer responses and hashes are in
`data/e2e-kanboard-duplicate-title/prompt-review-20260926/`.

The freeze in `data/e2e-kanboard-duplicate-title/freeze-20260926/` contains
18 randomized, balanced A/B/C × two-model × three-repetition requests. Its
manifest SHA-256 is
`9954878ecab7fa169fd421b319b0dbb47e6ee64428ed069dbb50789c08d19d32`.
All generations must precede browser execution, with no retry, repair or
replacement. Unknowns remain in the denominator. No generated model result
exists in this qualification packet, and it does not confirm H1 or H2.
