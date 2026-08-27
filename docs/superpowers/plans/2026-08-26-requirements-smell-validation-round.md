# Requirements-smell validation round v8 implementation plan

> **For the executing agent:** execute this plan task-by-task in the validation-round-v8 worktree. Keep the status boundary between source-label screening and confirmatory evidence visible in every artifact.

**Goal:** Execute a reproducible natural-requirement screening round with project-held-out splits, a text-only baseline, a controlled paraphrase probe, and explicit readiness blockers for expert annotation and real models.

**Architecture:** A versioned private JSONL corpus stores source text and provenance; `baselines/natural_smell.py` owns the frozen text-only comparator; `eval/validation_round.py` owns licensing validation, split construction, metrics, probes, and redacted artifact writing. The runner reuses the existing grouped split utility and does not invoke provider APIs in offline mode.

**Tests:** Pytest behavior tests at the public-module boundary cover schema failures, quota/split invariants, marker independence, paraphrase exclusion, readiness status, and artifact completeness.

## Task 1: Add failing behavior tests

- [ ] Add `tests/test_natural_smell_baseline.py` for deterministic text-only scoring, marker independence, and metric counts.
- [ ] Add `tests/test_validation_round.py` for corpus validation, quota enforcement, project-disjoint splitting, paraphrase exclusion, readiness blockers, and artifact files.
- [ ] Run the focused tests and confirm they fail because the new modules do not exist yet.

## Task 2: Add the frozen natural-corpus baseline

- [ ] Add `baselines/natural_smell.py` with the six supported families, versioned lexicons, text-only prediction, Wilson intervals, and source-label screening metrics.
- [ ] Keep marker/source-label fields out of all scoring code.
- [ ] Run focused baseline tests until green.

## Task 3: Materialize the natural ARTA screening corpus

- [ ] Select 10 single-marker positives and 10 distinct clean controls per supported family from the versioned ARTA workbook.
- [ ] Write per-case provenance, source-label type, project ID, licensing note, and pending expert-label state.
- [ ] Write the corpus manifest with source hash, dataset commit, supported/underrepresented families, annotation plan, and model slots.
- [ ] Run schema/quota validation against the selected JSONL.

## Task 4: Implement and run the v8 runner

- [ ] Add `eval/validation_round.py` with strict validation, project-held-out split, baseline test metrics, controlled paraphrase probe, v7 simulation-only agent conditions, and readiness report.
- [ ] Enforce the source-rights gate; run `discovery-20260826-v8-screening` only with an explicit private-source flag, and write an auditable redacted bundle under `artifacts/experiments/runs/`.
- [ ] Confirm the status is screening/descriptive-only and that real-model slots remain `not_run` without credentials.

## Task 5: Document and verify

- [ ] Update `tasks/todo.md` and relevant READMEs with the exact v8 command, artifact path, interpretation, and blockers.
- [ ] Run the full pytest suite, `git diff --check`, and the repository gates available locally.
- [ ] Review the diff for leakage, false claims, SOLID/clean-code issues, and accidental changes outside scope.
- [ ] Commit, fast-forward `main`, push GitHub, and verify CI before reporting completion.

## Required verification commands

```bash
./.venv/bin/python -m pytest -q tests/test_natural_smell_baseline.py tests/test_validation_round.py
./.venv/bin/python -m eval.validation_round --corpus data/pairs/discovery-natural-v8/cases.jsonl --run-id discovery-20260826-v8-screening --output-root artifacts/experiments
./.venv/bin/python -m pytest -q
git diff --check
```

## Explicit non-claims

- ARTA source markers are not independent thesis annotations.
- The ARTA requirement excerpts are not redistributed until a written reuse/derivative-use permission is recorded.
- The offline baseline is not a real LLM.
- The deterministic v7 agent-condition control is not a live-agent result.
- No production latency, cost, sandbox, or generalization claim is made by this round.
