# Offline addressed comparison implementation plan

> **For agentic workers:** Use superpowers:executing-plans task by task. Execution
> and review are inline under the user's memory constraint; no subagents.

**Goal:** Prepare and audit the approved v3/v4 comparison without provider access
or mutation of historical studies and budget claims.

**Architecture:** Planning verifies the preserved predecessor and derives the
matched private plan. Auditing consumes that plan and supplied responses; a
small CLI exposes only these offline operations. Existing parsers, pricing,
integer envelopes and read-only journal inspection remain unchanged.

**Tech stack:** Python standard library and pytest in the existing private
runtime. No package installation, browser or new model dependency.

## Acceptance contract and ownership

The five BDD scenarios and prospective gates are in the
[approved spec](../specs/2026-09-07-addressed-comparison-design.md).
They cover read-only 144-call preparation, custody/budget failures, complete
denominators, response identity and the absence of execution authority.

- `eval/addressed_comparison_plan.py`: bounded private reads, predecessor
  verification, matched calls, integer budget proposal, deterministic plan
  validation and safe preparation summary.
- `eval/addressed_comparison_audit.py`: supplied-observation validation, separate
  v3/v4 parsing, counts by phase/provider/arm/operation/source and paired counts.
- `eval/addressed_comparison.py`: offline CLI and exclusive private export.
- `tests/test_addressed_comparison_plan.py`: real frozen predecessor fixtures,
  custody and accounting boundaries, with fake historical provider receipts.
- `tests/test_addressed_comparison_audit.py`: authored response inventories and
  prospective exact-vector gates; no empirical qualification claims.
- `tests/test_addressed_comparison_cli.py`: file, privacy and network boundaries.

No strategy class is needed for two fixed arms: explicit dispatch to existing
pure parsers is narrower. Do not modify the frozen baseline, ledger or launch.

## Task 1 — Read-only plan and budget

- [x] Add tests: `prepare_comparison(predecessor, approval=True)` returns 144
  calls, false authority flags and a proposal retaining all measured spending.
  Snapshot every existing file before/after; test missing approval, incomplete,
  passing, pending and changed predecessors, altered baseline, bank and claims.
- [x] Run `python -m pytest -q tests/test_addressed_comparison_plan.py` and
  observe failures for the missing module/contract before production code.
- [x] Implement bounded reads, both existing shared locks, predecessor
  regeneration, preserved-source checks and budget arithmetic. New calls reuse
  v3/v4 prompts and alternate both arms/providers. Reject duplicate locators.
- [x] Implement `validate_plan(plan)` by rederiving its deterministic contents
  from unchanged private custody and comparing strict canonical identities.
- [x] Re-run focused tests. Review integer cap boundaries and exact read-only
  behavior. The implementation units will share a reviewed integration commit.

## Task 2 — Offline response audit

- [x] Write tests for missing/invalid/valid observations, identity mismatches,
  exact versus aggregate agreement, group/paired denominators, and no release
  even for fully matching authored responses.
- [x] Run the new test file and observe the missing audit contract fail.
- [x] Implement `audit_comparison(plan, records)`. Require unique planned call
  IDs and matching prompt digests. Count absent/null responses as missing,
  malformed model responses as invalid, and every planned pair as a pair.
- [x] Evaluate candidate response rules separately from authorization, with
  complete development required before the offline evaluation rule can pass.
  Keep construction agreement and semantic support validity separate.
- [x] Re-run plan/audit tests. Inspect summaries for private source,
  response, provider and exception leakage.

## Task 3 — CLI and private preparation check

- [x] Add CLI tests first: `prepare --predecessor PATH --approve-offline`,
  optional `--output-dir PATH`, and `audit --plan PATH --responses PATH`.
  Reject live/env options, symlinks, oversized/invalid JSON and overwrites.
- [x] Run tests and observe failure, then implement the bounded CLI. Private
  plans export outside Git checkouts, exclusively; stdout is aggregate-only.
- [x] Verify the full path with network functions disabled. No provider factory
  or mutable ledger is used by the new implementation.
- [x] Run private preparation against the preserved study, displaying only
  aggregate counts and budget. Verify all historical bytes remain unchanged.

## Task 4 — Documentation, verification and handoff

- [x] Add `docs/research/addressed-comparison.md` with CLI contracts, metrics,
  budget-proposal limitations and the remaining live-coordinator boundary.
  Link it from the research index and update the roadmap's offline status.
- [x] Run focused tests, `python -m pytest -q`, compilation, `python -m eval`,
  `python -m gates`, `make wedge-check` with the private Python override, and
  replay fixtures. Run `git diff --check` and inspect the complete diff.
- [x] Review security/privacy, custody races, SOLID and clean-code properties
  inline. Do not claim an independent review or empirical provider improvement.
- [ ] Commit and publish the branch/PR with fresh evidence; leave merge and
  real collection separate. Preserve all historical worktrees and manifests.

The local `python` in commands above means
`/Users/dantecosta/Documents/GitHub/.private-research-evidence/advisor-meeting-20260907/runtime/bin/python`.
Plan review: direct, against the approved spec; no blocking gap identified.

## Implementation review

Plan gaps: none identified in the offline scope. Real dispatch and budget
succession remain absent by design. Use-case review covers both phase rules,
all planned pairs, exact versus aggregate agreement and historical custody.
Supplementary tests cover simultaneous writers, non-integer costs, duplicate
source locators, altered inherited provider settings and malformed hash maps.

The initial tests failed before each new module existed. A complete authored
audit caught iterator exhaustion in operation totals; the same behavioral test
passes after the fix. Review also found that provider credential-variable names
could diverge from the parent without changing price receipts. The new planner
now checks the full inherited provider specification. Frozen legacy code was
not modified.

Architecture/SOLID: pure response scoring remains separate from custody and
budget preparation; only the CLI exports files. No provider or mutable ledger
is instantiated. Existing pricing, parser and journal contracts are reused.
Clean-code review found no need for a new abstraction hierarchy. This review
is AI assisted, not independent human or methodological approval.

## Verification record

Fresh local verification: 60 focused tests; 1,113 full-suite tests passed,
7 skipped and 9 subtests passed. Compilation, eval/gates, 11 wedge tests and
the three wedge fixtures passed. Replay returned 0 for clean and the expected
20 for constraint loss. Diff checks passed; no new dependencies were installed.

The final private offline preparation reproduced 144 planned calls. The
uncollected audit retained 144 missing responses and no observed response;
both candidate rules were unmet. Hash comparisons verified 19 historical
files unchanged. A preliminary plan was rejected after a code change, then a
new final plan was exported without overwriting that preliminary artifact.
No closure, reservation release or provider call occurred.
