# Next E2E expansion block

The current program has six represented projects, five new obligations from
the screened block, and a completed TodoMVC bridge. Six new obligations remain:
TodoMVC Clear completed visibility, RealWorld comment Delete visibility,
Kanboard close-task board visibility, Paperless nested-tag propagation,
Nextcloud restore-name conflict, and Nextcloud permanent delete. Existing
instrument reviews deferred four of these; their votes and failed gates must
remain intact. The next case is Paperless nested-tag propagation, accepted by
three reviewers at source screening and not yet built as a browser oracle.

## ATDD contract for Paperless nested tags

Given a document with no tags and a source-grounded Child→Parent hierarchy,
when the user assigns Child in the document UI, both Child and Parent must be
visible on that document after reload. A and B express both obligations; C
deletes only automatic parent propagation. The document, hierarchy, Child
assignment, unrelated tag absence, and reload are controls. The page must not
implement propagation for the model. A failed interface, invalid output,
console error, or malformed report is not scored as a target defect.

The browser oracle uses two distinct Child/Parent fixtures, a fixed isolated
Chromium image, and authored reference, alternative, target-mutant, non-target,
and interface/error controls. Independent reviewers assess source mapping,
A/B equivalence, leakage, and target/non-target separation before the freeze.
Only a unanimous ACCEPT admits generation. The freeze binds source, license,
arms, prompts, schedule, provider executable, oracle and image. Run 18 slots
(A/B/C × two model configurations × three repetitions) once with the Codex
subscription, generating every HTML before browser execution. Preserve all
categories and images; report this as one exploratory requirement stratum.

No new design pattern is needed. The fixture owns presentation and exact tag
persistence, the generated handler owns assignment policy, and the browser
runner owns observation. This mirrors existing bounded E2E pilots without
coupling classification to generated implementation details. The main risk is
accidentally implementing parent propagation in the common fixture; authored
mutants and independent review specifically test that boundary.

Completion requires a qualified oracle, prospective freeze, complete
single-attempt collection, inventory checks, local tests and code review, and
an updated evidence matrix. H1 ordinal severity and H2 warning prediction
remain separate outcomes.

## ATDD contract for RealWorld comment Delete visibility

Given one source-grounded article comment by user A, when A opens the article
in a fresh authenticated browser context, the comment's Delete button is
visible. When a different authenticated user B opens the same article in a
separate context, the comment remains visible but its Delete button is not.
A and B express that author-only visibility policy; C omits only the policy.
The common page may render the comment and viewer identity as fixture data,
but must neither add nor hide the Delete button. The generated handler owns
the button policy. Two fixtures with distinct article, comment and user IDs
protect against a single hard-coded identity. Missing comments or identity,
duplicate controls, exceptions, and malformed observations are non-evaluable
or non-target failures rather than evidence of an author-only defect.

The observable contract comes from the RealWorld frontend routing
specification, which explicitly says the Delete comment button is shown only
to the comment's author. The same qualification, independent review, freeze,
single-attempt collection, and custody gates apply. No new pattern is needed:
the page provides state, the generated code decides visibility, and the runner
observes the UI in isolated contexts.

## Kanboard closed-task filter replacement, before generation

The prior close-task candidate combined status mutation, board hiding and
closed-filter retrieval and failed unanimous instrument review. Its votes and
packet remain unchanged. This replacement narrows the same source excerpt to
one browser obligation: with an already closed task in the data, selecting
**Closed tasks** from the filter dropdown shows it. The board's initial open
task view is a control. A/B require the board and closed-filter views; C
deletes only the closed-filter rule. Two fixtures use different task identities
and titles. The common page provides tasks and rendering but no filter policy.
Target failure is a missing closed task after selecting the filter; interface
absence, malformed observations, and broken board controls are separate.
The source expressly names the Closed tasks filter, so no status-changing
action or inferred board persistence is scored. This replacement requires a
new qualification and independent instrument review before any generation.

The first Kanboard closed-filter lot exposed an incomplete data contract: the
page did not declare that task status is the string `open` or `closed`, and
many generations assumed a boolean `closed` field. That original lot remains
an instrument failure. A successor declares the record shape in the common
page, was requalified and independently accepted before new generations.

## Nextcloud conflict redesign candidate

The prior three restore-name-conflict instruments were deferred. A genuinely
new design will represent an original directory as structured data with path
and writability; active and deleted file records carry paths. The browser
first observes an existing file with the target name and another active file
whose name could collide with a naïve rename, then clicks Restore. After
reload in the original directory, it should see the original and restored IDs
with distinct names, and the restored name must be distinct from *every*
active name in that directory. The original directory path and writable state
must be visible before action and the restored path must be visible after.
The generated handler owns restoration, destination and naming. The common
page only persists supplied records and renders the current directory.
Missing restore, corruption of unrelated files, wrong destination and
unavailable action are controls or interface errors, not target-only defects.
This design needs a fresh source-to-endpoint review and qualification before
any generation; it does not amend the three earlier failed reviews.

The new path-aware v4 instrument passed 10/10 authored browser controls and
three independent ACCEPT reviews. Its first frozen 18-generation lot exposed
a collector screenshot-name mismatch; all original categories remain
`browser_error` and a separate diagnostic read is labeled accordingly. A
newly frozen collector successor generated 18 fresh HTMLs and produced A/B
12/12 passes and C 6/6 target-only failures. This is the eighth new
obligation in the block. Three remain: TodoMVC Clear completed, RealWorld
comment Delete visibility, and Nextcloud permanent deletion. The review-defer
records for the first two and the original Nextcloud candidate remain intact.
