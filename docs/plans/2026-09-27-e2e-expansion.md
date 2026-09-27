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
