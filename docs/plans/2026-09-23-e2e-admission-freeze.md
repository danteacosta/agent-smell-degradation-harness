# E2E admission and prompt freeze

Goal: freeze exact direct-code A/B/C requests only after source/prompt and endpoint admission review. No provider dispatch is part of this preparation step.

Architecture: reuse the pinned criteria-expansion source/variant records and existing qualified browser instruments. Store a public source-relative admission record and prompt bundle, plus a private evidence packet with immutable file hashes. Keep generator requests free of source URLs, condition labels, omitted-target annotations, fixtures and oracle code. No new provider adapter or design pattern is needed.

Acceptance scenarios:
1. Given pinned sources, A must equal the exact source slice and C must be exactly the declared single-span deletion; B must preserve all obligations in an independent review.
2. Given a prompt for any arm, its common interface must not state or imply the omitted target; compare exact common bytes across all arms.
3. Given a qualified instrument, its current runtime bytes and authored-control receipts must match, and endpoint limitations must be resolved before case admission. Defer unsupported cases explicitly.
4. Given admitted cases, record a balanced randomized schedule and every planned position without calling models. Empty admission is not a runnable experiment.
5. Given an existing packet, never overwrite it; verify every recorded hash before recording freeze status. Source exposure and human approvals remain explicit.

- [x] Inspect current sources, interfaces and runtimes; baseline 53 focused tests pass.
- [x] Independently review exact draft source/prompt bundle and admission decisions.
  Prompts accepted for all three; bounded persistence endpoint accepted, Mark all and StrictDoc deferred.
- [x] Freeze reviewed prompt bytes and document any deferred endpoint.
- [x] Verify provenance, qualification custody, schedule balance and request separation.
- [ ] Update current research status and submit preparation artifacts for CI/merge.

The admission review is performed by an independent assistant, not a human or an empirical judge. No H1/H2 conclusion follows from this preparation. The intended cross-project expansion is not replaced by a one-project subset.
