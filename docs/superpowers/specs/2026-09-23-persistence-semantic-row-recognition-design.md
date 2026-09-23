# Persistence Semantic Row Recognition Design

## Purpose

Qualify a successor to the persistence browser instrument that recognizes the
required todo from visible user-facing text across ordinary DOM structures.
The successor must remove the selector-coverage ambiguity exposed by the
2026-09-23 persistence pilot without changing or reclassifying that frozen
collection.

## Acceptance contract

Given a generated TodoMVC page that satisfies the common UI contract, when the
runner adds a uniquely titled todo, then it identifies exactly one visible row
whose visible user-facing title equals the requested title after trimming.
Recognition must work when the title is rendered by an HTML `label`, a
`span`, or another non-interactive visible text container. Hidden text,
accessible-only text, control values outside an active edit field, substring
matches, and duplicate matching rows do not qualify.

Given the recognized row, the runner must activate the user-visible edit
gesture on the title element associated with that match. It must not assume
that the title is a `label`. If the exact visible title is ambiguous within
the row, cannot be acted on, or does not expose the required visible editable
input after the gesture, the artifact is interface-invalid.

After a second page opens in the same browser context and origin, the runner
must independently recognize the exact visible row using the same rule.
Absence or ambiguity after that navigation leaves the edit-restoration target
unknown; it is never converted into a target pass or failure.

## Design

The JavaScript runner will expose one small row-recognition helper returning a
structured match: the row plus the title element used for interaction. The
helper will enumerate direct and nested visible text-bearing elements within
each `ul.todo-list > li`, normalize only surrounding whitespace, and retain
elements whose rendered text exactly equals the requested title. It will
remove ancestor candidates when a more specific descendant has the same
rendered text, reject interactive form controls except the existing visible
editable text input path, and require exactly one row and one specific title
element.

Edit entry will double-click the returned title element. Existing edit-input
detection remains responsible for verifying the observable result. Reload,
completion, storage, screenshot, isolation, and report-classification
contracts remain unchanged.

## Qualification controls

The authored fixture will add independently named modes for:

- visible title in a `span`, expected to follow the same outcome as the
  ordinary conforming reference;
- visible title in another neutral text container, expected to pass;
- hidden matching text beside a visible nonmatching title, expected not to
  select the hidden match;
- two visible rows with the exact same title, expected to fail closed as an
  interface error;
- a visible wrapper and nested title element with identical aggregate text,
  expected to resolve to the most specific element rather than appear
  ambiguous.

All existing selective mutants and controls must retain their expected vectors.
Qualification succeeds only if every expected category, failure list, target
reason, screenshot set, and immutable image identity matches.

## Evidence and scientific boundary

The new image, source hashes, qualification report, and screenshots form a new
versioned packet. The 18 original responses, reports, categories, hashes and
screenshots remain byte-for-byte unchanged. Running the successor over saved
HTML is allowed only as explicitly labelled post-hoc diagnostic analysis.
Prospective evidence requires a new admitted packet, frozen runtime, randomized
schedule, and once-only generation.

The successor validates measurement coverage for alternative DOM structures.
It does not establish an omission effect, prove equivalence among conditions,
or confirm H1/H2.

## Verification

Unit tests cover fail-closed report handling and any new report reason.
Browser qualification exercises all existing and new authored controls in the
pinned offline container. The full repository test suite, evaluation command,
gates, diff review, SOLID review, and clean-code review run before integration.
