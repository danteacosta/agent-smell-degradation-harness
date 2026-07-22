# Wedge-First Reliability Check — Implementation Plan

> **For agentic workers:** Execute task-by-task with TDD. Checkbox tracking.

**Goal:** Ship the usable OSS wedge (CI/local reliability check) plus thesis infrastructure (Tier A/B, mutation, RF-11, H2 group-split) without breaking existing gates.

**Architecture:** Extend harness-core; add `wedge/` package as the product surface; keep `eval`/`gates` as lab twin.

**Tech Stack:** Python ≥3.11, pytest, existing packages.

---

### Task 1: Docs — thesis+product positioning in README

Update README hero: reliability layer / CI check; link new design spec; keep failure modes.

### Task 2: Tier A/B provenance tagging

- Modify `observability/tracing.py`: events include `"tier": "A"|"B"`
- Runner: operational + constraint_extract = A; after oracle, log `oracle_verdict` as tier B in a **separate** file or same JSONL with tier B
- `observability/features.py`: `extract_tier_a_features(provenance_path)` — never reads oracle_verdict
- Tests: features have no `oracle_passed` / oracle_verdict keys

### Task 3: Mutation testing for test_gen

- `eval/mutation.py`: for each intent, define mutants that violate clean constraint; run generated test_gen artifact as a **predicate** (structured JSON checks against mutant params)
- Since artifacts are structured JSON not pytest files, mutation score = fraction of smell-relevant mutants that the test_gen artifact would reject (using must_reject / criterion fields)
- Attach `mutation_score` to episodes for test_gen; binary degraded if score < 1.0 on smelly or use alongside oracle
- Tests for RF-09: weak test_gen catches fewer mutants than clean

### Task 4: RF-11 numerical inconsistency pair

- `data/pairs/mesaflow_rf11.json` — 10 vs 15 minute conflict
- oracle_spec encodes clean window (10); smell type `numerical_inconsistency`
- Stub weakenings for RF-11
- Taxonomy map

### Task 5: Wedge CLI

- `wedge/check.py` + `python -m wedge.check`
- Inputs: requirement text path or pair id; optional traces; policy
- Outputs JSON: `{decision: approve|warn|clarify, reasons: [], static_smell, tier_a_risk, tier_b_degraded}`
- Offline: run against stub eval episode or direct detect+features
- Makefile `wedge-check`
- Tests for three decisions

### Task 6: GitHub Action

- `.github/workflows/wedge-check.yml` — on PR, run `python -m wedge.check --demo-smell-blind` or fixture that proves check fails when degradation undetected... Actually for CI of the *repo*, keep eval-gate; add job that runs wedge acceptance tests.
- `action.yml` or docs for consumers: how to call wedge.check on their repo (document in `docs/wedge.md`)
- Workflow job `wedge` runs `pytest tests/test_wedge.py` + `python -m wedge.check --fixture demo`

### Task 7: H2 group-split detector script

- `eval/h2_detection.py`: load episodes+tier A features; group K-fold by intent_id; AUROC for static / operational / provenance_semantic
- Offline on smell-blind stub episodes
- `python -m eval.h2_detection`
- Test: group split never mixes same intent across folds; provenance AUROC computed

### Task 8: Acceptance + CHANGELOG + PR

- `tests/test_wedge_acceptance.py`
- CHANGELOG entry
- Full pytest green; PR

---

## Verification

```bash
pytest -q
make all
python -m wedge.check --fixture demo-clean   # approve or warn
python -m wedge.check --fixture demo-smelly  # clarify or warn
python -m eval.h2_detection
```
