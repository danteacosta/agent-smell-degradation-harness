# Shared-omission E2E extension plan

Scientific contract: see
`docs/preregistration/2026-10-05-shared-omission-e2e.md`.

The adapter reuses the frozen custody, provider, Docker runner and
mutation-adequacy machinery without editing the completed PR #180 artifacts.
It selects one confirmed mutant per requirement and creates a 2×2 design:
complete/incomplete requirement × scaffold/mutant-code context. The two code
arms receive the same mutant.

- [x] Add regressions for deterministic mutant selection, identical code
  context, distinct complete/incomplete prompts and the four-arm primary
  contrast.
- [x] Implement preparation, verification, generation, execution and separate
  public summary in `scripts/shared_omission_e2e.py`.
- [ ] Run all focused and inherited tests, compilation and diff checks without
  model calls.
- [ ] Review security, custody and the scientific contract; publish the
  protocol before any generation.
- [ ] Qualify Docker, freeze a fresh packet and execute exactly one collection
  only after human authorization of the 200-call budget.
- [ ] Reconcile receipts and results, then open a separate result PR without
  automatic merge.

Fail closed on drift, missing packets, an unqualified control or a code arm
that does not use the selected mutant. No API-key fallback, retry or repair.
