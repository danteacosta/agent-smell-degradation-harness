# RealWorld Article-Author UI Oracle Design

Date: 2026-09-24  
Status: design approved; implementation and experimental admission pending

## Purpose

Qualify a deterministic browser oracle for an independently sourced RealWorld
UI obligation outside TodoMVC:

> Delete article button (only shown to article's author)

The source is the RealWorld maintainers' frontend routing specification at
revision `ebbcdeb8d55b42a3a613c787560498b8ef10003f`. The preserved source SHA-256
is `65fbd975a3ab2021057b1c1944cf66418aa846039e51b166d2a98eb29e7169fb`.

This work qualifies an authored-control instrument. It does not generate model
outputs, admit a study case, rescore prior artifacts, or add evidence for H1 or
H2.

## Alternatives considered

### Standalone generated article page — selected

The generated artifact is one self-contained HTML page that consumes a neutral
`window.initialState` containing a viewer and an article. A trusted Playwright
controller renders the same bytes in separate author and non-author contexts.

This option preserves a real browser boundary, keeps fixtures deterministic,
and avoids coupling the model output to a particular RealWorld framework or
backend implementation.

### Generated view inside a fixed RealWorld shell

A fixed router, styles and data layer would host a generated view component.
This is closer to an application integration, but the shell can disclose the
ownership rule through props, policy helpers, selectors or surrounding code.
Framework compatibility would also become part of the measured task.

### Full RealWorld implementation pair

A complete frontend/backend deployment would provide the strongest ecological
realism. It also adds authentication, persistence, routing, build and network
variation unrelated to the selected condition. The resulting cost and failure
surface are disproportionate for the first cross-project instrument.

## Acceptance contract

The implementation is accepted when all of the following observable scenarios
hold.

1. **Author view:** given viewer `alice` and an article authored by `alice`, when
   the article route renders, then exactly one visible button with accessible
   name `Delete Article` is present.
2. **Non-author view:** given viewer `bob` and the same article authored by
   `alice`, when the article route renders in a fresh browser context, then no
   visible button with accessible name `Delete Article` is present. A removed or
   hidden button satisfies this bounded “only shown” condition.
3. **Page prerequisite:** in both contexts, the expected route, article title,
   body and author identity are visible before the ownership condition receives
   a target verdict. If the article page is unavailable or materially broken,
   the target is not evaluable and the page failure is reported separately.
4. **Oracle sensitivity:** two independently structured valid controls pass;
   always-visible and never-visible target mutants fail the corresponding
   ownership assertion; a broken-article control is not mislabeled as a target
   failure; duplicate author controls are reported as unassessable.
5. **Evidence:** the qualifier records the immutable browser image, input and
   runtime hashes, exact categories and assertion IDs, structured observations,
   and author/non-author screenshots.

The source specifies visibility, not delete execution, navigation after a
click, backend authorization or security. Those behaviors are outside this
oracle.

## Public candidate interface

The candidate receives the same interface in every future A/B/C arm:

```javascript
window.initialState = {
  viewer: { username: "alice" },
  article: {
    slug: "bounded-ui-case",
    title: "Bounded UI case",
    body: "Observable article body",
    author: { username: "alice" }
  }
};
```

The controller changes only `viewer.username` to `bob` for the non-author
context. The interface describes available data but does not say when any
control must be rendered. It contains no target label, omission annotation,
oracle code, source URL or fixture expectation.

The future prompt will require a self-contained article page at
`/article/bounded-ui-case` and consumption of `window.initialState`. The exact
A/B/C prompt texts require a separate leakage review and freeze after the
instrument qualifies.

## Browser observations

The trusted controller serves candidate bytes only at
`http://fixture.invalid/article/bounded-ui-case` and aborts every other network
request. It creates a new browser context for each viewer and injects the state
before candidate scripts run.

The delete-control role is resolved through Playwright's accessible button role
and a whitespace-normalized, case-insensitive exact accessible name of
`Delete Article`. This follows the source and official template without
requiring a private class, component name or test ID.

For each context, the report records bounded counts for:

- visible title text;
- visible article body text;
- visible author identity;
- all matching delete buttons and the subset that is visible;
- final URL; and
- console and page errors.

Screenshots illustrate the rendered state but never replace structured browser
observations as the verdict source. Opacity-only hiding remains visible under
the declared endpoint because a rendered control still occupies the interface;
the exact Playwright visibility behavior and browser version are pinned in the
qualification image.

## Classification

The report schema is `realworld-author-ui-browser/v1`. The Python adapter rejects
duplicate JSON fields, unknown schema versions, extra or missing observation
fields, wrong scalar types, counts outside fixed bounds, inconsistent visible
counts, oversized console errors, unsupported assertion IDs and exit-code
contradictions.

Target assertions:

- `author_sees_delete_article`;
- `non_author_does_not_see_delete_article`.

Non-target assertion:

- `article_page_preserved`.

The page assertion is a prerequisite for both target assertions. If it fails in
either context, target status is `not_evaluable`; it is never converted into a
requirement-smell failure. More than one visible author delete button is also
`not_evaluable` because the declared singular control identity is ambiguous.
Any visible matching delete button in the non-author context is a target
failure, regardless of duplicates.

The adapter maps complete reports into `pass`, `target_only_failure`,
`non_target_only_failure`, `mixed_failure`, or `target_not_evaluable`.
Malformed reports, interface failures, browser failures and timeouts remain
separate operational categories.

## Authored-control matrix

The initial qualification contains:

- a reference that conditionally inserts/removes the button using direct
  username equality;
- a structurally different reference that derives an ownership policy and
  keeps a hidden non-author control;
- an always-visible mutant;
- a never-visible mutant;
- a wrong-identity mutant;
- a broken-article control that prevents target evaluation;
- a duplicate-author-button control; and
- a missing-interface control that fails before classification.

The qualifier must match every expected category, target/non-target failure set
and not-evaluable reason. A mutant kill demonstrates sensitivity only to this
bounded obligation; it is not evidence of completeness or smell causality.

## Isolation and trust boundary

The candidate HTML is untrusted. It runs in the existing offline,
resource-bounded Docker pattern with a read-only input, writable evidence
directory, no network, dropped capabilities, bounded processes, memory and
time, and a trusted external Playwright controller. The controller writes the
report and screenshots. Candidate code never writes the classification receipt.

The implementation reuses the existing container command and receipt patterns.
One adapter boundary is justified: it isolates the external browser-report
schema from internal outcome categories and allows schema versioning. No new
factory, strategy hierarchy or generic oracle framework is needed.

## Planned files

- `eval/realworld_author_ui_executor.py`: schema validation, classification and
  bounded container execution.
- `eval/fixtures/realworld-author-ui/runner.cjs`: trusted two-context browser
  controller.
- `eval/fixtures/realworld-author-ui/Dockerfile`, `package.json` and
  `package-lock.json`: pinned offline runtime.
- `eval/fixtures/realworld-author-ui/qualify.py`: authored-control matrix and
  evidence manifest.
- `eval/fixtures/realworld-author-ui/*.html`: reference, mutant and interface
  controls.
- `tests/test_realworld_author_ui_executor.py`: report and category behavior.
- `.github/workflows/realworld-author-ui-oracle-qualification.yml`: Linux
  qualification and artifact upload.
- `docs/research/realworld-author-ui-oracle-qualification-20260924.md`: source,
  hashes, results and limitations after qualification.

## Verification

Implementation must proceed test-first:

1. write classifier tests for pass, the two target directions, prerequisite
   failure, ambiguity, malformed observations and exit-code mismatch;
2. confirm those tests fail for the intended missing behavior;
3. implement the minimal adapter and runner;
4. run focused Python tests plus JavaScript syntax and JSON checks;
5. build the pinned browser image and execute every authored control;
6. inspect representative author, non-author, mutant and ambiguous screenshots;
7. run the repository eval, replay and wedge gates in the supported Linux
   CPython 3.12 CI environment; and
8. record exact hashes without admitting the case or calling a provider.

The current macOS baseline has an environment limitation unrelated to this
design: Darwin reports `RLIMIT_AS` as `9223372036854775807` and rejects the
supervisor's finite address-space limit before child execution. On 2026-09-24,
the local suite therefore produced `1766 passed, 21 skipped, 4 failed`, with all
four failures in `tests/test_collection_limits.py`. The same `main` revision
passed both Linux CPython 3.12 `eval-gate` jobs. This design does not change or
waive the collection-limit policy; implementation completion depends on green
supported CI and focused local checks.

## Admission boundary

Qualification does not admit the requirement into the study. A successor step
must independently verify the exact source slice and single-span deletion,
review a meaning-preserving B rewrite, audit the serialized common interface for
target leakage, freeze prompt/runtime/schedule/custody bytes and define treatment
of every not-evaluable result. Only a prospective collection under that frozen
packet can contribute new behavioral observations.
