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

The generated artifact is one self-contained HTML page that consumes a common
feasibility interface, `window.initialState`, containing a viewer and an
article. A trusted Playwright controller renders the same bytes in crossed
author and non-author contexts.

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

1. **Author views:** given an article authored by `alice` and viewer `alice`, and
   separately an article authored by `bob` and viewer `bob`, when each article
   route renders, then at least one perceptible button with accessible name
   `Delete Article` is present. Multiplicity is diagnostic because the official
   pinned template renders the action in two article-meta regions; the source
   does not require exactly one instance.
2. **Non-author views:** given the same Alice article with viewer `bob`, and the
   same Bob article with viewer `alice`, when each route renders in a fresh
   browser context, then no perceptible button with accessible name
   `Delete Article` is present. A removed or non-perceptible button satisfies
   this bounded “only shown” condition.
3. **Page prerequisite:** in all four contexts, the expected route, article
   title, body and author identity are perceptible before the ownership
   condition receives a target verdict. If an article page is unavailable or
   materially broken, the affected target assertion is not evaluable and the
   prerequisite failure is reported separately.
4. **Oracle sensitivity:** two independently structured valid controls pass;
   always-visible, never-visible, hard-coded-identity and transparent target
   mutants fail the corresponding ownership assertion; a broken-article
   control is not mislabeled as a target failure; and a valid two-button author
   control passes.
5. **Evidence:** the qualifier records the immutable browser image, input and
   runtime hashes, exact categories and assertion IDs, structured observations,
   and author/non-author screenshots.

The source specifies visibility, not delete execution, navigation after a
click, backend authorization or security. Those behaviors are outside this
oracle.

## Public candidate interface

The candidate receives the same interface schema in every future A/B/C arm:

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

The controller executes two crossed fixture pairs:

| Fixture | Article author | Author viewer | Non-author viewer |
| --- | --- | --- | --- |
| `article-alice` | `alice` | `alice` | `bob` |
| `article-bob` | `bob` | `bob` | `alice` |

Only the viewer and article-author usernames change. Both fixture pairs retain
`slug: "bounded-ui-case"`, the fixed `/article/bounded-ui-case` route and the
same title and body; the interface shape and candidate bytes remain identical.
The viewer and article-author identities are necessary feasibility
data and therefore cue that an ownership comparison is possible. They do not
state the delete-control verdict, but this residual cue is recorded as a threat
to construct validity. The interface contains no target label, omission
annotation, oracle code, source URL or fixture expectation. A serialized-prompt
leakage review remains an admission gate.

The future prompt will require a self-contained article page at
`/article/bounded-ui-case` and consumption of `window.initialState`. The exact
A/B/C prompt texts require a separate leakage review and freeze after the
instrument qualifies.

## Browser observations

The trusted controller serves candidate bytes only at
`http://fixture.invalid/article/bounded-ui-case` and aborts every other network
request. It creates a new browser context for each of the four fixture/viewer
combinations and injects the state before candidate scripts run.

The delete-control role is resolved through Playwright's accessible button role
and a whitespace-normalized, case-insensitive exact accessible name of
`Delete Article`. This follows the source and official template without
requiring a private class, component name or test ID.

For each context, the report records bounded counts for:

- perceptible title text;
- perceptible article body text;
- perceptible author identity;
- all matching delete buttons and the subset that is perceptible;
- final URL; and
- console and page errors.

Screenshots illustrate the rendered state but never replace structured browser
observations as the verdict source. The controller applies one generic
perceptibility predicate to delete buttons and to the title, body and author
elements used as page prerequisites. An element is **perceptible** only when
Playwright reports it visible, its finite bounding box is at least one CSS pixel
in both dimensions, its effective opacity across its ancestor chain is greater
than `0.01`, and, after it is scrolled into view, at least one point in a fixed
`5 × 5` inset grid over the intersection of its bounding box and viewport
hit-tests to the element or one of its descendants. Grid coordinates and edge
insets are fixed in the runner and recorded in its source hash. Pointer-event
targeting is not part of the source obligation: inside a `try/finally` around
the hit-test only, the controller saves the target and ancestor inline
`pointer-events` declarations, applies `pointer-events:auto !important`, then
restores every saved declaration before recording the observation. It changes
neither layout nor opacity nor visibility. This bounded exposed-area sample
therefore accepts a visible `pointer-events:none` element and a partially
occluded element when a sampled portion remains exposed, while rejecting one
whose sampled area is fully occluded by a hit-testable element. It does not
claim to detect occlusion by a non-hit-testable overlay or to model every
human-perception or accessibility condition. Removed controls, `display:none`,
`visibility:hidden` and effectively transparent controls are not perceptible.
Exact Playwright, Chromium and viewport versions are pinned in the qualification
image.

## Classification

The report schema is `realworld-author-ui-browser/v1`.

Target assertions:

- `author_sees_delete_article`;
- `non_author_does_not_see_delete_article`.

`article_page_preserved` is a measurement prerequisite, not a non-target
requirement. It is evaluated per fixture/context from the route, title, body and
article-author observations. A prerequisite failure makes every target
assertion that depends on that context not evaluable; it is never converted
into a target failure. Button multiplicity is recorded but does not affect the
verdict. Any perceptible matching button in a non-author context is a target
failure.

