# TodoMVC Escape-edit repository E2E screening dossier

Checked: 2026-09-17. Status: screening only; not admitted to provider-backed or
confirmatory execution.

## Narrow behavioral claim

Candidate claim: omitting the condition that Escape discards an edit may make a
code-generation agent commit the draft instead of cancelling it. The observable
failure is at the browser interface: after a user replaces a todo title and
presses Escape, edit mode closes but the replacement text remains.

This is a controlled missing-condition treatment. It is not yet a validated
requirement-smell label, and one case cannot establish that requirement smells
generally cause defective code.

## Upstream evidence bindings

Repository: <https://github.com/tastejs/todomvc> (MIT; `license.md` blob
`9275d4371020294b6a107e454a0d1819f8b71c31`).

Known-good revision:
`1f2bd7f0a1fa8c602284451d282c3821d0d96aec`, authored 2026-05-03,
"Refresh of the modern framework examples (#2297)".

Parent revision:
`c8aedce5f512e47991a62b37b9ee3ef38df1a4b6`.

The known-good commit changes 139 files. It introduced or repaired the selected
Vue behavior together with framework upgrades, test-infrastructure changes and
many unrelated fixes. Therefore, parent versus known-good is provenance for the
feature mapping, not the experiment's causal contrast. The causal rehearsal must
use a one-line targeted mutant on one frozen scaffold.

| Role | Path and revision | Bound blob |
| --- | --- | --- |
| Canonical requirement | `app-spec.md` at known-good revision | `d040877fd8895c4f18fa5190e4b8ee474ffa8ac4` |
| Known-good implementation | `examples/vue/src/components/TodoItem.vue` at known-good revision | `3ca0eb4233e2fee3fddea3d198c58617844eb045` |
| Pre-feature implementation | same path at parent revision | `a128ccf4846237d6ef80c9260eeed33d213a13e4` |
| Shared browser oracle | `cypress/e2e/spec.cy.js` at known-good revision | `478bcfb17f407d56b4db19c4bffadcd0aa1e0972` |
| Vue package declaration | `examples/vue/package.json` at known-good revision | `ac2f8aead7d1eb113297375a03015f8af6ad277b` |

Canonical source sentence:

> If escape is pressed during the edit, the edit state should be left and any changes be discarded.

Candidate arms for independent review:

| Arm | Text | Intended role |
| --- | --- | --- |
| Complete | If escape is pressed during the edit, the edit state should be left and any changes be discarded. | Nominal complete condition. |
| Rewrite control | Pressing Escape while editing must exit edit mode without saving the draft. | Meaning-preserving wording control; equivalence is pending independent review. |
| Missing-condition treatment | If escape is pressed during the edit, the edit state should be left. | Removes only the explicit discard obligation; classification is pending independent review. |

The changed span is `and any changes be discarded`. No variant-specific tests
may be generated after assignment.

## Requirement-to-code mapping

The known-good Vue component initializes a fresh draft from the visible title
when editing starts. `cancelEdit()` first clears editing state and restores the
draft from `props.todo.title`. The Escape handler calls `cancelEdit`; the blur
handler calls `commitEdit`. Because `commitEdit()` immediately returns when
editing is false, the blur caused by removing the input cannot commit the typed
replacement after Escape.

The parent implementation had no Escape handler, used a computed edit model,
and called cancellation on blur. The broad commit message explicitly identifies
the missing Escape handler and stale draft behavior. This supports locating the
feature, but the broad diff prevents using the historical before/after alone as
causal evidence.

## Frozen observable contract

Initial state: three todos are visible and the second title is `feed the cat`.

Action: double-click the second label, replace its edit value with `foo`, and
press Escape.

Outcome: edit mode closes and all three original titles remain visible; in
particular, the second title remains `feed the cat`.

The upstream Cypress test named `should cancel edits on escape` performs the
interaction and asserts that all three original titles remain. It does not
directly assert that the second item loses its `editing` class or that the edit
input disappears. It is therefore a partial oracle for the compound source
sentence. Before freezing the case, the reviewed shared oracle must retain the
title assertions and add direct assertions for edit-mode exit. The selected Vue
revision is intentionally listed as in-memory by the shared test infrastructure,
and the commit reports one skipped persistence test. Reload is therefore outside
this case's oracle. Adding reload would create a false failure unrelated to
Escape.

## Targeted mutant and execution recipe

The minimal candidate mutant changes only the Escape binding in
`TodoItem.vue`:

```diff
- @keyup.escape="cancelEdit"
+ @keyup.escape="commitEdit"
```

Expected oracle behavior:

1. The untouched known-good revision passes the frozen Escape test.
2. The mutant fails because the second visible label becomes `foo`.
3. Complete, rewrite-control and missing-condition code-generation arms start
   from the same scaffold and execute the identical frozen test.

The frozen test must also assert that the second `<li>` no longer has class
`editing` and that its `.edit` input no longer exists after Escape. These checks
come from the canonical complete requirement and must be added before variant
assignment, not after observing generated outputs.

The mutation is a rehearsal of oracle sensitivity, not the generated treatment
outcome. It must not be counted as an H1 result.

Proposed qualified commands after an exact checkout and dependency installation:

```bash
npm ci
npm --prefix examples/vue ci
npm --prefix examples/vue run build
node tests/cya.js -f vue
```

The full Vue run can produce the gold receipt; a focused Cypress invocation may
be added only if its exact test selection is captured in the receipt. The same
environment, built scaffold, command, browser, configuration and oracle bytes
must be used for the mutant run.

## Qualification automation and first attempt

`eval/todomvc_escape_qualification.py` now enforces the rehearsal boundary. It
verifies the exact revision and upstream component/oracle blobs, requires the
two edit-mode-exit assertions, binds both lockfiles and the strengthened oracle
by SHA-256, and runs one unchanged command. It executes the mutant only after a
successful gold run, restores the component atomically, and emits a receipt
labelled `oracle_rehearsal_only`. A shared infrastructure failure therefore
cannot be counted as a mutant kill.

The 2026-09-17 preparation checkout built the selected Vue application under
Node 24.19.0 and the two committed npm lockfiles. The strengthened oracle hash
was `a91bd10963f434a9c7d981bb915fcf3dfef0475761363e6b63826bdf9c873c3a`.
The browser qualification remained blocked before the gold run because the
Cypress 15.14.2 executable download was corrupt twice in this environment and
no browser binary was available locally. The fail-closed receipt recorded
`gold_passed=false`, `mutant=null`, and `mutation_killed=false`; it is an
environment diagnostic, not admission evidence. No provider was called.

## Admission blockers

- Independent mapping review has not approved the requirement-to-Vue linkage.
- Independent manipulation review has not approved the rewrite control, the
  missing-condition treatment or the one-line mutant.
- The upstream Cypress assertion covers title preservation but not edit-mode
  exit; the strengthened shared oracle and its independent review are pending.
- Rights/governance review remains pending despite the public MIT license.
- No qualified-environment gold-pass or mutant-kill receipts exist yet.
- No provider configuration or paid collection is authorized by this dossier.

The case must remain `screening` until every blocker has evidence and reviewer
identity bound in a `repository-e2e-case/v1` manifest. Passing infrastructure
checks, this upstream history, or an LLM judge cannot approve those fields.
