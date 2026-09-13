# Source-to-oracle revision candidate v1

Status: **pending independent review**, 2026-09-12. This proposal advances the
[historical audit](behavior-oracle-review-20260911.md) without changing the twelve
legacy pair files, their tests, reference implementations or recorded outcomes.
It grants no provider, corpus, rights or confirmatory approval.

## What can be established now

The executable [partial-oracle candidate](../../data/oracle_review/candidate-v1.json)
retains only selected positive/prohibitory obligations in four cases and marks
other historical test points `unspecified`. This is an assistant's proposed
interpretation, not a human-reviewed reference standard. The retained predicates
are narrower than the full source requirements.

Run the offline comparison with:

```bash
python -m label_plane.oracle_review
python -m label_plane.oracle_review --output new-reference-audit.json
```

The optional output must not exist. The CLI accepts no provider or arbitrary code
input. Source bytes must match an explicit trusted historical inventory, not just
a hash supplied by the candidate. It validates all cases before executing either
checked-in reference. Both variants receive the same candidate oracle hash and
retained test set. These are constructed implementations, not stochastic LLM runs.

The [reproducible report](partial-oracle-reference-audit-v1.json) compares eight
references on four selected cases. All four historical oracles distinguish their
constructed clean and defective references. Under the partial candidates, the
contrast remains for NFR-002 and PEERING-001 and disappears for GAMMA-002 and
ERTMS-002. The latter results expose dependence on unsupported expectations;
they do not establish a null effect of smells or a population error rate.

`compatible_on_checked_points` means only no violation at the retained points.
Unspecified points are never counted as correct negatives. Execution errors,
invalid results and timeouts yield an incomplete comparison, not zero violations.
The utility is entirely in the label plane, disconnected from the live runner and
T1–T3 features. Public reference fixtures remain unsuitable for contamination-free
confirmatory evaluation.

## Review packet covering all twelve cases

Each row is a proposed next contract, not an approved corpus revision. Reviewers
should work from the pinned original source plus its surrounding specification.
Retain source modality (`should`, capability, prohibition) unless an explicit
scope decision justifies a change. Record every added assumption separately.

| Case | Proposed repair / executable obligation | Tests and unresolved decision |
| --- | --- | --- |
| CCTNS-001 | Preserve the source's `should` and opt-in wording. Define what an action on an alert means before mapping it to an event. | Review all four opt-in/action combinations. The current source excerpt alone does not settle every no-action or opt-out outcome; do not silently impose a closed-world policy. |
| CCTNS-002 | Replace the supplied `immutable` flag with an audit-store transition contract. Creation records actor, timestamp, action and parameters; attempts to update/delete an existing entry must preserve its content. | Cover ordinary user and administrator attempts, repeated operations, and allowed copying with identical content. Specify initial state, critical-entity scope and what counts as deletion. This tests a storage contract, not security against every attack. |
| ERTMS-001 | Preserve the capability to prevent unauthorized movement under RBC supervision. A capability is not equivalent to unconditional automatic braking. | Define the prevention command/actor, success observation, operating state and other supervision policies. All three existing action-only expectations need review before a behavioral oracle is possible. |
| ERTMS-002 | Retain brake initiation when acknowledgement is required and missing. Mark outside-antecedent behavior unspecified unless the full specification rules it out. | Partial candidate retains `required_ack_missing`. To test unnecessary braking, obtain an explicit prohibition or scoped rule-only contract first. Otherwise the current deletion treatment is not discriminated by this partial oracle. |
| FUN-001 | Preserve non-initiator listening-only permission. Make the defective wording a minimal removal of the restriction instead of a broad rewrite. | Distinguish permission to speak from actual audio production. Define call membership and initiator state. Review whether the retained wording still implies the deleted restriction. |
| FUN-002 | Preserve `up to six different parties` and separate capacity support from admission policy. Remove the ungrounded `one through` rewrite. | Review behavior for 0, 1, 2, 6 and 7 parties, the meaning of distinct parties and whether the source really mandates rejection of a seventh party. Do not manufacture a seventh-party prohibition solely to obtain a contrast. |
| GAMMA-001 | Model USB insertion followed by an observed operational-state transition with a monotonic clock. A supplied elapsed-time predicate is not deployment performance. | Review capability versus every-run deadline, start/end events, timer resolution and strict `<60` boundary. Non-USB execution lies outside this excerpt. Use a simulated clock for instrument tests; real performance needs deployment evidence. |
| GAMMA-002 | Candidate clean wording should preserve the original capacity obligation rather than introduce `at most`. A quantitative omission can be drafted only after defining the capacity measurement. | Partial candidate retains the 1000-user point and leaves 1001/0 unspecified. A Boolean function does not demonstrate actual concurrency capacity; load, duration, acceptable service and environment remain to be specified. |
| NFR-001 | Replace stateless `elapsed>=60` with a sequence of refresh events and an explicit clock/reset model. Remove the unreviewed addition `exactly`. | Review cadence, allowed jitter, first refresh, observation duration, missed cycles and extra refreshes. Until these are explicit, do not infer that an extra refresh is forbidden. |
| NFR-002 | Retain unauthorized-access denial. Keep recognition of user category as a separate obligation from granting permission. | Partial candidate leaves authorized-user admission unspecified. Add a state transition showing whether access actually occurred; review how authentication is established and other denial policies. |
| PEERING-001 | Retain rejection of a request known to be malicious. Separate detection correctness from the response to a detection. | Partial candidate leaves benign admission unspecified. Define the malicious-request reference and whether rejection must occur before side effects; a supplied flag does not evaluate detection. |
| PEERING-002 | Replace category-declaration booleans with actual request instances and observable handling outcomes. | Define `considered`, anticipated/unanticipated membership and permitted handling. The source does not by itself require accepting every request. No approved behavior oracle can be inferred from the two flags. |

