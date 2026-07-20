# Agent Smell Degradation Harness — Tier 0–1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship an offline-first CI twin of `rag-reliability-harness` that detects requirement-smell-induced semantic degradation via paired clean/smelly episodes (codegen + test_gen), three injectable failure modes, and ATDD gates — Tier 0–1 / public repo DoD.

**Architecture:** Harness-core (`pairs` → stub `agents` → `observability` JSONL → oracles → `eval` paired Δ → `gates`) with empty thesis overlays. Failure modes are orthogonal to agent policies. Live LLM (`make experiment`) is stubbed as a no-op/documented deferral until Tier 2.

**Tech Stack:** Python ≥3.11, pytest, PyYAML, Makefile, GitHub Actions. No API keys in default CI.

**Spec:** `docs/superpowers/specs/2026-07-20-agent-smell-degradation-harness-design.md`

**Out of scope for this plan (separate plans later):** Tier 2 taxonomy/baselines/live LLM; Tier 3 mitigation/full protocol packaging.

---

## File structure (lock-in)

```text
agent_harness/
  __init__.py
  types.py                 # Episode, Smell, OracleResult dataclasses
pairs/
  __init__.py
  loader.py                # load pairs from data/pairs/*.json
  data/                    # (actual data under repo data/pairs/)
agents/
  __init__.py
  stub.py                  # deterministic stub generator
  policies.py              # Policy enum: direct | static_smell | rewrite | clarify
observability/
  __init__.py
  tracing.py               # JSONL provenance writer + semantic vs operational events
eval/
  __init__.py
  __main__.py
  oracles.py               # codegen + test_gen meta-oracles per intent
  metrics.py               # paired Δ, degradation detection flags
  runner.py                # run episodes → metrics JSON
  simulate_regressions.py  # FM1–FM3
  thresholds.yaml
  baselines/ci.json
gates/
  __init__.py
  __main__.py
  run.py                   # check_gate
taxonomy/__init__.py       # overlay stub
protocol/__init__.py
baselines/__init__.py
mitigation/__init__.py
data/pairs/
  mesaflow_rf04.json … rf13.json   # clean + smelly texts + oracle specs
tests/
  test_types.py
  test_pairs.py
  test_stub_agent.py
  test_oracles.py
  test_provenance.py
  test_eval_runner.py
  test_gate.py
  test_simulate.py
  test_acceptance.py
docs/interop.md
README.md
Makefile
pyproject.toml
.github/workflows/eval.yml
```

**Artifact format (decision):** stubs emit **structured JSON** (not free-form code strings) so oracles stay deterministic offline.

- `codegen` example RF-09: `{"delay_threshold_minutes": 5, "comparator": ">"}`
- `test_gen` example RF-09: `{"must_reject_minutes": [0, 5], "must_accept_minutes": [6], "criterion": "delay_minutes > 5"}`

Smell-blind stubs emit weakened forms (`comparator: ">="` or empty `must_reject_minutes`).

---

### Task 1: Scaffold project + package layout

**Files:**
- Create: `pyproject.toml`, `Makefile`, `agent_harness/__init__.py`, `pairs/__init__.py`, `agents/__init__.py`, `observability/__init__.py`, `eval/__init__.py`, `gates/__init__.py`, `taxonomy/__init__.py`, `protocol/__init__.py`, `baselines/__init__.py`, `mitigation/__init__.py`, `docs/interop.md`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "agent-smell-degradation-harness"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]
live = []  # Tier 2

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = [
  "agent_harness*",
  "pairs*",
  "agents*",
  "observability*",
  "eval*",
  "gates*",
  "taxonomy*",
  "protocol*",
  "baselines*",
  "mitigation*",
]
```

- [ ] **Step 2: Write minimal `Makefile`**

```makefile
.PHONY: test eval simulate gate experiment all
test:
	pytest -q
eval:
	python -m eval
simulate:
	python -m eval.simulate_regressions
gate:
	python -m gates
experiment:
	@echo "make experiment is Tier 2 (live LLM); not enabled in Tier 1"
