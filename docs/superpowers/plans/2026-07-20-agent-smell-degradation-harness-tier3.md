# Agent Smell Degradation Harness — Tier 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship C5 mitigation baselines (rewrite / clarify), expand C3 protocol packaging, and produce a dissertation-ready offline report — without breaking Tier 1–2 CI (still secret-free).

**Architecture:** Mitigation runs *before* stub generation on smelly variants: detect smell → rewrite to clean text *or* inject a simulated clarification answer → generate with policy `rewrite` / `clarify`. Compare degradation rates vs `direct` under smell-blind conditions to evaluate the mitigation trade-off (H5). Protocol packaging aggregates paired stats, taxonomy, baselines, and mitigation deltas into `eval/dissertation_bundle.json` + markdown summary.

**Tech Stack:** Python ≥3.11, pytest, existing harness packages. No new required deps. Live mitigation LLM optional behind `[live]` (offline stubs first).

**Spec:** `docs/superpowers/specs/2026-07-20-agent-smell-degradation-harness-design.md` Tier 3 / C3 / C5 / H5.  
**Depends on:** Tier 1–2 on `main`.

**Out of scope:** Real human clarification UI; production AgentOps; claiming mitigation is always beneficial.

---

## File structure (lock-in)

```text
mitigation/
  __init__.py
  detect.py           # static smell flags from pair.smell / heuristics
  rewrite.py          # smelly → clean requirement (deterministic stub)
  clarify.py          # simulated Q&A → clean constraint text
  pipeline.py         # apply policy before agent.generate
  tradeoff.py         # cost/quality comparison report
protocol/
  paired_stats.py     # (exists) extend lightly
  packaging.py        # dissertation bundle builder
  reliability.py      # placeholder IRR/agreement helpers (synthetic demo)
eval/
  mitigation_report.py  # python -m eval.mitigation_report
  dissertation_bundle.py
agents/
  stub.py             # honor policy rewrite/clarify via mitigated requirement text
  policies.py         # already has REWRITE/CLARIFY
tests/
  test_mitigation_detect.py
  test_mitigation_rewrite.py
  test_mitigation_clarify.py
  test_mitigation_pipeline.py
  test_mitigation_tradeoff.py
  test_protocol_packaging.py
  test_tier3_acceptance.py
docs/
  dissertation/
    README.md         # how to export bundle for thesis
```

**Mitigation behavioral contract (offline stub):**

| Policy | Behavior |
|--------|----------|
| `direct` | Use requirement text as-is (current Tier 1) |
| `static_smell` | Detect/label smell; still generate from original smelly text |
| `rewrite` | Replace smelly requirement with `pair["clean_requirement"]` (oracle: rewrite recovers clean). Record `rewrite_delta` metadata. |
| `clarify` | Emit one clarification question from smell type; apply canned answer that restores clean constraint; then generate. Record `clarification_question` + `answer`. |

Under `failure_mode="smell-blind"` + policy `direct`: high `paired_degradation_rate`.  
Under same FM + policy `rewrite` or `clarify`: `paired_degradation_rate` drops toward 0 (mitigation helps).  
Trade-off report also records `interaction_overhead` (clarify steps) and `token_proxy_cost` (requirement length after rewrite).

**Mitigation gate (report, not CI-blocking):**  
`mitigation_beneficial` true if rewrite/clarify reduces `paired_degradation_rate` vs direct under smell-blind by ≥ threshold (e.g. 0.5 absolute). Also report when cost overhead rises. Never claim always-positive.

---

### Task 1: Smell detect + rewrite stubs

**Files:**
- Create: `mitigation/detect.py`, `mitigation/rewrite.py`, `tests/test_mitigation_detect.py`, `tests/test_mitigation_rewrite.py`
- Modify: `mitigation/__init__.py`

- [ ] **Step 1: Failing tests**

```python
from mitigation.detect import detect_smell
from mitigation.rewrite import rewrite_requirement
from pairs.loader import load_all_pairs

def test_detect_flags_smelly_pair():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    d = detect_smell(pair["smelly_requirement"], pair["smell"])
    assert d.detected is True
    assert d.smell_type == "vague_threshold"

def test_rewrite_restores_clean_text():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    out = rewrite_requirement(pair["smelly_requirement"], pair)
    assert out.text == pair["clean_requirement"]
    assert out.changed is True
```

- [ ] **Step 2–4: Implement + PASS**

- [ ] **Step 5: Commit** `feat: add smell detect and rewrite mitigation stubs`

---

### Task 2: Clarify simulation

**Files:**
- Create: `mitigation/clarify.py`, `tests/test_mitigation_clarify.py`

