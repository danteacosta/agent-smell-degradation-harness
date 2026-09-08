# Qualified evidence comparison implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline. The user
> requests sequential work without subagents to limit memory use.

**Goal:** Execute the approved source-block and v4/v5 correction without changing
historical scores, release criteria or spending caps.

**Architecture:** Add a versioned case/prompt module, a frozen-runtime custody
adapter, a plan and audit module, and a sequential coordinator. Reuse the existing
receipt inspector, provider adapter, immutable file writer and cost journal.
Do not modify production modules bound to earlier experiments.

**Tech stack:** Existing Python runtime, standard library and pytest; no new
dependencies. The [specification](../specs/2026-09-07-qualified-evidence-design.md)
and this plan are reviewed inline, not by an independent agent.

## Task 1: source-block cases and candidate prompt

Files: `label_plane/qualified_judge.py`, `tests/test_qualified_judge.py`.

- [x] Write behavior tests for contiguous wrapped prose, table and code context;
  exact target-only deletion; unchanged partial controls; versioned identity;
  oracle/source isolation; identical v4/v5 data; immutable parser semantics.
- [x] Run `python -m pytest -q tests/test_qualified_judge.py` red because the
  new module is absent. Also demonstrate the historical midpoint interruption.
- [x] Implement `build_cases(seeds)` by validating the preserved seed contract,
  then composing `first_clause + separator + whole_context + separator + rest`.
  Change only distributed/long-omission presentation and version all case IDs.
- [x] Implement `build_prompt(item, arm)` and `parse_response(raw, item, arm)`.
  V4 stays byte-identical to its existing builder; v5 adds the completeness
  instruction and a distinct prompt version. Both use the existing span parser.
- [x] Run focused tests green and commit.

## Task 2: frozen predecessor, plan and budget

Files: `eval/qualification_lineage.py`, `eval/qualification_plan.py`,
`tests/test_qualification_plan.py`.

- [x] Write tests for the complete failed predecessor, old-byte preservation,
  exact 48/96 plan, distinct case/prompt hashes and cumulative budget arithmetic.
- [x] Add rejection scenarios for missing/pending receipts, mutated custody,
  symlink paths, wrong runtime, malformed subprocess output and timeout.
- [x] Run tests red before creating the new modules.
- [x] Implement `predecessor_snapshot(directory, runtime)` using the preserved
  read-only report command. Verify code hashes first, suppress inherited
  credentials, bound output/time, and check private bytes before/after.
- [x] Implement `prepare_plan(predecessor, runtime)`, `validate_plan(plan)`,
  `check_budget(plan, spent, completed)` and `prices_for(plan)`. Rebuild cases
  and counterbalanced calls deterministically; freeze source/environment and
  preserve provider configuration, prices and 512-token output bounds.
- [x] Run green, inspect exact private envelope without dispatch, and commit.

## Task 3: receipt-derived scoring and exclusive successor

Files: `eval/qualification_audit.py`, `eval/qualification_custody.py`,
`tests/test_qualification_audit.py`, `tests/test_qualification_custody.py`.

- [x] Write tests for candidate-only gating, planned denominators, invalid
  baseline outputs, empty phases, operation-level errors, and no semantic claim.
- [x] Write custody tests for explicit approval, one successor, immutable
  closure, partial preparation, lock contention and missing-file rejection.
- [x] Run red, then implement pure `audit(plan, completed)` with opaque groups
  and the existing threshold applied to v5 for both providers.
- [x] Implement `create_run`, `load_run`, `custody_locks`, and `verify_custody`.
  Validate outside nested locks, recheck snapshots inside, publish the exclusive
  parent-linked claim last, and never recreate a missing journal.
- [x] Verify green and review authorization, shared accounting and private paths.

## Task 4: sequential live coordinator and CLI

Files: `eval/qualification_live.py`, `tests/test_qualification_live.py`.

- [x] Write integration tests with real journals and authored network adapters
  for 48+96 success, failed development, failed evaluation, resume, missing
  usage, post-reservation interruption, stale custody and secret-safe output.
- [x] Write CLI tests for read-only planning/reporting, explicit live approval,
  malformed arguments and missing credentials before any attempt.
- [x] Run tests red. Implement `report` and `run_phase` using the existing
  strict receipt inspector, `PilotLedger`, provider adapter and private env loader.
  Keep reserve-before-call and zero hidden retries; never repair model judgments.
- [x] Persist immutable private reports; retain accounting readiness separately
  from the scientific decision. A passing auxiliary cannot release main collection.
- [x] Verify green and commit.

## Task 5: freeze, collect and report

- [x] Run full pytest, compile, eval, replay, wedge and an isolated wheel build.
  Review security/cost/privacy, SOLID and clean-code boundaries. Verify all
  historical production files are unchanged and the old runtime still reports.
- [x] Commit the runtime, prepare the exact private plan and verify it fits
  both caps. Preserve a before-custody snapshot and apply only the approved closure.
- [x] Run 48 development calls sequentially, preserving every receipt. Run 96
  evaluation calls only if the frozen candidate rule passes for both providers.
- [x] Recheck custody, costs, incomplete outcomes and actual phase decisions.
  Preserve any failure without further prompt revisions or selective reruns.
- [ ] Publish redacted results and update the operational research documents;
  distinguish software invariants, construction agreement and unmeasured validity.
- [ ] Publish the implementation PR and verify its remote checks.

## Checkpoints

Collection reconciled on 2026-09-08 from the preserved `4e13d34` runtime:
48/48 development calls, US$0.032449, no pending accounting, all 16 bound
historical files unchanged. Both arms matched 23/24 vectors. V5 failed a required
partial-scope control, so all 96 evaluation calls remain unattempted. See the
[results](../../research/qualified-evidence-results.md). No prompt or criterion
was changed after collection. Public repository status is reconciled; Drive
synchronization remains separate. PR #49 fixes CI portability outside the frozen
collection worktree.

Historical pre-collection checkpoint: design approved by the user, including
the written specification. Clean baseline:
1,160 tests passed, 7 skipped and 9 subtests passed. CCE discovery returned mostly
historical worktrees; exact files were read directly before planning. No new
provider calls or closure writes have occurred at this checkpoint.
