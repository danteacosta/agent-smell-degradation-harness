# TodoMVC Persistence: browser oracle qualification

The pinned TodoMVC `app-spec.md` subsection “Persistence” says editing mode
should not be persisted. The selected C deletion removes precisely that
sentence. The common generated page interface supplies creation, completion,
and edit entry to all conditions without describing what to store or restore.

The trusted runner uses a second page in the same browser context and origin
while the first remains open, avoiding blur/save side effects. It records native
screenshots before edit, during edit, and after reload. `editing_not_restored`
is assessed only if a visible edit input was reached and the todo is present
after reload. Missing edit entry violates the common interface and is invalid.
Todo survival, completed state, and a nonempty `todos-vanilla`
localStorage entry are separate assertions. Storage bytes and schema are not
used to decide the target; encoded storage is a passing reference.

The eight authored controls are two ordinary references, an encoded-value
reference, a mutant that restores active editing, a no-reload mutant, a no-edit
control, a no-edit control with an unrelated button input, and a completed-state-loss mutant. Qualification requires the exact expected failure
vector for every control, not merely an aggregate pass rate. The Docker image
is pinned by base digest and recorded by built image ID. The private packet
contains reports, screenshots, fixture HTML and hashes. This qualifies the
instrument on authored controls; it does not show a generated-code defect,
general smell effect, or H1/H2 confirmation.

Final local qualification: **8/8 expected vectors matched**. The ordinary,
false-flag and encoded references passed; restoring edit mode failed only the
target; no-reload made the target not evaluable and failed both todo and
completion survival; both no-edit controls were interface errors without
claiming a source-level failure; completed-state loss failed only its own invariant.
The image ID is
`sha256:2c987ec3345d00f5b27f25c40b666a8def180136dfaf27eb562bd9ea24ac1bc3`.
The private packet is
`.private-research-evidence/persistence-qualification-20260922-v4` with 61
evidence files, qualification SHA-256
`1159d356222be2facf5c8658c94d68b3f706c2af78c5de687a67d24c056cc137`
and receipt SHA-256
`75c95ae47647cbe744b444684110798c8a9863f499de97855edfeba3480cb95f`.
The reference and mutant after-reload screenshots were visually inspected.

The oracle observes *visible restoration*. It cannot establish literal absence
of serialized edit-related bytes. The direct-code candidate remains pending
independent prompt-leakage review and cohort freeze. The previous results and
frozen packets are unchanged.

## 2026-09-23 visibility correction

A post-qualification audit found that the runner located a restored todo by DOM
text without requiring the row and its identifying label to be visible. A page
could therefore keep the todo in a hidden row after reload and receive passing
`todo_survives_reload`, `completed_survives_reload`, and target observations even
though no restored todo was available at the user interface. This is an oracle
false positive, not evidence about a generated artifact.

The successor runner requires a visible row and visible label (or visible edit
input) for user-level restoration. A ninth authored control restores the exact
todo and completed state in a hidden row; the expected outcome is two non-target
failures and `editing_not_restored=not_evaluable` with
`todo_not_visible_after_reload`. The Python adapter accepts that reason only as
an unknown target outcome, never as a target pass or defect.

The v4 packet and image above remain immutable qualification history for the old
runner. They do not qualify the corrected bytes. The successor workflow rebuilt
the instrument and matched all **9/9** expected vectors, including the hidden-row
control. The corrected image ID is
`sha256:e284d3ef9996b7cf4d1662a1f0efbc8d89abc8dafa56a52d6e5177a74f1b81bb`;
the qualification JSON SHA-256 is
`3210afa73cd633193f6b27d4dac81fc3ea6468f0a368e52cfb10bb7295764667`, and
the 69-file CI artifact ZIP SHA-256 is
`98f411cf2c42616ff0b620fe0d33fd240d0105ce7e8ed2b09fd471fa0bc99c58`.
Admission remains blocked until the exact prompt passes independent leakage
review and the eligible cohort, runtime, and schedule are frozen.

## 2026-09-23 semantic selector successor

The frozen 18-generation pilot exposed another measurement limitation: four
second-page screenshots show the named todo rendered with a `<span>`, while the
runner recognized only an HTML `<label>` or edit input. Those four historical
target outcomes remain unknown. The [semantic selector qualification](persistence-selector-qualification-20260923.md)
defines a visible, exact rendered-title and actionable edit-entry contract and
matched **27/27** authored controls, including alternative DOM structures and
ambiguous or non-actionable titles. Its image ID is
`sha256:7ec0ab7cde9cf5b84b0ee5d4c07e86a94f1a696c8a26c6ccdbd73569ae460d4a`.
The new private packet and receipt are separate from the v4 and nine-control
history above. This qualification does not revise the pilot classifications or
establish a generated-code or smell effect.
