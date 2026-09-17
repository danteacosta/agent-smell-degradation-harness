# Repository-level E2E candidate screening

Date checked: 2026-09-16. Status: engineering screening only. No project below
is admitted to a provider-backed or confirmatory run.

## Experimental boundary

The repository lane tests a narrow causal chain: a controlled missing condition
in a requirement may change generated code and create a user-observable failure.
It does not claim that every smell causes a defect. Acceptance-criteria
generation remains the primary thesis task; repository-level code generation is
a secondary behavioral extension.

Tests must be generated or assembled once from the canonical complete
requirement, independently reviewed, frozen, and then executed unchanged on
every clean, paraphrase-control, and smelly arm. Generating a separate suite
from each arm is forbidden: the defective requirement could induce a defective
test suite that omits the same condition and falsely passes the generated code.
LLM judges may assess test clarity or explain failures, but they are not the
behavioral ground truth.

Each admitted case needs a source revision, a pre-implementation base commit, a
known-good implementation commit, exact implementation paths, an observable
interaction, a complete requirement, a distinct meaning-preserving rewrite
control, a smelly treatment, one shared scaffold and oracle hash, and a targeted
mutant that the oracle kills. The rewrite control estimates ordinary wording
sensitivity; it cannot prove that all non-smell edits are harmless.
The gold pass and mutant failure must each be bound to an execution-receipt
hash. Independent reviews of the requirement-to-code mapping, manipulation,
oracle, and processing rights require reviewer identities and evidence hashes.

## Four screened repositories

| Candidate | Verified live evidence | Candidate observable contract | Main unresolved work | Screening decision |
| --- | --- | --- | --- | --- |
| [TodoMVC](https://github.com/tastejs/todomvc) | `app-spec.md` specifies that Escape leaves edit mode and discards changes; `cypress/e2e/spec.cy.js` is a browser-level suite shared across implementations. Repository license: MIT. | Create a todo, enter edit mode, replace its title, press Escape, and observe in the same browser session that edit mode closes and the original title remains. A missing “discard changes” condition is the candidate intervention. | Independently review the requirement-to-Vue mapping, the narrow Escape-handler mutation, and the frozen Cypress assertion; then reproduce gold-pass and mutant-kill receipts in the qualified environment. Vue is intentionally in-memory in the selected revision, so reload is not part of this contract. | Priority 1; not admitted. |
| [RealWorld](https://github.com/realworld-apps/realworld) | The organization maintains shared specifications and Playwright E2E tests; `specs/e2e/articles.spec.ts` exercises Favorite and Unfavorite through the UI. Repository license: MIT, with a stated exclusion for third-party framework logos. | Favorite another user's article, observe Unfavorite/count state, then reverse it and verify persistence. | Choose one frontend/backend implementation pair, bind exact commits, remove dependence on demo data, and isolate deterministic state. | Priority 2; not admitted. |
| [StrictDoc](https://github.com/strictdoc-project/strictdoc) | `SDOC-SRS-110` requires UID, version, classification, and authors; the requirement is linked from `strictdoc/backend/sdoc/models/document_config.py`. Repository license: Apache-2.0. | Edit document metadata, save/reload, export HTML, and observe the selected field in both editor and export. | Find a true pre-feature base commit; define one field-level intervention; freeze a black-box test that does not inspect implementation-only state. | Priority 1; not admitted. |
| [CaSS](https://github.com/cassproject/CASS) | `REQUIREMENTS.md` and `ENVIRONMENT.md` describe browser/API modes, including disabled editor/adapters while the core API remains functional. The SRS says it was derived from code, tests, OpenAPI, and documentation. Repository license: Apache-2.0. | Start in a disabled component mode; observe disabled surface behavior and unchanged core API behavior. | Retrospective requirement provenance weakens causal interpretation; select a natural source revision and exact implementation commit before considering admission. | Secondary/engineering replication; not admitted. |

The first pilot should use one independently approved case per project, not four
cases merely because four interfaces exist. With four projects, four arms
(complete, meaning-preserving paraphrase, smelly, and repeated complete
control), three stochastic replications, and two qualified generation models,
the candidate budget is 96 generation episodes. This is a planning calculation,
not a registered sample size or authorization to spend.

The license files make controlled local modification technically plausible, but
they do not complete the study's rights and governance review. The admission
manifest therefore still requires an explicit `rights_review: approved` decision.

The causal contrast is smelly versus complete. Rewrite-control versus complete
is the wording-instability contrast, and smelly versus rewrite-control is a
sensitivity analysis. All arms start from the same scaffold and use the same
frozen oracle. A difference observed only against complete, but not against the
rewrite control, is not sufficient evidence of a smell-specific effect.

## Admission command

Create a private manifest conforming to `repository-e2e-case/v1`, then run:

```bash
python -m eval.repository_case_admission --manifest /absolute/private/case.json
```

Exit code 0 means only that the evidence bindings and declared approvals are
complete. Exit code 2 means the manifest is structurally valid but blocked.
Malformed, variant-specific, unbound, path-unsafe, or receipt-free evidence
fails closed.
Passing this gate does not establish semantic validity or confirm H1/H2.

## Immediate selection order

1. TodoMVC Escape editing, because the behavior is concise and directly visible.
2. StrictDoc metadata, if a pre-feature commit can be recovered without leakage.
3. RealWorld Favorite/Unfavorite after making backend state deterministic.
4. CaSS only as a replication of the method, with retrospective provenance
   reported as a validity limitation.

The [TodoMVC screening dossier](todomvc-edit-escape-screening-20260917.md)
binds the first candidate to exact requirement, implementation, test and license
revisions. It also records why the broad historical base-to-gold diff is
provenance rather than a causal contrast and why the case remains blocked.