The receipt contains exact, sorted `target_failed: string[]` and
`target_not_evaluable: string[]` assertion-ID sets. `target_failed` includes an
assertion when any evaluable applicable context contradicts it.
`target_not_evaluable` includes an assertion when any applicable context lacks
a valid page prerequisite, even if another context produced an evaluable
failure. A separate `not_evaluable_reasons: object[]` is sorted by assertion ID,
fixture ID, context ID and reason. Each unique object contains exactly those
four fields and uses one of the closed reasons `route_mismatch`,
`title_missing`, `body_missing`, or `article_author_missing`. An assertion ID is
present in `target_not_evaluable` if and only if at least one reason object
names it. IDs may appear in both target sets when one applicable context is
unassessable and another yields an evaluable failure.

Category precedence and exit codes are fixed:

1. a report-bearing trusted runner uses return code `20` for
   `interface_failure` and `21` for `browser_failure`; neither reaches
   scientific classification;
2. any non-empty `target_not_evaluable` set yields `target_not_evaluable` and
   exit code `11`, while retaining all evaluable IDs in `target_failed`;
3. otherwise a non-empty `target_failed` set yields `target_only_failure` and
   exit code `10`; and
4. otherwise the result is `pass` with exit code `0`.

The report-bearing runner's return code must be `0`, `10`, `11`, `20` or `21`
and must agree with its category. A Python-side `TimeoutExpired` maps directly
to executor outcome `timeout` after process termination and keeps the observed
subprocess return code, if any, as diagnostic data. Missing or malformed output
maps directly to `malformed_report` and likewise retains, but does not trust,
the observed subprocess return code. These executor outcomes do not pretend the
runner emitted a valid receipt.

The adapter rejects duplicate JSON fields, unknown schema versions, extra or
missing observation fields, wrong scalar types, counts outside fixed bounds,
inconsistent perceptible counts, unsupported assertion IDs or reason codes,
oversized console errors, unsorted or duplicate receipt sets, and category or
exit-code contradictions.

## Authored-control matrix

The initial qualification contains:

- a reference that conditionally inserts/removes the button using direct
  username equality;
- a structurally different reference that derives an ownership policy and
  keeps a hidden non-author control;
- a valid reference that renders two perceptible author buttons and no
  perceptible non-author button;
- a valid reference with a perceptible author button and a transparent
  non-author button;
- a valid partially occluded author control with at least one exposed sampled
  point;
- a valid visible author button styled `pointer-events:none`;
- a valid page whose perceptible title, body and author prerequisite elements
  are styled `pointer-events:none`;
- an always-visible mutant;
- a never-visible mutant;
- a wrong-identity mutant;
- a hard-coded-`alice` mutant that must fail both target assertion IDs across
  the crossed fixtures;
- a transparent-only-author mutant that must fail
  `author_sees_delete_article`;
- a transparent non-author plus visible non-author mutant that must fail
  `non_author_does_not_see_delete_article`;
- a fully occluded author mutant that must fail
  `author_sees_delete_article`;
- a broken-article control that emits a schema-valid observation but produces
  `target_not_evaluable` through a failed page prerequisite;
- a mixed-evaluability control in which one assertion has a prerequisite
  failure while another has an evaluable failure, proving category precedence
  and preservation of both receipt sets; and
- an interface-boundary control in which the qualifier deliberately supplies a
  state payload missing `article.author.username`; the runner rejects it as an
  operational `interface_failure` before navigation or candidate execution.

The broken-article control receives a valid, immutable interface and executes,
but fails to render the expected page body, so its target is not evaluable. The
interface-boundary control instead proves that invalid harness input never
reaches candidate execution. The controller installs each valid fixture as a
deep-frozen, non-writable and non-configurable `window.initialState` property
before candidate scripts run.

The qualifier must match every expected category, target-failure set,
not-evaluable set and closed reason. A mutant kill demonstrates sensitivity
only to this bounded obligation; it is not evidence of completeness or smell
causality.

## Isolation and trust boundary

The candidate HTML is treated as untrusted. It runs in the existing offline,
resource-bounded Docker pattern with a read-only input, writable evidence
directory, no network, dropped capabilities, bounded processes, memory and
time, and a trusted external Playwright controller. The controller writes the
report and screenshots. Candidate code never writes the classification receipt.

As in the existing browser-oracle image, Chromium may run with its sandbox
disabled inside the constrained container. The evidence records the exact
sandbox flags. Container qualification demonstrates deterministic containment
under the declared controls; it does not prove browser-escape safety or make
the candidate safe to execute outside that boundary.

The implementation reuses the existing container command and receipt patterns.
One adapter boundary is justified: it isolates the external browser-report
schema from internal outcome categories and allows schema versioning. No new
factory, strategy hierarchy or generic oracle framework is needed.

## Planned files

- `eval/realworld_author_ui_executor.py`: schema validation, classification and
  bounded container execution.
- `eval/fixtures/realworld-author-ui/runner.cjs`: trusted four-context
  crossed-identity browser controller.
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

1. write classifier tests for pass, the two target directions, crossed
   identities, prerequisite failure, mixed evaluability, multiplicity,
   perceptibility, malformed observations and exit-code mismatch;
2. confirm those tests fail for the intended missing behavior;
3. implement the minimal adapter and runner;
4. run focused Python tests plus JavaScript syntax and JSON checks;
5. build the pinned browser image and execute every authored control;
6. inspect representative author, non-author, transparent, multiplicity and
   mutant screenshots;
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
