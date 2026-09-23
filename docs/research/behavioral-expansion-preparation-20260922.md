# Behavioral expansion: preparation, not a new result

Update, 2026-09-23: the primary endpoint now requires generated UI observed in
browser E2E. The mixed API/browser 144-slot proposal below is historical and
superseded for that cohort by the [E2E-first plan](../plans/2026-09-23-e2e-first-h1.md).
The new screening currently retains three candidate intents in two projects;
it does not claim four-project diversity or authorize generation before freeze.

The user approved expanding the behavioral comparison on 2026-09-22. This
checkpoint screens all 12 source requirements from the completed criteria pilot.
Eight are candidates across four projects; four are deferred with reasons in
[the candidate register](../../data/behavioral-expansion/candidates.json).
No new generation, qualified oracle, frozen collection or outcome is claimed.

All 12 exact excerpts, single-span omissions, source bytes, license bytes and
available NOTICE hashes were rechecked against the committed corpus. These are
already exposed sources: every intent participated in the criteria pilot, and
TodoMVC New todo additionally participated in the completed browser pilot.
“New” means a new behavioral task for a previously unexecuted intent, not an
unseen requirement, unseen project or independent confirmatory sample.

## Candidate contracts

The machine-readable register contains Given/When/Then scenarios, non-target
invariants, authored qualification controls and unresolved interfaces for each
candidate. Proposed selection is based on testability, not previous panel labels
or predicted omission effects. The analyst has seen aggregate prior outcomes;
this is not outcome-blind source selection.

| Candidate | Layer | Target behavior | Admission issue to resolve |
| --- | --- | --- | --- |
| StrictDoc SRS-97 | Browser | Show generation date | Neutral fixture clock; accept equivalent date formats |
| TodoMVC Mark all | Browser | Clear master checkbox after Clear completed | Empty-list observation must not require visible geometry |
| TodoMVC Persistence | Browser | Do not restore editing mode | Fix observable editing/reload contract without leaking target |
| RealWorld List Articles | Integration/API | Correct offset/default-zero pagination | Pin linked response schema; freeze ordering fixtures |
| RealWorld Follow user | Integration/API | Follow without extra required parameters | Pin Profile/auth contract; optional fields remain allowed |
| RealWorld Add comment | Integration/API | Reject unauthenticated creation | Pin auth/Comment contract; assert no storage side effect |
| CaSS IDATA-007 | Integration/API | Preserve numeric confidence | Support is not mandatory presence or an invented numeric range |
| CaSS BATCH-002 | Integration/API | Check permissions for every object | Pin KBAC; resolve atomic versus partial success before testing |

Deferred: StrictDoc SRS-47 is a development-process contract, SRS-157 needs an
independent definition of visualization/coverage, TodoMVC New todo is already
behaviorally measured, and CaSS DATA-011 has a broad uniform-search claim that a
few examples would not adequately operationalize. No deferred case is labeled
as a null effect, a failure or an inconvenient result.

The CaSS batch oracle must also accept an all-permitted valid batch, store every
object and return the correct count. A reject-all implementation must fail this
non-target control; otherwise refusing every request could falsely pass the
permission check. This does not decide mixed-batch atomicity.

## Chosen design and alternatives

Use direct requirement-to-code generation first. Reusing the criteria-only route
would mix upstream loss with code-generation behavior; rebuilding full upstream
applications would improve ecological realism but add scaffolding and integration
confounds. Bounded executable replicas provide a tractable intermediate study,
provided they are explicitly reported as replicas and not upstream application
compliance. API/domain obligations use integration tests, not decorative browser
E2E. UI mechanisms use real browser interactions.

