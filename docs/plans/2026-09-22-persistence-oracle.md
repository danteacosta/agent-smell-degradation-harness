# TodoMVC persistence browser oracle

Acceptance contract: at one fixed origin, create a todo, enter edit mode by
double-clicking its label, leave the editor open, and open a second page in the
same browser context. A source-conformant implementation restores the todo and
title without visible editing. A target mutant restores the editor and fails
only `editing_not_restored`. Independent scenarios check todo reload, completed
state reload, and use of the `todos-vanilla` localStorage key. A missing todo or
unavailable editing interface makes the target not evaluable, not a target pass
or failure. The test observes browser state and does not claim that no edit
related byte was ever serialized.

The shared generator interface requires a standalone vanilla-JavaScript page,
`input.new-todo`, `ul.todo-list > li` records with a checkbox and label, and
double-click label to edit. It does not prescribe the saved state or restore
algorithm. The browser runner owns a fresh context per scenario and two pages
in the target context. It runs generated HTML only in offline, resource-bounded
Docker. The Python adapter checks report IDs, statuses, return code, app hash,
and screenshots before classification. There is no model dispatch in this step.

BDD qualification: given an implementation omitting edit state, storing a false
edit flag, or encoding the stored value, when the browser runs, all assertions
pass. Given an implementation restoring active editing, only the target fails.
Given a no-reload implementation, the todo and completion checks fail and the
target is unknown. Given unavailable edit entry, the target is likewise unknown.
Given completion loss, only that invariant fails. Review
visual evidence and exact source mapping before cohort admission. Only after
an immutable image, source hashes, leakage review, and sufficient quota should
the case enter a once-only randomized schedule.
