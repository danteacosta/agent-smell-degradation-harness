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
a division-by-zero exception and a bounded over-budget loop control (one-second
executor timeout). Version 2 requires all five distinct statuses; execution
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

## Product consequence

A diagnostic should display an oracle disagreement together with the scope of
the tested obligation, unscored regions and review status. A future interface
should offer `review oracle assumption` alongside `inspect generated behavior`.
No automatic semantic approval or blocking follows from this reference audit.

Conceptual basis: [Barr et al., TSE 2015](https://doi.org/10.1109/TSE.2014.2372785)
distinguishes test oracles from ground truth. The partial candidates and workflow
above are our design decisions, not an intervention validated by that survey.