If all eight candidates qualify: 8 intents × A/B/C × 2 generator configurations
× 3 repetitions = **144 planned generations**. A/B/C remain the existing exact
complete excerpt, reviewed rewrite and single-span omission. Candidate allocation
is unequal (StrictDoc 1, TodoMVC 2, RealWorld 3, CaSS 2); report that explicitly.
Two configurations from one provider are not independent providers. All three
conditions receive identical auxiliary interface/schema material. Audit that
material for reintroduction of the deleted obligation, especially authentication,
confidence and permission checks. If leakage cannot be avoided, defer the case
before freeze and publish the reason.

Freeze the final eligible set, model aliases/reasoning, prompt bytes, public-only
inputs, runtime image, source dependencies, fixtures, oracle, qualification
results, observation windows and randomized schedule before generation. Proposed
schedule seed: 20260922; opaque IDs and fresh isolated contexts for every slot.
The current candidate register is **not** that freeze. Source transformations
remain assistant-reviewed; no human or expert approval is implied.

## Acceptance and failure contract

1. Given each reference implementation and an independently authored alternative,
   the oracle accepts both; it rejects a target-only mutant with the expected
   assertion ID and distinguishes non-target mutants. Qualification failures
   stop admission before any generation. Authored controls qualify the instrument,
   not a smell effect. Alternative controls must exercise permitted variation.
2. Given any A/B/C prompt, auxiliary context and tool access are identical and do
   not expose the full source, target marker, hidden tests or another condition.
   Required interface failures are reported separately from source violations.
3. Given a frozen schedule, dispatch once per slot through the official Codex
   subscription adapter, without API-key fallback, repair or replacement. Keep
   provider errors, invalid output, unattempted positions and timeouts. A started
   packet is immutable and non-resumable; use a new version for a later collection.
4. Given collected artifacts, finish generation before examining behavioral
   outcomes. Execute untrusted code in bounded isolated environments without
   network, host credentials or socket access. Reuse existing custody/isolation
   contracts, with explicit platform limitations; do not claim Docker proves
   protection against every browser/runtime escape.
5. Given results, independent recomputation must reproduce every label, planned
   denominator, contrast and receipt. Screenshots illustrate browser observations;
   API transcripts/state assertions provide evidence for API cases. Both passing
   and failing outputs remain in the packet.

## Analysis to freeze before dispatch

Primary endpoint: source-relative violation of the deleted target obligation,
not all-tests-pass and not obedience to the shortened C prompt. Report target
failure separately from non-target failure and artifact/interface invalidity.
For each intent/model, report C−A and B−A failure-rate differences, all 3 planned
positions per arm, valid counts and worst-case missingness bounds. A/B regressions
are retained, never a reason to discard an intent after generation.

Report project-specific results and an equal-project-weighted descriptive
summary (equal-intent weighting within each project), with an equal-intent-weighted
sensitivity because candidate counts differ by project. Preserve per-model
results. Do not pool the previous focus pilot into the primary expansion estimate.
Repeated generations are nested within intent/project, not independent source
samples. Four purposively selected projects do not support a precise population
confidence interval. Missingness bounds are not confidence intervals. Larger
prospective project sampling and an independently specified precision analysis
remain necessary for general H1 inference; H2 detector evaluation is separate.

## Implementation boundary and remaining work

Reuse source/custody utilities and the provider adapter; add per-case behavioral
oracles at the layer justified above. Keep collection, sandbox execution and
analysis separate. An adapter is warranted only for differing browser/API entry
contracts; do not generalize the existing focus oracle by renaming selectors.
No executable runner changes are included in this preparation checkpoint.

Next: resolve linked contracts from pinned public sources, author fixtures and
controls, qualify each candidate, perform independent semantic and leakage review,
then freeze the eligible cohort and exact budget. Any reduction from eight must
be recorded before outcomes with its reason and revised count, not silently
substituted with easier or already positive examples.

The account check at this checkpoint reported 99% of the weekly Codex limit used.
No new model collection was started. This is a temporary resource constraint,
not a scientific exclusion, permission to consume an API key, or a claim that
remaining quota can be converted into a known number of calls. Recheck capacity
before dispatch; do not purchase/reset credits or automatically resume a packet.
