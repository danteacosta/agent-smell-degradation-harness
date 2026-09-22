# TodoMVC Persistence: browser oracle qualification

The pinned TodoMVC `app-spec.md` subsection “Persistence” says editing mode
should not be persisted. The selected C deletion removes precisely that
sentence. The common generated page interface supplies creation, completion,
and edit entry to all conditions without describing what to store or restore.

The trusted runner uses a second page in the same browser context and origin
while the first remains open, avoiding blur/save side effects. It records native
screenshots before edit, during edit, and after reload. `editing_not_restored`
is assessed only if a visible edit input was reached and the todo is present
after reload. Todo survival, completed state, and a nonempty `todos-vanilla`
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
completion survival; both no-edit controls made the target not evaluable without
claiming a source-level failure; completed-state loss failed only its own invariant.
The image ID is
`sha256:8a863227e0a77362bc519eae38644a0a5410e8483bd9642c2c6c7b27b665ac79`.
The private packet is
`.private-research-evidence/persistence-qualification-20260922-v3` with 65
evidence files, qualification SHA-256
`191a83483698ec4a3fbe03d39179a7f1380432976055a9ff8c7980e2d244336b`
and receipt SHA-256
`8a1c87252946de8c103f33a1297d18edf36d53fb65fa59b01c2e843de27f1ecd`.
The reference and mutant after-reload screenshots were visually inspected.

The oracle observes *visible restoration*. It cannot establish literal absence
of serialized edit-related bytes. The direct-code candidate remains pending
independent prompt-leakage review and cohort freeze. The previous results and
frozen packets are unchanged.
