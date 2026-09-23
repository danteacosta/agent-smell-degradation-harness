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

The JavaScript runner will expose one small row-recognition helper returning
exactly one of `matched`, `absent`, or `ambiguous`. A match carries the row
and title element used for interaction; the other outcomes carry no locator.
The helper will enumerate direct and nested text-bearing descendants within
each `ul.todo-list > li` and use Playwright's rendered `innerText` after
requiring both the element and row to be visible. It normalizes only surrounding
whitespace and retains elements whose complete rendered text equals the
requested title. It removes ancestor candidates when a more specific visible
descendant has the same rendered text, rejects form controls except the existing
visible editable text-input path, and requires exactly one row and one most
specific title element.

Handling is phase-specific:

| Phase | `matched` | `absent` | `ambiguous` |
| --- | --- | --- | --- |
| After adding, before edit | continue and double-click the title | interface error | interface error |
| Non-target reload checks | assertion passes | assertion fails | assertion fails |
| Target second-page observation | evaluate visible edit state | unknown: `todo_missing_after_reload` | unknown: `todo_ambiguous_after_reload` |

An invisible row or invisible exact-title element is treated as `absent` for
recognition. Existing hidden-row diagnosis may still map a non-visible exact
DOM match to `todo_not_visible_after_reload`; it must never become a match.

Edit entry will double-click the returned title element. Existing edit-input
detection remains responsible for verifying the observable result. Reload,
completion, storage, screenshot, isolation, and report-classification
contracts remain unchanged.

## Qualification controls

The authored fixture will add independently named modes with these exact
vectors:

- visible title in a `span`, expected to follow the same outcome as the
  ordinary conforming reference: `pass`, no failures, no target reason;
- visible title in another neutral text container: `pass`, no failures, no
  target reason;
- hidden exact text beside a visible nonmatching title: `interface_error`
  during initial recognition, no assertion failures or target reason;
- accessible-only exact text with a visible nonmatching title:
  `interface_error`, no assertion failures or target reason;
- form-control value equal to the title outside editing with a visible
  nonmatching title: `interface_error`, no assertion failures or target
  reason;
- visible title that merely contains the requested title as a substring:
  `interface_error`, no assertion failures or target reason;
- two visible rows with the exact same title: `interface_error`, no assertion
  failures or target reason;
- two equally specific exact-title elements in one visible row:
  `interface_error`, no assertion failures or target reason;
- a visible wrapper and nested title element with identical aggregate text,
  expected to resolve to the most specific element: `pass`, no failures, no
  target reason;
- duplication introduced only after reload: `target_not_evaluable`, failed
  `todo_survives_reload` and `completed_survives_reload`, with target reason
  `todo_ambiguous_after_reload`.

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
