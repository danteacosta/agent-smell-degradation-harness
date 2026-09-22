# UI behavioral expansion: source-to-oracle contracts

Status: **authored design, not qualified or frozen**. No new generation, browser
execution, outcome or human review is claimed here. These three already exposed
source intents are bounded standalone replicas, not tests of the upstream apps.
Their A/B/C texts and exact source bytes remain in the [pinned corpus](../../data/criteria-expansion/corpus.json);
the [candidate register](../../data/behavioral-expansion/candidates.json) records
their prior exposure and proposed 144-slot ceiling. This document specifies
observable contracts for independent instrument construction. Every hidden test,
fixture value, target name and mutant stays outside all generator prompts.

## Shared admission rule

The generator sees one A, B or C text plus the same minimal entry contract for
its intent. It does not see a sibling variant, the whole source document, an
obligation map, a control implementation, test code or expected outcomes. A and
B should have the same permitted mechanics as C. The fixture and oracle may
specify values and actions **after** generation, provided the generator receives
the corresponding public interface in every arm. Prompt and oracle bytes must
be frozen together and audited for target reintroduction. CSS selectors are
observation handles, not required implementation logic.

Each reference and target-only mutant runs in a fresh offline browser context
under the same bounded executor as the focus pilot. Record original assertion
IDs, visible DOM observations, storage/context identity where relevant, native
screenshots before and after actions, console errors and artifact/interface
errors separately. Reference controls qualify sensitivity; they do not supply
scientific treatment labels. The prior focus pilot's empty-list placement check
could reject a valid hidden empty list. No case below requires a bounding box
for an empty list. Passing these bounded tests never means full project
compliance. The browser runtime's own sandbox limitations remain as reported in
the [focus pilot](focus-chain-results-20260922.md).

## StrictDoc `SDOC-SRS-97`: generation date

Pinned [source](../../data/criteria-expansion/sources/strictdoc/docs__strictdoc_21_l2_high_level_requirements.sdoc)
at revision `abf7be7daa2a25721a56980b5be15845336ea0b8`, lines 1287–1296,
requires a Project Statistics screen with title, **date of generation**, Git
revision, document and requirement totals, status breakdown and total TBD/TBC
occurrences. C deletes only the date bullet. The target is a displayed date
corresponding to the generation event; non-target fields need separate checks.

Proposed common generator contract: a standalone browser page renders one
statistics view from a read-only `window.projectStatistics` object supplied
before its script runs. The object contains project title, Git revision,
documents and requirements with statuses and TBD/TBC counts. It contains **no
date, time, `generatedAt` or preformatted date string**. The ordinary JavaScript
`Date` API is available. No prompt asks the app to display or suppress time.
The trusted browser fixture freezes wall time to `2032-04-17T12:00:00Z`, timezone
UTC, before application code runs. Treat view creation as the generation event
for this standalone replica; disclose that interpretation, since the upstream
SRS does not define the event or date format. The fixture uses a distinct title,
revision and numeric counts, with no date-like substring in another field.

Behavior scenario: given that fixture, when the statistics view has settled,
then user-visible page text expresses the same calendar date. Accept ISO
`2032-04-17`, long month forms such as `17 April 2032` or `April 17, 2032`,
and locale numeric forms when their day/month interpretation is unambiguous.
Do not require a `Date of generation` label, markup tag, exact locale, time of
day or visual position. Inspect rendered, perceivable text rather than raw
HTML, hidden nodes, `aria-label` alone or source strings. Qualification must
also test a legitimate localized representation not mentioned here; if the
parser cannot accept it without false positives, narrow the claim or defer the
case. A relative word such as “today” needs explicit semantic adjudication
before freeze rather than a post-outcome decision.

Non-target assertions independently compare the project title and revision,
document and requirement totals, each status count, and the total TBD/TBC
occurrences to fixture-derived values. Use at least two nonzero status classes
and unequal totals so swapping counts is observable. Missing or ambiguous
fixture-to-display mapping is an interface/measurement error, not an automatic
target failure.

Qualification controls: (1) a correct ISO implementation and a structurally
different correct localized implementation pass all checks; (2) omission of
the date, a different calendar date and a date only in a hidden node each fail
only `generation_date_visible`; (3) a wrong revision or count fails its own
non-target check while the date still passes. A static hard-coded date could
pass this one fixed fixture, so run a **second hidden clock value** in
qualification and scoring. Both clocks are fixed before collection, and no
generated code sees their literals. Date matching must use the active fixture
clock; otherwise the test does not establish generation-time behavior.

Admission risk: a generated page might reasonably expect an export timestamp as
input rather than use the runtime clock. The public interface chooses a
standalone view-generation interpretation. An independent source-to-oracle
review must accept that operationalization before dispatch; if it does not,
defer this candidate rather than treat interface failures as source defects.

## TodoMVC `Mark all as complete`: clear master state

Pinned [source](../../data/criteria-expansion/sources/todomvc/app-spec.md) at
revision `ff43b02e59dfa604386bb382034b2cd07c2bcd8a`, subsection “Mark all
as complete”, requires the master checkbox to set every todo to its own state,
to clear its checked state after **Clear completed**, and to track changes to
individual items. C removes only the clear-state sentence.

