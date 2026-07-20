# Pre-Experiment Tooling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or execute task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Ship all offline pre-experiment tooling so live LLM runs only need an API key — mocks, dry-run, manifesto, tolerant oracles, IRR import, H1–H5 analysis, template mitigation, release hygiene.

**Architecture:** Extend existing harness without breaking Tier 1–3 CI. Live path uses injectable transport (real OpenAI client OR `MockTransport`). Experiment writes under `runs/<run_id>/`. Default CI stays secret-free.

**Tech Stack:** Python ≥3.11, pytest; optional `openai` behind `[live]`.

---

### Task 1: LiveAgent + MockTransport + parse/retries

**Files:** `agents/live.py`, `agents/mock_transport.py`, `tests/test_live_agent.py`

- Transport protocol: `complete(prompt: str) -> str`
- `MockTransport(responses: list[str] | dict)` for offline tests
- `LiveAgent(transport=..., api_key=..., require_creds=True)` — if `transport` provided, skip openai/key checks
- `generate`: build prompt from pair/variant/task_family asking for JSON matching oracle keys; parse JSON from response; max 2 retries on parse fail; return artifact dict; on total failure raise or return empty with caller setting infra_error
- Also expose `generate_with_meta(...) -> (artifact, meta)` with tokens/latency proxies

### Task 2: Experiment dry-run + manifesto + runs/

**Files:** `eval/experiment.py`, `eval/manifest.py`, `tests/test_experiment_preflight.py`

- `--dry-run`: write prompts + manifesto, no model calls
- `--mock-live`: use MockTransport with canned clean/weak artifacts
- `--model`, `--replications`, `--seed`, `--policy`, `--intents` filter
- Output under `runs/<run_id>/manifest.json`, `metrics.json`, `episodes.jsonl`, `prompts/` (dry-run)
- `manifest.json`: git_sha, pairs_hash, config, timestamp

### Task 3: Pair schema + expand seed

**Files:** `pairs/schema.py`, `pairs/validate.py`, 2+ new pair JSON files, `tests/test_pair_schema.py`

- Validate required keys on load
- Add `mesaflow_rf09b.json` (alt vague threshold) and `synthetic_trace_link.json` (minimal 3rd family stub: `task_families` field OR new family `trace_link` with binary oracle) — prefer expand mesaflow + one `data/pairs/extra_rf_cardinal_soft.json`
- Keep loader compatible

### Task 4: Tolerant oracles

**Files:** `eval/oracles.py`, `tests/test_oracles_tolerant.py`

- Score by required keys subset: all oracle_spec keys present and equal; ignore extra artifact keys
- Populate `OracleResult.checks` per key
- Keep equality-failing cases for weakened stubs

### Task 5: IRR tooling

**Files:** `protocol/irr.py`, `protocol/annotation_template.csv`, `tests/test_irr.py`

- Load two annotator CSV/JSONL (`episode_id,mode,severity`)
- Cohen's kappa (nominal) for mode; simple percent agreement
- Deprecate synthetic demo as default; keep function but mark

### Task 6: Offline H1–H5 analysis

**Files:** `eval/thesis_analysis.py`, `tests/test_thesis_analysis.py`

- Read episodes JSONL → tables: H1 paired Δ, H2 by smell type, H3/H4 baseline AUROCs if features available, H5 mitigation if report present
- Write `runs/.../thesis_tables.json` or `eval/thesis_tables.json`
- Negative boundary flags when effect≈0

### Task 7: Template mitigation (non-blind oracle copy)

**Files:** `mitigation/rewrite.py`, `mitigation/templates.py`, tests

- `rewrite_mode="oracle"` (current) vs `rewrite_mode="template"`
- Template rewrite: smell-type specific string transforms (e.g. vague → insert "more than 5 minutes" from pair metadata / oracle_spec)
- Must not literally assign `pair["clean_requirement"]` in template mode; reconstruct from smell type + oracle_spec fields
- Pipeline flag `rewrite_mode`

### Task 8: Release hygiene

**Files:** `CITATION.cff`, `CHANGELOG.md`, Makefile targets, `.gitignore` for `runs/`, docs update

### Task 9: Acceptance + CI green

**Files:** `tests/test_pre_experiment_acceptance.py`

Offline only; then PR.
