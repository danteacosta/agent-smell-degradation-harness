# Tau2 analysis contract implementation plan

**Goal:** Remove the three outcome-accounting errors reproduced in the readiness
review before scientific collection. Dante approved the inventory and design
and selected GPT-6 Astra for agent and simulated user on 2026-10-09.

**Architecture:** Keep policy construction, upstream rewards and the seeded
variant order unchanged. Index analysis by explicit variant/task/trial slots.
Missing or technical outcomes remain unresolved, not failed scientific outcomes.

**Tech stack:** Python, pytest; offline synthetic fixtures only.

## Acceptance and implementation

Files: `scripts/policy_adequacy.py`, `tests/test_policy_adequacy.py`.

- [x] Write and run failing public tests for null outcomes, absent initial slots,
  attempted technical failures, partial confirmations, empty eligibility,
  duplicate slots, invalid rewards and order independence.
- [x] Require trial identity: A uses 1-4, variants use 1-3. Reject duplicate and
  unknown slots rather than count them twice or infer identity from file order.
- [x] Preserve 3/4 baseline eligibility and 2/3 confirmation. A technical baseline
  outcome makes that task unresolved; all three valid confirmation outcomes are
  required before a confirmation decision.
- [x] Separate missing initial slots, technical failures and unattempted
  confirmations. Emit only genuinely unattempted confirmations after a valid
  initial failure; never retry an attempted technical failure.
- [x] Mark every rule `not_estimable` when no task is eligible. Report the
  eligible denominator and unresolved baseline tasks explicitly.
- [x] Keep legacy class names operational: they summarize reward sensitivity,
  not proof of a target-rule violation. Human trajectory inspection remains a
  separate requirement.
- [x] Run all policy and subscription transport tests against pinned tau2;
  compile changed files, review SOLID/clean code/security and documentation.

Verification: `python -m pytest -q tests/test_policy_adequacy.py` with the pinned
checkout supplied as `TAU2_CHECKOUT`. This analysis change launches no calls.
Live technical feasibility remains separate and excluded from these rows.

Verification: 87 focused tests passed before the two review advisories were
covered; final count is recorded in the execution-readiness note. Three
independent reviewers checked all seven review dimensions. No analysis provider
calls were made.