## Finite next steps for independent review

### Four-case source recheck and proposed dispositions

Re-fetched all four ARTA source files at commit
`493297655cd653f8ebc797ef5c3c7ee2f736ab4c` and inspected the selected records
and their neighboring records. These recommendations are assistant-authored;
they are not independent approval or a review of the complete original standards.
Source links and record identifiers remain in each historical pair's `source`.

| Case | Recommended disposition before a live behavioral pilot | Concrete decision for the reviewer |
| --- | --- | --- |
| GAMMA-002 | Defer the current Boolean abstraction. Capacity is not a maximum admission policy, and checking an input count does not measure concurrent service. | Specify workload, service success and observation interval before drafting a capacity experiment. Do not approve the historical `at most` rewrite. |
| ERTMS-002 | Keep as an identifiability warning; defer a treatment-effect comparison under the current partial oracle. | Obtain a source-backed prohibition on unnecessary braking if that is the intended outcome. Otherwise preserve the outside-antecedent region as unspecified. |
| NFR-002 | Revise the candidate pair before admission. The historical clean text drops classification while the defective text retains it, so this is not a single deletion contrast. | Keep classification identical in both prompts and delete only enforcement; review the abstract access-decision scope independently. |
| PEERING-001 | Candidate for a narrowly scoped response-policy pilot, subject to review and rights. | Agree that maliciousness is an externally supplied classification and only the required rejection response is assessed. Do not claim detection quality or require benign admission. |

Proposed NFR clean wording: `The product shall distinguish authorized from
unauthorized users on every access attempt. The product shall deny access to
unauthorized users.` Proposed defective wording: `The product shall distinguish
authorized from unauthorized users on every access attempt.` The first sentence
is identical; only the second is removed. This is a draft for a new version,
not a change to the frozen historical pair. An access-decision-only abstraction
must explicitly exclude evaluation of classification quality in both arms.

For the NFR candidate, unauthorized access must yield denial; authorized access
remains unspecified by the excerpt. For PEERING, malicious input must yield
rejection; benign acceptance remains unspecified. Returned policy tokens are
evidence about that decision function only, not proof that a deployed system
prevented side effects. These scope limits must travel with any pilot result.

These dispositions are based on specification/abstraction suitability, not
selection for a desired observed effect. Retain all four records and decisions.
No candidate is admitted by this document; no prior reference result is relabeled.

1. Decide source meaning, permissible abstraction and the expected outputs **before**
   inspecting any newly generated provider output. Record retained obligations,
   unknown regions and assumptions separately. An uncertainty decision is valid.
2. Review the clean rewrite and minimal defective variant independently of the
   expected experimental contrast. Exclude cases where a valid contrast cannot
   be identified; retain the exclusion reason rather than tuning the oracle.
3. Create a new corpus/oracle version, source/rationale links, per-constraint tests
   and a frozen manifest. Preserve these legacy artifacts for comparison. Resolve
   rights and the private/public evidence boundary before external processing.