Proposed common generator contract: one standalone page, with a master
`input[type=checkbox]#toggle-all`, a `button#clear-completed`, and a `ul#todo-list`
whose direct `li` items each contain one individual checkbox and a visible
label. A neutral fixture supplies two uniquely titled, initially active todos.
The generator may choose its state representation and may hide/remove controls
when the list becomes empty. The public contract gives action handles and an
initial state; it says nothing about the master state **after** clearing. The
`clear-completed` handle and familiar TodoMVC semantics can cue recovery, so
retain recovered C outputs and report this residual cue.

Target scenario: given two active todos, click the master checkbox and first
verify both item checkboxes are checked. Click Clear completed. Verify both
completed items are gone by querying direct `li` records without any geometry
or visibility requirement for the now-empty list. If the master exists, its DOM
`checked` property must be false, including when hidden. If the master has
been removed, no checkable master remains; record this distinct valid state
rather than requiring an element that the source does not require in an empty
app. Reintroducing a todo, if that interaction is later provided, must start
with an unchecked master; it is not part of this minimum target assertion.

Independent non-target scenarios use fresh contexts: toggling the master on
checks both items, and toggling it off unchecks both; checking two individual
items in turn checks the master after the second, and unchecking either clears
it. Verify labels identify the same two records and action preconditions hold.
If an app lacks the declared interface, classify it as interface-invalid; if
bulk selection fails, report that non-target failure without mislabeling a
target test whose checked precondition was never reached.

Qualification controls: (1) an explicit mutable master state that resets on
clear and (2) a derived-state implementation using a nonempty-all-completed
rule both pass; the latter may remove the master when empty. (3) A target-only
mutant that leaves a still-present master checked after clear fails only
`clear_master_after_clear_completed`. (4) An individual-sync mutant fails
`master_tracks_individuals` while the target scenario still passes. (5) A bulk
toggle mutant fails `master_sets_items`, and its interrupted target scenario
is classified as unassessable precondition, not evidence for a reset defect.
The empty-list proxy failure from the focus pilot is explicitly excluded.

## TodoMVC `Persistence`: editing mode across a fresh page

The pinned [source](../../data/criteria-expansion/sources/todomvc/app-spec.md),
subsection “Persistence”, requires dynamic todo persistence to localStorage,
conditional framework preference, preferred item keys when possible, a
`todos-[framework]` storage name, and **no persistence of editing mode**. C
deletes only the final sentence. The source's separate “Item” subsection says
double-clicking a label activates edit mode; that action is used solely as a
common test interface and is supplied identically to all arms.

Proposed common generator contract: a standalone vanilla-JavaScript page with
no external library, an `input.new-todo` accepting Enter to add a todo, and a
`ul.todo-list` of direct `li` records, each with one checkbox and visible label.
Double-clicking a label exposes an editable text input in that row. The page
runs at one fixed origin with localStorage available. This supplies ways to
create, complete and enter edit mode but gives **no instruction about what edit
state to store or restore**. The source's conditional framework clause is
vacuous in this no-framework replica; `id/title/completed` keys remain a
preference rather than an exact-schema gate. The storage-name check can accept
the chosen `todos-vanilla` token but must not require a particular JSON shape.

Target scenario: in page 1, add a uniquely titled todo and enter its edit mode
by double-clicking its label. Observe a visible editable input and leave it
open without pressing Enter, Escape or blur. Open page 2 at the **same origin in
the same browser context**, leaving page 1 open so localStorage is shared and
no blur/save transition is triggered. After page 2 loads, the todo must be
present with its original visible title and **without a visible edit input or
active edit state**. Do not inspect CSS class names or serialized `editing`
fields as the primary oracle; a persisted false flag may be harmless while an
arbitrary internal representation may omit that field entirely. The browser
observation establishes absence of restored edit mode, not the stronger claim
that no edit-related byte was ever serialized.

Non-target scenarios independently verify that a newly added todo appears in
a second page without manual save, its title survives another fresh page, and
the completed state set by its checkbox survives. Query localStorage only to
confirm that the app used that storage mechanism and the expected name family;
do not use exact JSON equality. Use unique titles per scenario and clean the
origin between scenarios. An absent saved todo is a non-target persistence
failure, not evidence that editing mode was correctly excluded.

Qualification controls: (1) one reference that omits editing state from stored
records and one that stores a false edit flag but never restores active editing
both pass; (2) a target-only mutant that persists and restores active editing
fails only `editing_not_restored`; (3) a mutant that drops todos at reload fails
`todo_survives_reload` and renders the target scenario unassessable; (4) a
completed-state mutant fails only `completed_survives_reload`. Capture storage
key names and redacted shape diagnostics, never user credentials. If generated
apps require a framework or build process despite the common standalone
contract, classify that as interface-invalid, not a source-level persistence
defect.

## Pre-freeze review required

An independent reviewer must map every assertion to its exact source phrase,
confirm the public interfaces do not restate the three deleted obligations,
run all alternative references and selective mutants in the final browser
image, and inspect any divergent behavior. Freeze clock values, fixture data,
selectors, DOM visibility rule, settling horizons, source/runtime hashes and
assertion IDs before model dispatch. Preserve qualification failures and defer
unresolved cases before any outcomes are seen. These controls and interfaces
are a proposed instrument; no candidate is admitted merely by this document.
