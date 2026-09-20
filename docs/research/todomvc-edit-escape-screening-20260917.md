# TodoMVC Escape-edit repository E2E screening dossier

Checked: 2026-09-20. Status: screening only; not admitted to provider-backed or
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

## Qualification automation and verified rehearsal

`eval/todomvc_escape_qualification.py` enforces the rehearsal boundary. It
verifies the exact revision and upstream component/oracle blobs, requires the
two edit-mode-exit assertions, binds both lockfiles and the strengthened oracle
by SHA-256, and runs one unchanged command. It executes the mutant only after a
successful gold run, rebuilds the application from each arm's current source,
restores the component atomically, and emits a v2 receipt labelled
`oracle_rehearsal_only`. Each arm must produce a fresh JUnit report; gold must
include a passing `TodoMVC - vue Editing should cancel edits on escape` test.
The mutant must fail that test with the DOM `AssertionError` that its `<li>`
should contain the original `feed the cat` title. Cypress JUnit omits the actual
text value; qualification does not claim that the report observed `foo`. Other failures, missing or malformed
reports, changed test inventories, and signal exits cannot count as a kill.
The runner preserves per-arm stdout, stderr and JUnit files with receipt hashes.
The [built-in Cypress JUnit reporter](https://docs.cypress.io/app/tooling/reporters)
provides this structured evidence without another dependency.

A historical v1 browser rehearsal completed at harness revision
`371330595ef91b25e3bfaf4933189450f7377517`. The known-good implementation
returned 0 and the targeted `Escape -> commitEdit` mutant returned 1 under the
same rebuilt-bundle command and frozen Cypress oracle. The run therefore
recorded `gold_passed=true` and `mutation_killed=true`. Its receipt SHA-256 is
`4af6e35f24507abcace6be008eba65771971068868074b45fe75ee7d685864d7`;
the preserved workflow artifact digest is
`sha256:e585788dfd1f5f0fa58639bdd4663cec41de212faac7bd53aa0bbd1f30083960`.
The historical CI run passed 1,473 tests and 9 subtests. No provider was
called. That v1 receipt classified any nonzero mutant exit as a kill and retained
only output hashes, so it cannot distinguish an assertion failure from an
infrastructure failure. It is historical execution metadata, not qualification
under the v2 evidence contract; a fresh v2 browser rehearsal is required.

Even a successful v2 qualification establishes only sensitivity to this specific
seeded fault. It does not establish
that a requirement smell causes a generated defect, that the mutation is
representative, or that the requirement-to-code mapping is semantically valid.

## Role-isolated review handoff

`eval/repository_case_review.py` now makes the four pending reviews executable
without exposing every reviewer to every condition. The custodian supplies a
private `repository-review-source/v1` file and receives separate mapping,
manipulation, oracle and rights packets. In particular, the mapping reviewer
does not receive the treatment variants, and the oracle reviewer does not
receive the mutant outcome or run receipt. Each completed form must declare
prior exposure and record a decision, confidence, rationale and limitations.

The recorder binds each immutable response to the original form and export
receipt. Assembly requires exactly the four roles, rejects changed materials,
mixed cases and case-insensitive reviewer aliases, and emits records compatible
with the repository admission gate. The generated packets and responses must
remain outside the repository with private permissions. This workflow prepares
human review; it does not supply reviewers, establish their competence, or turn
their decisions into H1/H2 labels.

## Admission blockers

- Independent mapping review has not approved the requirement-to-Vue linkage.
- Independent manipulation review has not approved the rewrite control, the
  missing-condition treatment or the one-line mutant.
- Independent oracle review has not approved the strengthened shared Cypress
  oracle, despite its successful gold/mutant rehearsal.
- Rights/governance review remains pending despite the public MIT license.
- The four approvals must use four distinct pseudonymous reviewer identities;
  one person cannot satisfy multiple review roles.
- No provider configuration or paid collection is authorized by this dossier.

The case must remain `screening` until every blocker has evidence and a
distinct reviewer identity bound in a `repository-e2e-case/v1` manifest.
Distinct identifiers are an enforceable separation-of-duty control, not proof
of expertise or organizational independence. Passing infrastructure checks,
this upstream history, mutation kill, or an LLM judge cannot approve those
fields.