4. Qualify the real execution sandbox and provider configuration using original
   development controls; record rejection, timeout and accounting separately.
   Then collect the planned paired repetitions with one fixed oracle per pair.
   No provider credentials were found in this workspace during the prior check;
   no live qualification is claimed here.

This packet reduces preparation work for scarce reviewers; it cannot replace
their independent decisions or the separate H1/H2 annotation protocol.

## Execution readiness

`python -m eval.behavior_runtime_smoke` exercises the actual subprocess executor
with an original correct increment, an incorrect increment, a forbidden import,
a division-by-zero exception and a bounded over-budget loop control (250-ms
wall-clock timeout, preceding the fixed one-second CPU limit). Version 2 requires all five distinct statuses; execution
failure must not be conflated with a semantic violation.
It exits nonzero if expected outcomes are not observed and explicitly denies
provider/oracle/confirmatory qualification. The CI evaluation workflow runs it
after pytest. A green smoke is a limited execution-path check, not a hostile-code
isolation proof or a performance measurement.

The [local root run](behavior-runtime-smoke-root-v1.json) correctly refused both
executable controls with `unsafe_not_run` / `root_user`; static rejection worked.
The [non-root setup attempt](behavior-runtime-smoke-nonroot-v1.json) was denied by
the environment before any controls ran. No safety condition was bypassed.
The version-1 CI smoke passed its three controls at commit `401ebfacd340e1a81257dcf0587fe8ecd448e017`,
alongside 1281 tests and nine subtests. Version 2 adds exception and timeout
qualification. Provider configuration and source/oracle review remain separate
dependencies even if it passes. The two local JSON records above remain historical
version-1 evidence and are not rewritten as version-2 results.

## Shortest path to a defensible first run

The proposed NFR and PEERING single-deletion drafts are now machine-readable in
`data/oracle_review/nfr-single-deletion-candidate-v1.json` and
`data/oracle_review/peering-single-deletion-candidate-v1.json`. Both retain their
shared detection/classification sentence and remove only the response sentence.
They remain unapproved drafts outside the live corpus loader.

Prepare separate text and review files using an existing private parent folder:

```bash
python -m label_plane.draft_packets --output /path/to/private/new-drafts
```

The command creates a new directory exclusively: four requirement text files
under `generation/`, two full candidate files plus a hash receipt under `review/`.
The latter directory contains oracle information and must never be sent to a
generator. Each generation text includes the same interface scaffold within its
pair: one externally supplied Boolean classification, a pure `evaluate` function,
two decision tokens and a JSON `source_code` response. No expected input/output
mapping, test input, source identifier or mutation description is included.
The resulting prompts differ by exactly the removed requirement sentence. The
shared scaffold and abstraction still require review; their presence does not
establish that the prompts preserve the full source requirement.
The export is reproducible preparation, not preregistration, semantic review,
rights clearance or corpus admission. The receipt explicitly denies live and
confirmatory eligibility. The names of the variants are visible in this reviewer
packet; it is not a blinded outcome-annotation packet.

The receipt also enumerates all four possible decision tables over each Boolean
interface. Both current partial oracles admit two tables, including an unconditional
`deny` (NFR) or `reject` (PEERING) response. This is an explicit scope control:
compatibility on the scored condition does not validate the full program or its
behavior on the unspecified input. Do not add an unsupported admission expectation
merely to make this control fail. The exporter rejects overlapping scored/unscored
inputs, non-Boolean inputs, wrong arguments, illegal decisions and mismatched
constraint IDs before creating output. These are offline finite-table checks,
not generated-model observations or a semantic approval.

Each review JSON also contains an `executor_test_draft`: the scored point is
translated into the existing executor's `args`/`kwargs`/`expected` format with its
constraint ID intact. Unspecified points remain outside `hidden_tests`. Literal
allow/deny/reject controls verify format compatibility through the trusted-fixture
test path. This is not qualification of generated code or a provider, and the
draft tests are not registered with any live loader.

This is an execution order, not another approval framework. Review all four
partial candidates before selecting the first behavioral case; do not select
only NFR-002/PEERING-001 because their constructed references retain a contrast.
For each candidate, an independent reviewer can accept the stated abstraction,
correct it with source support, or exclude it as unidentifiable. Preserve all
four decisions, including null contrasts and exclusions. This small convenience
subset remains exploratory and cannot estimate the corpus-wide effect.