all: test eval simulate gate
```

Note: `gate` reads `eval/last_run.json` produced by `make eval`. `simulate` must **not** overwrite that file (see Task 9).
- [ ] **Step 3: Write `docs/interop.md`** (contracts with sister harness: `eval/`, `gates/`, `observability/`, JSONL, thresholds, ATDD, no shared code)

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml Makefile docs/interop.md agent_harness pairs agents observability eval gates taxonomy protocol baselines mitigation
git commit -m "chore: scaffold harness packages and interop docs"
```

---

### Task 2: Episode types (TDD)

**Files:**
- Create: `agent_harness/types.py`, `tests/test_types.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_types.py
from agent_harness.types import Episode, Smell, TaskFamily, Variant

def test_episode_roundtrip_fields():
    ep = Episode(
        episode_id="e1",
        intent_id="RF-09",
        variant=Variant.CLEAN,
        smell=None,
        task_family=TaskFamily.CODEGEN,
        policy="direct",
        mode="stub",
        replication_id=0,
    )
    assert ep.intent_id == "RF-09"
    assert ep.semantic_label is None
```

- [ ] **Step 2: Run test — expect FAIL** (`ModuleNotFoundError` or import error)

```bash
pytest tests/test_types.py -v
```

- [ ] **Step 3: Implement types**

```python
# agent_harness/types.py
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class Variant(str, Enum):
    CLEAN = "clean"
    SMELLY = "smelly"

class TaskFamily(str, Enum):
    CODEGEN = "codegen"
    TEST_GEN = "test_gen"

@dataclass(frozen=True)
class Smell:
    category: str
    type: str
    injection_rule: str

@dataclass
class OracleResult:
    passed: bool
    detail: str
    checks: dict[str, bool] = field(default_factory=dict)

@dataclass
class Episode:
    episode_id: str
    intent_id: str
    variant: Variant
    smell: Smell | None
    task_family: TaskFamily
    policy: str
    mode: str
    replication_id: int = 0
    requirement_text: str = ""
    artifact: dict[str, Any] | None = None
    oracle_result: OracleResult | None = None
    semantic_label: str | None = None  # ok | degraded | infra_error
    provenance_path: str | None = None
    cost: float = 0.0
    latency_ms: float = 0.0
    model: str | None = None
    provider: str | None = None
```

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add agent_harness/types.py tests/test_types.py
git commit -m "feat: add episode schema types"
```

---

### Task 3: MesaFlow pair data + loader

**Files:**
- Create: `data/pairs/mesaflow_rf04.json`, `mesaflow_rf07.json`, `mesaflow_rf09.json`, `mesaflow_rf13.json`, `pairs/loader.py`, `tests/test_pairs.py`

Each JSON file shape:

```json
{
  "intent_id": "RF-09",
  "clean_requirement": "New orders are delayed after more than 5 minutes.",
  "smelly_requirement": "New orders delayed after significant time.",
  "smell": {
    "category": "semantic",
    "type": "vague_threshold",
    "injection_rule": "replace exact threshold with vague temporal phrase"
  },
  "oracle_spec": {
    "codegen": {
      "delay_threshold_minutes": 5,
      "comparator": ">"
    },
    "test_gen": {
      "must_reject_minutes": [0, 5],
      "must_accept_minutes": [6],
      "criterion": "delay_minutes > 5"
    }
  }
}
```

RF-04 / RF-07 / RF-13 `oracle_spec` shapes (use these exact keys in the JSON files):

```json
// RF-04
"oracle_spec": {
  "codegen": {"order_id_pattern": "^P-\\d{3}$"},
  "test_gen": {
    "must_reject_ids": ["P-1", "P-1004", "X-014"],
    "must_accept_ids": ["P-014"],
    "criterion": "P- plus exactly three digits"
  }
}
// RF-07
"oracle_spec": {
  "codegen": {"sort_key": "elapsed_time_asc"},
  "test_gen": {
    "required_sort_key": "elapsed_time_asc",
    "forbidden_sort_keys": ["order_code", "seed"],
    "criterion": "cards oldest to newest by time"
  }
}
// RF-13
"oracle_spec": {
  "codegen": {"cardinality": 5, "selection": "oldest_active"},
  "test_gen": {
    "exact_cardinality": 5,
    "criterion": "display exactly 5 oldest active orders"
  }
}
```

- [ ] **Step 1: Write failing loader test**

```python
from pairs.loader import load_all_pairs, list_intent_ids

