# Live addressed comparison implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline. The user
> requires sequential work without subagents to limit memory use.

**Goal:** Execute the approved 48-call development and conditional 96-call
evaluation with preserved custody, verified costs and no main-pilot release.

**Architecture:** A custody module owns succession and shared accounting. A
separate live coordinator uses the existing durable journal and immutable
auditor. Validation happens outside nested locks; byte identities and journal
heads are checked again inside each critical section.

**Tech stack:** Existing Python runtime, pytest, standard library, installed
provider SDK. No dependency changes.

## Contract and review

The [approved specification](../specs/2026-09-07-addressed-comparison-live-design.md)
defines the scientific and spending boundaries. Preserve old modules and private
evidence. Adapter doubles replace network calls only; real journals, locks,
budget calculations, prompts and parsers remain in integration tests. Review
is inline, not independent.

## Task 1: custody and exclusive succession

Create `eval/addressed_comparison_custody.py` and
`tests/test_addressed_comparison_custody.py`.

- [x] Write tests for preparation with explicit approval, unchanged predecessor
  bytes, one successor only, transferred experimental identity, durable closure
  and shared-budget arithmetic.
- [x] Run `python -m pytest -q tests/test_addressed_comparison_custody.py` and
  confirm failure because the new interface does not exist.
- [x] Implement `create_run(approved_plan, directory, approval=False)`: rederive
  the current offline plan, permit only additional coordinator source files while preserving the environment,
  lock parent then predecessor, recheck custody, exclusively create private
  manifest/closure/ledger, and publish the successor claim last.
- [x] Implement `load_run`, `custody_locks`, `verify_custody`, `prices_for` and
  `check_budget` with fixed error categories. Never recreate a missing ledger.
- [x] Add malformed files, symlinks, partial preparation, changed plans, changed
  source/environment, claim mismatch, missing files and lock contention tests.
- [x] Run focused tests green and review all failure paths before committing.

## Task 2: verified reporting and gated dispatch

Create `eval/addressed_comparison_live.py` and
`tests/test_addressed_comparison_live.py`.

- [x] Write integration tests for a complete passing 48+96 path, unchanged old
  bytes, resume without repurchase, failing development and invalid baseline.
- [x] Run the new tests red before implementing the coordinator.
- [x] Implement a private verified snapshot: inspect the journal under locks,
  bind each completed receipt to its planned prompt/model, release locks for
  the existing auditor, then recheck custody and journal head.
- [x] Implement `report(directory)` with redacted counts, costs, usage,
  pending reservations, phase decisions and the unchanged nested offline audit.
  Keep ledger heads and configuration identities private.
- [x] Implement `run_phase(directory, phase, approval=False, provider_factory=None,
  environ=None, progress=None)`: require approval, rederive the gate, acquire
  parent/predecessor/ledger locks, recheck the snapshot head, skip completions,
  enforce shared commitments, dispatch once and preserve receipts.
- [x] Add regressions for missing usage, a crash after reservation, corrupt or
  missing journals, stale snapshots, edited saved reports and drift before a
  later call. Invalid model judgments must not become transport retries.
- [x] Verify red/green results and commit the coordinator.

## Task 3: CLI and privacy

Extend the live module and add `tests/test_addressed_comparison_live_cli.py`.

- [x] Write subprocess/entry-point tests red for `prepare`, `development`,
  `evaluation`, `report`, required approval and secret-safe failures.
- [x] Add explicit private-plan/directory/env-file options. Preparation and
  reporting never contact providers. Reuse the existing private env loader.
- [x] Emit aggregate progress only. On an ambiguous attempt, preserve and report
  the stopped state. Use exit 2 for a failed/incomplete phase or fixed error.
- [x] Test network prohibition for offline operations, private output permissions,
  malformed arguments and no raw/private strings in public output.

## Task 4: verification, freeze and collection

- [x] Run all new suites and `python -m pytest -q`; compile source and run the
  existing eval, constraint-replay and wedge gate commands from CI.
- [x] Review the complete diff for custody, authorization, integer accounting,
  privacy, SOLID and clean-code boundaries. Confirm frozen modules are unchanged.
- [x] Commit the runtime and preserve the exact source/environment identity.
- [x] Revalidate the private approved plan; check frozen pricing and key presence
  without revealing secrets. Record the successor and audited closure only after
  all preconditions hold. Do not buy credits or increase the approved caps.
- [x] Run development sequentially with periodic aggregate progress. Preserve
  every outcome. If the prospective gate passes, run evaluation unchanged.
- [x] Generate private and redacted reports; document observed outcomes and
  limitations separately from software verification. Preserve any failed gate.
- [ ] Publish code and redacted findings in a PR, with fresh tests and CI evidence.

No step promotes the constructed answers to human truth, claims semantic
validity from resolvable citations, or releases the main cohort.

## Execution record

The frozen runtime `10e2d8f` completed 48 development calls at US$0.028024.
Every call has verified usage and cost. The prospective gate failed on one v4
long-omission abstention, so evaluation was not dispatched. See the
[redacted results](../../research/addressed-comparison-results.md). All 18
historical custody files remain unchanged; current unused reservations remain
held. Main collection was not released.

Verification before collection: 47 new tests; 1,160 full-suite tests passed,
7 skipped and 9 subtests passed. Eval, replay, wedge, compile and an isolated
wheel build passed. No frozen production module was changed after collection.
