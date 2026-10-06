# Proposed factorial-successor plan

Status: unexecuted proposal in PR #183, not the plan used by the completed
three-arm collection in PR #184. Preserve PR #181 at `eec5110` and all
original result packets. Human approval and a fresh freeze are required.

Proposed scientific contract: see
`docs/preregistration/2026-10-05-shared-omission-e2e.md`.

The adapter reuses the frozen custody, provider, Docker runner and
mutation-adequacy machinery without editing the completed PR #180 or #184 artifacts.
It selects one confirmed mutant per requirement and creates a 2×2 design:
complete/incomplete requirement × scaffold/mutant-code context. The two code
arms receive the same mutant.

- [x] Add regressions for deterministic mutant selection, identical code
  context, distinct complete/incomplete prompts and the four-arm primary
  contrast.
- [x] Implement preparation, verification, generation, execution and separate
  public summary in `scripts/shared_omission_e2e.py`.
- [x] Run focused and inherited tests, compilation and diff checks without
  model calls; 30 focused tests and three CI gates passed at `82e8b16`.
- [ ] Obtain human review of the successor contract with the #184 results
  already known; register and freeze it before any successor generation.
- [ ] Qualify Docker, freeze a fresh packet and execute exactly one collection
  only after human authorization of the 200-call budget.
- [ ] Reconcile receipts and results, then open a separate result PR without
  automatic merge.

Fail closed on drift, missing packets, an unqualified control or a code arm
that does not use the selected mutant. No API-key fallback, retry or repair.