def test_loads_four_mesaflow_intents():
    pairs = load_all_pairs()
    assert set(list_intent_ids(pairs)) == {"RF-04", "RF-07", "RF-09", "RF-13"}
    rf09 = next(p for p in pairs if p["intent_id"] == "RF-09")
    assert "5" in rf09["clean_requirement"]
    assert rf09["smell"]["type"] == "vague_threshold"
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Add four JSON files + `pairs/loader.py`**

```python
from __future__ import annotations
from pathlib import Path
import json

DEFAULT_PAIRS_DIR = Path(__file__).resolve().parents[1] / "data" / "pairs"

def load_all_pairs(pairs_dir: Path | str = DEFAULT_PAIRS_DIR) -> list[dict]:
    root = Path(pairs_dir)
    out = []
    for path in sorted(root.glob("*.json")):
        with path.open(encoding="utf-8") as f:
            out.append(json.load(f))
    return out

def list_intent_ids(pairs: list[dict]) -> list[str]:
    return [p["intent_id"] for p in pairs]
```

- [ ] **Step 4: Run — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add data/pairs pairs/loader.py tests/test_pairs.py
git commit -m "feat: add MesaFlow clean/smelly pair seeds and loader"
```

---

### Task 4: Provenance JSONL recorder

**Files:**
- Create: `observability/tracing.py`, `tests/test_provenance.py`

- [ ] **Step 1: Failing test**

```python
from observability.tracing import ProvenanceRecorder

def test_records_semantic_and_operational_events(tmp_path):
    path = tmp_path / "trace.jsonl"
    rec = ProvenanceRecorder(path)
    rec.operational("latency", {"ms": 10})
    rec.semantic("constraint_extract", {"delay_threshold_minutes": 5})
    rec.close()
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 2
    assert '"kind": "semantic"' in lines[1]
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement recorder** (append JSON objects with `kind`: `operational` | `semantic`, `name`, `payload`, `ts`)

- [ ] **Step 4: Run — PASS**

- [ ] **Step 5: Commit** `feat: add provenance JSONL recorder`

---

### Task 5: Stub agent (correct + smell-blind behaviors)

**Files:**
- Create: `agents/policies.py`, `agents/stub.py`, `tests/test_stub_agent.py`

- [ ] **Step 1: Failing tests**

```python
from agents.stub import StubAgent
from pairs.loader import load_all_pairs

def test_stub_codegen_clean_rf09_emits_exact_threshold():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    agent = StubAgent(failure_mode=None)
    art = agent.generate(pair, variant="clean", task_family="codegen")
    assert art == pair["oracle_spec"]["codegen"]

def test_stub_smell_blind_weakens_rf09():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    agent = StubAgent(failure_mode="smell-blind")
    art = agent.generate(pair, variant="smelly", task_family="codegen")
    assert art["comparator"] != ">"
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement**

**Behavioral contract (lock-in):**
- Happy path (`failure_mode=None`): stub always emits the **clean** `oracle_spec` for the task family (recovers / ignores smell). Paired Δ ≈ 0 → gate passes.
- `smell-blind`: on `variant=smelly`, emit weakened artifact; on `clean`, emit correct. Paired degradation detectable.
- `oracle-mismatch`: emit plausible-but-wrong artifact for the intent (even on clean) when MODE is set — proves oracle catches semantic miss.
- `provenance-collapse`: emit correct artifact; simulate path skips semantic provenance events (handled in Task 9 runner/simulate, not in stub payload).

Also add minimal `agents/policies.py`:

```python
from enum import Enum
class Policy(str, Enum):
    DIRECT = "direct"
    STATIC_SMELL = "static_smell"
    REWRITE = "rewrite"
    CLARIFY = "clarify"
