# Kanboard duplicate-title E2E successor

Status: oracle qualified and prompt/schedule frozen before generation; no
generated implementation has yet been evaluated. Qualification and review are
recorded in the [research note](../research/kanboard-duplicate-title-qualification-20260926.md).

This case is `kanboard-duplicate-preserves-title`, unanimously accepted in the
pre-oracle third candidate panel on 25 September. It is a second Kanboard
obligation, in a different interaction from completing unfinished subtasks.
The choice follows observed six-project results and is exploratory. It does
not add a project or a confirmatory H1 observation.

## Acceptance contract

Given a visible source task in project `project-one` with a unique title, when
the user chooses **Duplicate** in its task view, then a second, distinctly
identified task is visible in the same project with the same title. The source
task and an unrelated task remain unchanged. Distinct identity, project
placement, source preservation, and unrelated-task preservation are controls;
only the duplicate's visible title is the scored obligation.

Given the same task and no duplicate action, the original view stays intact.
Given absent/duplicate controls, script errors, malformed reports, or no
distinct duplicate, the target is not evaluable. A duplicate in the wrong
project or a changed unrelated task is a non-target failure, never a
target-only title defect.

## BDD browser scenarios

- Given a correct implementation, when Duplicate is clicked, then the new
  row has a distinct identity, the same project and title, and controls pass.
- Given an alternative correct implementation, when Duplicate is clicked,
  then the same visible outcome holds despite different internal code.
- Given a target mutant, when Duplicate is clicked, then a distinct new task
  appears in the same project but its title differs; only the target fails.
- Given a non-target mutant, when Duplicate is clicked, then title is
  preserved but project placement or unrelated-task preservation fails.
- Given a missing handler, duplicate IDs, or a script error, the runner
  records unknown/interface/browser error, not a target-only failure.
- Given a duplicate inserted before the click, the runner rejects the
  pre-click state even if a subsequent render reveals that duplicate.

## Design and separation

The existing four-project Kanboard page embeds duplication-independent task
behavior and was not designed for this target. Reusing it would expose
irrelevant behavior and risk testing scaffold mechanics. Generating the whole
page would repeat the earlier DOM-conformance failure (64/72 unknown). A small
case-specific fixed page is chosen instead: it owns DOM, navigation, initial
tasks, rendering, and a single `/* MODEL_BEHAVIOR */` insertion point. The
inserted behavior receives a source task and returns a new task object through
a narrow callback. The prompt includes no expected test title, oracle code,
or C-deletion rationale. The state shape necessarily cues fields and is shared
across A/B/C; target recovery in C must be preserved as a valid outcome.

The source requirement and license, page, browser runner, qualification cases,
image ID, exact A/B/C requests, randomized 18-slot schedule, and collector
runtime will be hash-bound before generation. Three repetitions for each arm
and each of `gpt-5.6-luna` and `gpt-5.6-sol` run in separate contexts.
Generation completes before any generated artifact is opened in a browser.
There is no retry, repair, or replacement. Report all 18 positions, including
invalid and unknown outputs, with C−A as the target contrast and B−A as the
wording diagnostic. Do not pool this successor with the earlier Kanboard pilot.
The browser runner and classifier execute from the frozen private runtime
snapshot; its receipt is rechecked after generation, before browser scoring.

The fixed page does not represent the complete upstream Kanboard product.
It is a bounded UI replica used to test propagation of one source-derived
obligation. Browser failure is construct-validation evidence; the formal H1
ordinal-severity outcome and H2 pre-final warning remain unevaluated here.