The reviewer needs only the pinned source/context, clean/defective wording,
proposed obligation, test expectations and assumptions in the packet above.
They should not receive newly generated outputs or expected treatment effects
when making the decision. Reviewing an oracle is a separate task from producing
the independent human outcome annotations required for primary H1/H2.

After that decision, freeze the revised pair and common oracle in a new private
manifest. Run the provider smoke on approved development material; do not use
the unresolved historical ARTA fixtures as a shortcut around discovery quarantine.
Use the existing `scripts/run_native_provider_smoke.py` only with a reviewed
private config and permitted inputs. Its example model names and prices are
historical values, not current account qualification or a budget authorization.
Confirm endpoint/model availability and pricing, set a spending ceiling, and
retain the redacted report outside the repository. This workspace currently has
neither `PANEL_OPENAI_API_KEY` nor `PANEL_DEEPSEEK_API_KEY`, and no repository `.env`;
these are observed local absences, not a claim about other machines or accounts.

For the first paired run, hold provider configuration, decoding settings and
oracle fixed; predeclare repetitions and execution order before inspecting
outputs. Preserve run/replication identities, errors and all variants. Report
constraint violations separately from runtime errors, timeouts and unexecuted
code. Do not retry only the worse variant or revise expected answers afterward.
Scale to additional projects only after this end-to-end pilot is reproducible.

## Product consequence

### Offline integration rehearsal (2026-09-13)

Run `python -m label_plane.behavior_rehearsal --output /private/new-run-directory`
under an existing private parent. Recheck with the same command plus
`--verify-only`. Existing directories are refused. The fixed rehearsal uses
literal control responses, never providers or arbitrary supplied code. It
exercises prompt projection, response JSON decoding, trusted-fixture execution,
per-replication artifacts, hash verification and analysis recomputation.

There are two unapproved source drafts and one separately named, original
development contract. The latter explicitly requires both authorized admission
and unauthorized denial; unconditional allow and unconditional deny both fail.
It is not a repair of the ARTA source or confirmatory evidence. Each contract is
used in positive, null and reverse synthetic scenarios, with two repetitions
and both variants: 36 episodes, 200 files, 199 receipt-bound file hashes and
three recomputed analyses. Expected project-mean deltas are +1, 0 and -1.
The source is deliberately selected by scenario; this does not simulate model
reasoning, estimate a treatment effect or qualify generated-code isolation.

The separate diagnostic analyzer matches run, replication, project, intent and
constraint IDs, and requires identical oracle/configuration hashes within each
planned pair. Duplicate or unexpected episodes are rejected. Missing arms,
crashes, timeouts, rejection and unexecuted code are counted separately and
excluded from semantic contrasts. With no complete pair the estimate is null,
not zero. Pair deltas are defective violation minus clean violation; projects
receive equal weight. The bootstrap resamples project means and is omitted with
fewer than two observed projects. Complete-case selection and very small project
counts limit interpretation; the synthetic intervals are only calculation checks.
No p-value, H1/H2 decision or change to the registered estimator is produced.

Do not route this rehearsal through the legacy `eval.thesis_analysis` aggregator:
its intent/task key collapses repetitions and its Boolean fallback cannot
distinguish a missing arm. That historical path is not corrected or endorsed by
this new, separate diagnostic. The new analyzer requires a planned inventory so
missing observations remain visible. Source/oracle review and live qualification
are still required before collecting real observations.

Verification: 35 focused tests passed for rehearsal, draft export and existing
paired-statistics helpers. The CLI created and verified the full bundle. Tests
cover unequal project sizes, all execution-failure categories, absent arms,
duplicate identities, mismatched hashes, changed artifacts and reverse effects.

The oracle-adequacy boundary remains grounded in the bounded Maton et al. ESEM
2025 entry in the canonical literature matrix. The rehearsal and estimator are
our implementation choices, not procedures evaluated by that paper.

A diagnostic should display an oracle disagreement together with the scope of
the tested obligation, unscored regions and review status. A future interface
should offer `review oracle assumption` alongside `inspect generated behavior`.
No automatic semantic approval or blocking follows from this reference audit.

Conceptual basis: [Barr et al., TSE 2015](https://doi.org/10.1109/TSE.2014.2372785)
distinguishes test oracles from ground truth. The partial candidates and workflow
above are our design decisions, not an intervention validated by that survey.
