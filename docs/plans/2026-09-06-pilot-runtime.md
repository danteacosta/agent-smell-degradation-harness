# Authorized exploratory pilot runtime

The user approved the proposed US$7 total cap, five repetitions and the expanded
24-intent exploratory LLM-only scope on 6 September. This records the user's
attestation, not a fabricated advisor signature or institutional exemption.
Prepare for the following week; collect admission screening now, not the main
pilot. All screening costs belong to the same US$7 experiment.

## Acceptance scenarios

1. Given a frozen 24-intent/six-project package and two pinned provider slots,
   planning yields 240 base episodes, 480 trajectories, 96 duplicated artifacts,
   2,748 calls including 60 screening and 96 diagnostic calls. Missing approval,
   altered inputs or an over-budget envelope blocks dispatch.
2. Given a planned call, reserve its conservative charge durably before network
   access; reconcile only valid usage and expected identity. Missing usage,
   exceptions, hash corruption and interrupted pending calls stop permanently.
   No retry or a second process may reset the shared budget.
3. Given screening, use only the prepared review-plane packets and retain every
   response. Provider consensus does not create rights, human labels or automatic
   admission. Persist operator dispositions and exact evidence references.
4. Given admitted records and a passed diagnostic gate, the prospective runner
   uses native T1/T2, local T3 before terminal generation, v2 judging, frozen
   duplicates and separate self/cross counts. Missing stages and uncertain labels
   remain explicit. No terminal outcome enters the pre-final observations.
5. Given successful offline checks, provide phase-specific commands sharing one
   ledger and preserve raw results, costs, hashes and temporal observations.
   A preflight must not itself issue provider calls.

## Design

- `eval/pilot_ledger.py`: separate explicit-call ledger for the authorized pilot;
  reuse the existing strict usage normalizer and price arithmetic, without
  relaxing the fixed pre-pilot ledger. One writer, hash chain, fsync, no hidden
  retries and no reuse of a paid call ID.
- `eval/pilot_runtime.py`: frozen planner, phase dispatcher and admission gates;
  reuse existing provider adapters, native runtime and v2 parser.
- Pilot-specific generation prompts remove the historical 2–4-word restriction
  and request explicit obligations. Keep output/context bounds enforceable and
  recalculate the US$7 envelope before paid screening.
- Private authorizations, source reviews, admission records and configurations
  live outside Git. Public documents contain only reviewed aggregate status.

The adapter pattern already isolates providers. The ledger is a command journal
because calls need durable intent and reconciliation; no extra framework is
needed. No subagents or concurrency, respecting the user's memory constraint.

## Verification

Write failing behavior tests first for counts, approval/hash gates, budget,
pending-call recovery, malformed usage, duplicate dispatch, blinding and native
checkpoint ordering. Run a full 480-trajectory offline rehearsal with deterministic
provider doubles. Run all repository tests/gates, compile, privacy and diff checks.
Freeze implementation/configuration before live screening and report its true
outcome, including unresolved corpus or funding blockers.