```

Tier 1 stub uses `Policy.DIRECT` only; other values are reserved for Tier 2–3.

Implement `StubAgent.generate(...)` accordingly; include `test_gen` weakening (e.g. empty `must_reject_minutes`).

- [ ] **Step 4: Run — PASS**

- [ ] **Step 5: Commit** `feat: add deterministic stub agent with smell-blind mode`

---

### Task 6: Oracles (codegen + test_gen)

**Files:**
- Create: `eval/oracles.py`, `tests/test_oracles.py`

- [ ] **Step 1: Failing tests** covering RF-04/07/09/13 for both families; at least one failing smell-blind artifact per family.

```python
from eval.oracles import score_artifact

def test_rf09_codegen_pass():
    spec = {"delay_threshold_minutes": 5, "comparator": ">"}
    r = score_artifact("RF-09", "codegen", {"delay_threshold_minutes": 5, "comparator": ">"}, spec)
    assert r.passed is True

def test_rf09_test_gen_rejects_vague():
    spec = {"must_reject_minutes": [0, 5], "must_accept_minutes": [6], "criterion": "delay_minutes > 5"}
    weak = {"must_reject_minutes": [], "must_accept_minutes": [6], "criterion": "after significant time"}
    r = score_artifact("RF-09", "test_gen", weak, spec)
    assert r.passed is False
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement `score_artifact(intent_id, task_family, artifact, oracle_spec) -> OracleResult`**

Equality / subset checks per intent; keep logic table-driven from `oracle_spec` rather than hardcoding every RF in deep branches where possible.

- [ ] **Step 4: Run — PASS**

- [ ] **Step 5: Commit** `feat: add codegen and test_gen oracles`

---

### Task 7: Eval runner + paired metrics

**Files:**
- Create: `eval/metrics.py`, `eval/runner.py`, `eval/__main__.py`, `tests/test_eval_runner.py`

Metrics JSON keys (gate inputs):

```yaml
# produced by runner
paired_degradation_rate: float   # fraction of intent×family pairs where smelly fails and clean passes
oracle_pass_rate_clean: float
oracle_pass_rate_smelly: float
semantic_provenance_coverage: float  # fraction episodes with ≥1 semantic provenance event
degradation_detected: bool         # paired_degradation_rate >= threshold floor logic handled in gate
```

- [ ] **Step 1: Failing test** — happy path runner yields `paired_degradation_rate == 0` and `semantic_provenance_coverage == 1`

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement runner**

For each pair × `{codegen, test_gen}` × `{clean, smelly}`:
1. Create provenance file
2. Generate artifact via stub
3. **Score oracle first** (anti-circularity)
4. Then assert/write provenance semantic event `constraint_extract` from artifact fields
5. Aggregate metrics; write `eval/last_run.json`

- [ ] **Step 4: Run — PASS**

- [ ] **Step 5: Commit** `feat: add paired eval runner and metrics`

---

### Task 8: Gate + thresholds + baseline

**Files:**
- Create: `eval/thresholds.yaml`, `eval/baselines/ci.json`, `gates/run.py`, `gates/__main__.py`, `tests/test_gate.py`

`gates/__main__.py` and `check_gate` load metrics from `eval/last_run.json` by default (same contract as sister harness). `make gate` / `python -m gates` therefore require a prior `make eval` / `python -m eval`.

```yaml
# eval/thresholds.yaml
floors:
  oracle_pass_rate_clean: 1.0
  semantic_provenance_coverage: 1.0
ceilings:
  paired_degradation_rate: 0.0
require_degradation_detector: true
```

Gate logic:
- Fail if `oracle_pass_rate_clean` < floor
- Fail if `paired_degradation_rate` > ceiling (happy path expects 0)
- Fail if `semantic_provenance_coverage` < floor
- For simulate “after” paths, the **detector** must mark catch correctly — see Task 9

Also support blind gate helper (operational-only) used to show before_catch_rate=0 for FM3.

- [ ] **Step 1: Failing test** — good metrics pass; metrics with degradation or missing semantic provenance fail

- [ ] **Step 2–4: Implement + PASS**

- [ ] **Step 5: Commit** `feat: add CI gate thresholds and checker`

---

### Task 9: Simulate FM1–FM3 + before/after report

**Files:**
- Create: `eval/simulate_regressions.py`, `tests/test_simulate.py`

