# Native UI sources for the next H1 expansion

Question: which independently sourced UI obligations can diversify the E2E
sample beyond TodoMVC and StrictDoc without wrapping API-only requirements?
Screened on 2026-09-23. These are source candidates, not admitted cases, frozen
prompts or generated-code results. They do not change the conditional 54-slot
subset recorded in PR71.

## RealWorld: author-specific controls

The RealWorld frontend routing specification describes an article view whose
delete control is restricted to its author, and a separate equivalent rule for
comment authors. This is a native UI obligation, distinct from the earlier
API-only follow/list/comment candidates. Use one author-control case initially;
article and comment variations share semantics and should not be represented
as unrelated independent evidence.

Proposed contract: given the same article and controlled user fixture, render
the author and non-author views in separate browser contexts. Then inspect
whether a usable delete control is available only in the author view; preserve
article content and route as non-target assertions. Omit only the author
restriction in C, retain the action and page, and review whether the common
identity fixture leaks the restriction. Browser evidence measures affordance
visibility, not backend authorization security or whole-project compliance.

Source: RealWorld maintainers, frontend `routing.md`, revision
`ebbcdeb8d55b42a3a613c787560498b8ef10003f`.
[Immutable routing specification](https://github.com/realworld-apps/realworld/blob/ebbcdeb8d55b42a3a613c787560498b8ef10003f/docs/src/content/docs/specifications/frontend/routing.md).
The pinned repository LICENSE declares MIT (Thinkster 2021; c4ffein 2026),
with a separate exclusion for framework logos, which this candidate does not
use. The frontend test documentation names a shared selector contract and
Playwright suite. Those tests require separate review and pinned retrieval;
their existence does not qualify our instrument. RealWorld is already exposed
in this research; the new UI source is not a held-out project.

## Kanboard: closing tasks and subtasks

The Kanboard user guide describes closing a task through a board or task-view
menu. Closed tasks leave the board and remain accessible through closed-task
filter/search. Closing also completes unfinished subtasks. This supports a
candidate omission of the subtask consequence while retaining closing,
board removal and discoverability as non-target obligations.

Proposed contract: given a task with Todo, In progress and Done subtasks plus
an unrelated open task, close it through the UI, inspect the closed view, and
observe the subtask statuses. Compare unchanged unrelated tasks, the closed
parent, and board/filter results separately. Do not pass the subtask target
when the closed view cannot be reached. Freeze neutral status selectors and
screen fixtures without prescribing the target transition. Independent review
must ensure that the selected complete subsection and common interface do not
remove needed context or silently duplicate the target from another source.

Source: Frédéric Guillot / Kanboard contributors, `content/en/v1/user/tasks.md`,
Closing Tasks subsection, revision `4455fd04fb48ed42817fc99402d4c1fb3bde1c0d`.
[Immutable user guide](https://github.com/kanboard/documentation/blob/4455fd04fb48ed42817fc99402d4c1fb3bde1c0d/content/en/v1/user/tasks.md).
The pinned documentation LICENSE declares MIT (Frédéric Guillot 2014–2023).
The separate subtask guide corroborates the closing consequence; it must not
be supplied unchanged to C if it reintroduces the omitted obligation.
The initial discovery also used the [rendered official guide](https://docs.kanboard.org/v1/user/tasks/).
Prior research exposure has not yet been exhaustively screened; do not label
this a held-out project.

## Decision and next use

Both sources pass initial UI/provenance screening. Neither has a qualified
oracle, reviewed omission/rewrite prompts, a source-exposure audit or an
admission receipt. Retain the original 12-case corpus unchanged. Prepare them
as new separately identified cases only after those checks. If eventually
admitted, they could add two project strata to the current two-project UI
subset; this does not meet the original 12-requirement target by itself and
does not establish statistical adequacy or H1/H2.

## Source custody

Downloaded immutable bytes and full license notices are retained in
`.private-research-evidence/e2e-source-screening-20260923` with the following
SHA-256 identifiers. Only the routing and closing-task sources inform the
candidate decisions; templates are retained as context, not as requirements
or generation input. No public API was exercised and no model was called.

- `kanboard/documentation:LICENSE`: `b14398501e47b08042d57b3ef7994cb2aab8d353a87d928a2395b7aea7c8ca2a`.
- `kanboard/documentation:content/en/v1/user/tasks.md`: `281c39c6e4c5a9c071d28bf01d08d2544929942977eeff4ae53ce0716510f081`.
- `kanboard/documentation:content/en/v1/user/subtasks.md`: `b5e6c82c05b30daae6e82052b27bc774c919e04bb503deff58f1167451a43291`.
- `realworld-apps/realworld:LICENSE`: `a999311c4ccfecf18b7c7beb7a7a31682bb009839ab3827164fa2f8c333fc9dd`.
- `realworld-apps/realworld:docs/src/content/docs/specifications/frontend/routing.md`: `65fbd975a3ab2021057b1c1944cf66418aa846039e51b166d2a98eb29e7169fb`.
- `realworld-apps/realworld:docs/src/content/docs/specifications/frontend/templates.md`: `e7d2524641c57576aef8f9f02009f404a68f09c92daf12bdb5ed84e808a860ee`.
- `realworld-apps/realworld:docs/src/content/docs/specifications/frontend/tests.md`: `d7ebebefc62a8f63df16bcc5c02acca274105f005b1193aaf309a90484aeb109`.
