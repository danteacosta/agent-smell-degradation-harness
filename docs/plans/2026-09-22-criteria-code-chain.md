# Requirement → criteria → browser behavior: exploratory successor

## Authorization and scope

User approved the proposed sequence (qualified independent behavioral tests,
criteria-to-code pilot, pre-outcome signals, research-wide fixes). Prior packets
remain immutable. This is a separate successor, not completion of missing PR66
votes. Main implementation starts from merged fb3b13d.

The first live case is TodoMVC New todo, from pinned public corpus PR66, target
page-load input focus. All selected criterion artifacts are already outcome-
exposed; case selection is retrospective feasibility selection, not held-out.
The new executable outputs are not yet observed. The application is a generated
standalone implementation of this source subsection, not the upstream TodoMVC
Vue implementation or the whole TodoMVC specification.

## Design and alternatives

Prefer actual browser behavior over a boolean abstraction: focus can be tested
before any user action. Defer RealWorld pure API abstractions and CaSS permission
predicates: interface conventions and repeated source obligations risk construct
changes/leakage. Other TodoMVC topics can follow after this instrument is qualified.

A public neutral interface requires one standalone HTML document, plain inline
JavaScript/CSS, one new-todo input identifiable by `.new-todo`, one list
`.todo-list` whose items are `li`, each with one visible `label` element. Start empty. No libraries,
network, persistence, assets or other features requested. This interface fixes
mechanics, not focus, trim, Enter, clearing or append behavior. It may still cue
familiar TodoMVC behavior; all arms share it and recovery is retained.

Routes:
- direct: each exact source A/B/C, 3 fresh replications × 2 code generators =18.
- criteria-only: all 18 planned artifacts for this source in PR66 (3 conditions ×
  2 criterion generators ×3 replicates), one completion from each of two code
  generators =36 planned. Invalid upstream artifacts remain missing slots.
No selection by coverage or output quality. Code generators are requested Luna
and Sol at low reasoning via official saved ChatGPT/Codex CLI; no API-key fallback.
Maximum54 observable calls, sequential dispatch, no repair/retry/resume. 180s per
call. Provider error stops subsequent dispatch; all missing slots retained.
No quota reset or additional purchase. Order is deterministically shuffled with
seed20260922, frozen before dispatch; independent sessions and no oracle feedback.

All code responses are collected before behavioral execution. The original
requirement, rubric, target identity, prior labels and sibling artifacts stay
outside criteria-route prompts. Direct-route prompts contain only common contract
and one variant. No staged plan is claimed: this pilot does not validate H2.
A later H2 study must compare its actual B3 vs B0 pre-final baselines, not merely
pre-final vs final evidence, with independent project-level evaluation.

## Acceptance contract (BDD)

1. Given reviewed references with autofocus and with imperative focus, when a
   fresh browser page loads, then target and all non-target tests pass; removing
   only focus fails the target and preserves all non-target passes. A separate
   non-target mutant is detected without changing target result.
2. Given any planned source/criteria slot, when prompts are frozen, then payloads
   contain only its allowed content and shared interface; hidden tests and source
   counterpart never enter criteria-only prompts. Invalid upstream remains explicit.
3. Given malformed, unavailable or rejected output, when collection/execution
   records it, then no repair or implicit retry occurs; planned denominators and
   hashes remain auditable; a prior output directory cannot be overwritten.
4. Given generated HTML, when executed, then it runs only in a fresh offline,
   non-root container with bounded resources, read-only input and dedicated output;
   screenshots and externally produced test results are captured. Host credentials
   and Docker socket are never mounted. Browser code cannot edit the trusted runner.
5. Given finalized evidence, when summarized, then target-only, non-target-only,
   mixed, pass, malformed, crash, timeout and unattempted outcomes remain distinct;
   nulls/recovery and all missingness are reported without H1/H2 confirmation.

## Modules and ownership

- `eval/fixtures/focus-chain/`: pinned browser runtime/package lock, trusted driver,
  independent oracle, shared inert shell, source-derived references/mutants.
- `eval/focus_chain_executor.py`: offline container adapter, result validation,
  exact assertion inventory and external return code checks, timeout cleanup.
- `scripts/focus_chain.py`: freeze/collect/analyze workflow reusing Codex provider
  and existing custody helpers; isolated successor packet, no modification of PR66.
- `tests/test_focus_chain.py`, `tests/test_focus_chain_executor.py`: public contracts,
  leakage, missingness, tamper/error handling; live reference/mutant qualification
  separately in actual browser.
- `docs/research/focus-chain-results-20260922.md`: source mapping, actual outcomes,
  screenshots, route/configuration denominators, limitations, delivery links.

Adapter is justified only for Docker/browser boundary; no strategy/factory layer
for this single case. Exact source/criteria bytes, executable/image IDs, runner
and oracle hashes are frozen before calls. Isolated runtime upgrade is separate
from frozen prior experiments.

## Behavioral oracle and analysis

Fresh context per scenario; fixed viewport. Target observation 500 ms after the page load event, before click/type/tab, requires the visible `.new-todo` input to be the
actual active element. Record active-element tag/class and native screenshot.
Non-target scenarios cover visible input above list, Enter creation and append
order, input clearing, trimming, empty and whitespace-only rejection. Keep
independent assertion IDs; no single full-output equality mixes targets.
Load and post-Enter observations use a 500 ms settling horizon. This timing is a declared harness convention, not a source-specified SLA. Label text is measured independently of outer item formatting; invisible labels cannot satisfy creation.
Generated application runs only in a browser, never as Node/host code.

Primary descriptive target-failure C−A within route/code-model; preserve original
criterion-model strata for mediated route. Repetitions do not create new source
units. Report counts/all planned denominators, unknown lower/upper bounds and
complete executable sensitivity; no p-value/population CI with one intent.
Route differences are not mediation estimates: information and representation
both change. Operational/test infrastructure failure is not requirement failure.
No label from source/criteria is used to choose or change hidden assertions.

## Execution plan and checks

- [x] Inspect current code, prior oracle warnings, source and finalized PR66.
- [x] Baseline52 focused tests pass.
- [x] Independently review this contract and source-to-oracle mapping.
- [ ] Write failing behavior tests; implement custody/runner/executor minimally.
- [ ] Pin browser dependencies and qualify references/mutants; test containment.
- [ ] Review implementation/security/SOLID and freeze hashes before live calls.
- [ ] Collect <=54 calls, execute saved artifacts once, audit receipts/results.
- [ ] Update repository/Drive/slides with actual results and native screenshots.
- [ ] Full applicable tests, build, exact-head CI; authorized merge only on green.

## External runtime evidence

Playwright Docker guidance: https://playwright.dev/docs/docker and
https://playwright.dev/docs/ci (consulted2026-09-22). Browser image and npm package
versions must match; Docker isolation is not proof against arbitrary hostile
browser exploits. Use separate non-root user, no network and constrained mounts.

Independent review accepted narrow source mapping and required explicit500 ms horizon and distinct interface/infrastructure errors. Both requirements are adopted before generation. Chromium sandbox is disabled within bounded non-root offline Docker; this is not a guarantee against browser exploits.

Presentation selection fixed before collection: illustrate the direct-route Luna repetition1 A/C screenshot pair regardless of outcome; if either is unavailable, report its absence rather than replacing it with a stronger-looking pair. All executable screenshots remain in the delivery packet.