Modes:
- `smell-blind` → stub failure_mode smell-blind → `paired_degradation_rate > 0`
- `oracle-mismatch` → wrong artifacts → clean oracle pass rate drops
- `provenance-collapse` → runner skips semantic events → coverage 0

**Isolation rule (required):** `simulate_regressions` writes only to `eval/sim_report.json` (and optional temp dirs). It must **never** overwrite `eval/last_run.json`. Happy-path metrics for `make gate` come solely from `python -m eval`.

Catch rates:
- **before:** evaluate with blind checker (ignore paired_degradation / semantic coverage)
- **after:** full `check_gate` on in-memory / temp metrics for that FM
- Expect before=0.0, after=1.0 for each mode (mirror sister harness AT5)

CLI: `python -m eval.simulate_regressions` and `--mode smell-blind` via argparse.

- [ ] **Step 1: Failing tests** for each mode catch + `simulate_all` report shape; assert `eval/last_run.json` unchanged when a pre-existing file is present

- [ ] **Step 2–4: Implement + PASS**

- [ ] **Step 5: Commit** `feat: simulate three smell-degradation failure modes`

---

### Task 10: ATDD acceptance tests

**Files:**
- Create: `tests/test_acceptance.py`

Mirror sister AT1–AT5:

1. Happy-path offline gate passes (no keys)
2. FM1 fails gate
3. FM2 fails gate
4. FM3 fails gate
5. `simulate_all` before/after 0→1; workflow has no `secrets.` / OPENAI / ANTHROPIC

**Also (spec advisory):** at least one assertion that simulate covers a `test_gen` episode (e.g. inspect sim report `task_families_exercised` includes `test_gen`, or run one FM on RF-09 test_gen explicitly).

- [ ] **Step 1: Write acceptance tests (will fail until CI file exists for AT5 partially)**

- [ ] **Step 2: Run — note failures**

- [ ] **Step 3: Fix any runner gaps so AT1–AT4 pass**

- [ ] **Step 4: Commit** `test: add ATDD acceptance criteria AT1–AT4`

---

### Task 11: CI workflow + README + Makefile polish

**Files:**
- Create: `.github/workflows/eval.yml`, `README.md`
- Modify: `Makefile`

Workflow (no secrets):

```yaml
name: eval-gate
on: [push, pull_request]
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: pytest -q
      - run: python -m eval
      - run: python -m gates
```

README sections: flow mermaid, 3 failure modes table, quickstart, attribution that MesaFlow is local seed, link to design spec, twin narrative vs `rag-reliability-harness`.

- [ ] **Step 1: Add workflow + README**

- [ ] **Step 2: Ensure AT5 passes**

```bash
pytest tests/test_acceptance.py -v
make all
```

- [ ] **Step 3: Commit** `ci: add offline eval-gate workflow and README`

---

### Task 12: Overlay stubs + freeze Tier 1 DoD checklist

**Files:**
- Ensure overlay packages import cleanly
- Modify: `README.md` with Tier 0–3 roadmap pointer
- Create: `docs/superpowers/plans/README.md` note that Tier 2/3 plans are follow-ons

- [ ] **Step 1: Add one-liner modules**

```python
# taxonomy/__init__.py
"""C1 overlay — activated in Tier 2."""
```

(same for protocol, baselines, mitigation)

- [ ] **Step 2: Run full suite**

```bash
pytest -q && python -m eval && python -m eval.simulate_regressions && python -m gates
# or: make all
```

Expected: all green. `last_run.json` reflects happy path; `sim_report.json` reflects FM catch rates.
- [ ] **Step 3: Commit** `chore: mark thesis overlays and Tier 1 DoD complete`

---

## Tier 2–3 (not in this plan)

Follow-on plans should cover:
- **Tier 2:** `taxonomy/` population, `baselines/` feature families, live adapter under `agents/live.py`, `make experiment`
- **Tier 3:** `mitigation/` rewrite/clarify, protocol stats, dissertation packaging

---

## Execution handoff

After this plan is approved by the plan reviewer and you choose an execution mode, implement task-by-task with TDD and frequent commits.
