# Agent Smell Degradation Harness — Tier 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Activate thesis overlays for C1 (taxonomy) and C4 (provenance vs static/output/operational baselines), plus a live `make experiment` path — while keeping default CI offline and secret-free.

**Architecture:** Extend the Tier 1 harness-core without breaking AT1–AT5. Taxonomy labels attach to episodes after oracle scoring. Baseline feature extractors consume provenance JSONL + pair metadata and produce comparable scores for characterization (retrospective). Live adapter is optional (`[live]` extra); offline stub remains the CI default. Effect/observability gates are *analysis reports*, not CI-blocking unless explicitly opted in.

**Tech Stack:** Python ≥3.11, pytest, PyYAML, existing harness packages; optional `openai` (or provider SDK) behind `[live]`.

**Spec:** `docs/superpowers/specs/2026-07-20-agent-smell-degradation-harness-design.md` §§8–10 (Tier 2 row).  
**Depends on:** Tier 0–1 on `main` (merged PR #1).

**Out of scope:** C5 mitigation (Tier 3), full dissertation packaging, human IRR tooling beyond CSV export hooks.

---

## File structure (lock-in)

```text
taxonomy/
  __init__.py
  catalog.py              # smell → degradation mode mapping
  label.py                # assign mode + severity from episode
baselines/
  __init__.py
  features.py             # extract feature dicts per family
  score.py                # fit/score simple baselines (offline)
  compare.py              # produce comparison table JSON
agents/
  live.py                 # LiveAgent adapter (optional deps)
eval/
  experiment.py           # make experiment entry
  analysis_report.py      # effect + observability gate reports
protocol/
  paired_stats.py         # minimal paired Δ + CI helpers
tests/
  test_taxonomy.py
  test_baselines.py
  test_live_agent_offline_guard.py
  test_experiment.py
  test_analysis_gates.py
docs/superpowers/plans/README.md  # mark Tier 2 plan
```

**Baseline feature families (from spec §10):**

| Family | Example features |
|--------|------------------|
| `static_smell` | smell category/type present, requirement length, ambiguity marker count |
| `output_only` | oracle passed, semantic_label |
| `operational` | latency_ms, token/cost proxy, trace event count |
| `provenance_semantic` | has constraint_extract, semantic event count, plan/validator flags (stub: presence of semantic kinds) |

Tier 2 claim: provenance_semantic improves *retrospective characterization* of degraded episodes beyond static_smell and operational alone (simple metrics: AUROC on synthetic labels from paired Δ, or accuracy of “was this episode degraded?”).

---

### Task 1: Taxonomy catalog + labeler (C1 seed)

**Files:**
- Create: `taxonomy/catalog.py`, `taxonomy/label.py`, `tests/test_taxonomy.py`
- Modify: `taxonomy/__init__.py`

- [ ] **Step 1: Failing test**

```python
from taxonomy.label import label_degradation
from taxonomy.catalog import DEGRADATION_MODES

def test_rf09_maps_to_vague_threshold_mode():
    result = label_degradation(
        intent_id="RF-09",
        smell_type="vague_threshold",
        oracle_passed=False,
        task_family="codegen",
    )
    assert result.mode in DEGRADATION_MODES
    assert result.mode == "wrong_numeric_threshold"
    assert result.severity in {"low", "medium", "high"}
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement catalog**

Seed modes (from thesis §9.1, keep small):
- `identifier_format_ambiguity`
- `ordering_ambiguity`
- `wrong_numeric_threshold`
- `cardinality_ambiguity`
- `unverifiable_output`
- `none` (oracle passed / clean recovery)

Map RF-04→identifier_format_ambiguity, RF-07→ordering_ambiguity, RF-09→wrong_numeric_threshold, RF-13→cardinality_ambiguity. If oracle_passed: mode=`none`, severity=`low`.

- [ ] **Step 4: PASS + Commit** `feat: add C1 taxonomy catalog and labeler`

---

### Task 2: Wire taxonomy into eval runner export

**Files:**
- Modify: `eval/runner.py`, `eval/metrics.py`
- Create: `tests/test_runner_taxonomy.py`

- [ ] **Step 1: Failing test** — happy-path metrics include `taxonomy_modes` summary; each episode record (if exported) has `degradation_mode`

Also enrich each episode dict with: `smell`, `artifact`, `requirement_text`, `intent_id`, `variant`, `task_family`, `oracle_passed`, `degradation_mode`, `degradation_severity` (from taxonomy after oracle).

- [ ] **Step 2–4: Implement + PASS**

- [ ] **Step 5: Commit** `feat: attach taxonomy labels to eval episodes`

---

### Task 3: Baseline feature extraction (C4)

**Files:**
- Create: `baselines/features.py`, `baselines/score.py`, `baselines/compare.py`, `tests/test_baselines.py`

- [ ] **Step 1: Failing tests**

```python
from baselines.features import extract_features
from baselines.compare import compare_baselines

def test_extract_static_and_provenance_features(tmp_path):
    # build minimal episode dict + provenance jsonl with one semantic event
    feats = extract_features(episode, provenance_path)
    assert "static_smell" in feats
    assert "provenance_semantic" in feats
    assert feats["operational"]["event_count"] >= 1

def test_compare_baselines_ranks_provenance_on_synthetic():
    report = compare_baselines(episodes_with_labels)
    assert "auroc" in report["provenance_semantic"]
    assert report["provenance_semantic"]["auroc"] >= report["operational"]["auroc"] - 1e-9
```

For offline synthetic characterization: label `y = 1` if episode is smelly variant AND oracle failed (or `degradation_detected` pair-level). Train/score with a **dumb threshold classifier** on a single feature (no sklearn required): e.g. AUROC via rank statistic, or accuracy of `semantic_event_count == 0 ⇒ degraded` vs operational `latency > 0` (weak). Prefer implementing `mann_whitney_auroc(scores, y)` in ~20 lines.

**Provenance features (lock-in):** prefer payload-derived signals from `constraint_extract` (e.g. whether extracted comparator matches clean oracle) over mere event presence — presence-only often ties operational AUROC at ~0.5.

- [ ] **Step 2–4: Implement + PASS**

- [ ] **Step 5: Commit** `feat: add C4 baseline feature families and comparison`

---

### Task 4: Protocol paired_stats helper (minimal C3) — before analysis gates

**Files:**
- Create: `protocol/paired_stats.py`, `tests/test_paired_stats.py`

Functions: paired proportion difference, bootstrap CI (simple resample), export dict for analysis report. Keep dependency-free.

- [ ] **Step 1–5: TDD + Commit** `feat: add minimal paired stats helpers`

---

### Task 5: Analysis report — effect + observability gates

**Files:**
- Create: `eval/analysis_report.py` (run as `python -m eval.analysis_report`), `tests/test_analysis_gates.py`
- Modify: `Makefile` add `analysis` target

**Input contract (lock-in):** `build_analysis_report()` calls `run_eval` twice in-process:
1. happy path (`failure_mode=None`)
2. smell-blind (`failure_mode="smell-blind"`)
Then runs `compare_baselines` on the smell-blind episode list. Does **not** read `last_run.json` (avoids clobbering gate artifacts). Writes only `eval/analysis_report.json`.

**Effect gate (report, not CI-blocking):** `effect_detected` true iff smell-blind `paired_degradation_rate > 0`.

**Observability gate (report):** `provenance_semantic` AUROC ≥ `operational` AUROC on the smell-blind episode set (payload-aware features preferred over presence-only).

- [ ] **Step 1: Failing test** for report shape and gate flags

- [ ] **Step 2–4: Implement + PASS**

- [ ] **Step 5: Commit** `feat: add effect and observability analysis reports`

---

### Task 6: Live agent adapter (optional deps)

**Files:**
- Create: `agents/live.py`, `tests/test_live_agent_offline_guard.py`
- Modify: `pyproject.toml` `[project.optional-dependencies] live = ["openai>=1.0"]`

**Contract:**
- Without `[live]` / API key: `LiveAgent` raises `NotConfiguredError`.
- With key + `mode=live`: call model, parse JSON artifact; on parse failure set `semantic_label` to `infra_error` distinctly from `degraded`.
- Record `model`, `provider`, date. Bounded retries (max 2).

Offline test: NotConfiguredError without network.

- [ ] **Step 1–5: TDD + Commit** `feat: add optional live LLM agent adapter`

---

### Task 7: `make experiment` entrypoint

**Files:**
- Create: `eval/experiment.py` (`python -m eval.experiment`)
- Modify: `Makefile` `experiment` target
- Create: `tests/test_experiment.py`

Behavior:
- Default: refuse live without `AGENT_EXPERIMENT=1` and API key; print instructions.
- `--stub-as-live` runs stub with experiment-shaped export (CI-less schema demo).
- `--replications N` writes `replication_id` on each episode.
- Writes `eval/experiment_run.json` + episodes JSONL; never overwrites `last_run.json` unless `--also-last-run`.

- [ ] **Step 1–5: TDD + Commit** `feat: add make experiment export path`

---

### Task 8: Docs + acceptance for Tier 2 overlays

**Files:**
- Modify: `README.md`, `docs/interop.md` (document new artifacts: `last_run_episodes.jsonl`, `analysis_report.json`, `experiment_run.json`), `docs/superpowers/plans/README.md`
- Create: `tests/test_tier2_acceptance.py`

Acceptance (offline, no secrets):
1. Taxonomy labels attach on eval export
2. `compare_baselines` runs on smell-blind episode set
3. Analysis report writes effect/observability flags
4. Live agent NotConfiguredError without keys
5. Default CI still green without live deps

- [ ] **Step 1–5: Implement + `make all` green + Commit** `test: add Tier 2 offline acceptance criteria`

---

## Verification

```bash
pytest -q
make all                  # Tier 1 path unchanged
python -m eval.analysis_report
make experiment           # should instruct / stub-as-live
```

CI must remain secret-free; do **not** add live API calls to `.github/workflows/eval.yml`.

---

## Exit criteria (Tier 2)

- [ ] C1 catalog + labels on episodes
- [ ] C4 four feature families + comparison report
- [ ] Effect + observability analysis JSON
- [ ] Optional live adapter with offline guard
- [ ] `make experiment` schema path
- [ ] Tier 1 ATDD still green