- [ ] **Step 1: Failing test** — for RF-09, clarification question mentions threshold; applying canned answer yields clean requirement text.

```python
from mitigation.clarify import build_clarification, apply_clarification_answer

def test_clarify_rf09_restores_clean():
    pair = ...
    q = build_clarification(pair)
    assert "5" in q.question or "threshold" in q.question.lower()
    resolved = apply_clarification_answer(pair, q, answer=q.simulated_answer)
    assert resolved.text == pair["clean_requirement"]
```

Map smell types → question templates + simulated answers that encode clean oracle constraints.

- [ ] **Step 2–5: Implement + Commit** `feat: add clarification simulation for mitigation`

---

### Task 3: Mitigation pipeline + stub policy wiring

**Files:**
- Create: `mitigation/pipeline.py`, `tests/test_mitigation_pipeline.py`
- Modify: `eval/runner.py` to accept `policy: str = "direct"` and pass mitigated requirement into stub
- Modify: `agents/stub.py` if needed to accept optional `requirement_override`

**Lock-in:**  
`prepare_requirement(pair, variant, policy) -> PreparedRequirement` with fields: `text`, `policy`, `mitigation_meta`.  
Runner uses `text` for episode `requirement_text` when generating; smell-blind still weakens on `variant=smelly` **unless** mitigation restored clean text — for rewrite/clarify on smelly, treat generation as if clean oracle_spec (stub generates clean artifact). Simplest: if policy in {rewrite, clarify} and variant smelly, call stub with `variant="clean"` after mitigation (document as "mitigation recovers clean intent").

- [ ] **Step 1: Failing test** — smell-blind + rewrite → paired_degradation_rate == 0; smell-blind + direct → > 0

- [ ] **Step 2–5: Implement + Commit** `feat: wire mitigation policies into eval runner`

---

### Task 4: Mitigation trade-off report (C5 / H5)

**Files:**
- Create: `mitigation/tradeoff.py`, `eval/mitigation_report.py`, `tests/test_mitigation_tradeoff.py`
- Modify: `Makefile` add `mitigation` target

`build_mitigation_report(work_dir)` runs `run_eval` for policies `direct`, `rewrite`, `clarify` under `failure_mode="smell-blind"` (and happy direct control). Emits:

```json
{
  "direct": {"paired_degradation_rate": ...},
  "rewrite": {...},
  "clarify": {...},
  "mitigation_beneficial": true,
  "overhead": {"clarify_steps_mean": 1.0, "rewrite_char_delta_mean": ...},
  "gate": {"passed": true, "detail": "..."}
}
```

Write `eval/mitigation_report.json`. Runnable: `python -m eval.mitigation_report`.

- [ ] **Step 1–5: TDD + Commit** `feat: add mitigation trade-off report`

---

### Task 5: Protocol packaging + reliability helpers (C3)

**Files:**
- Create: `protocol/packaging.py`, `protocol/reliability.py`, `eval/dissertation_bundle.py`, `tests/test_protocol_packaging.py`
- Create: `docs/dissertation/README.md`

Bundle includes: design-spec path, pair inventory, taxonomy mode counts, analysis report summary (call or embed paths), mitigation report summary, paired_stats, synthetic IRR demo (`agreement_rate` placeholder with documented limitation).

`python -m eval.dissertation_bundle` → `eval/dissertation_bundle.json` + `docs/dissertation/BUNDLE_SUMMARY.md` (generated; gitignore the generated md if noisy, or commit template only).

- [ ] **Step 1–5: TDD + Commit** `feat: add dissertation protocol packaging`

---

### Task 6: Docs + Tier 3 acceptance

**Files:**
- Modify: `README.md`, `docs/interop.md`, `docs/superpowers/plans/README.md`
- Create: `tests/test_tier3_acceptance.py`
- Update `.gitignore` for new report artifacts

Acceptance (offline):
1. rewrite/clarify reduce degradation vs direct under smell-blind
2. mitigation_report writes gate fields
3. dissertation_bundle exports without secrets
4. Tier 1 `make all` / gate still green
5. CI workflow unchanged (no secrets)

- [ ] **Step 1–5: Implement + Commit** `test: add Tier 3 offline acceptance criteria`

---

## Verification

```bash
pytest -q
make all
python -m eval.mitigation_report
python -m eval.dissertation_bundle
```

CI remains secret-free; do not add live API calls to GitHub Actions.

---

## Exit criteria (Tier 3 / dissertation DoD substrate)

- [ ] C5 rewrite + clarify offline baselines with trade-off report
- [ ] Mitigation gate reports benefit vs overhead (no always-positive claim)
- [ ] C3 packaging bundle for thesis export
- [ ] Tier 1–2 acceptance still green
