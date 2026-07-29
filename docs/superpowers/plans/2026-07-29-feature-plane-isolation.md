# Feature-plane Isolation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make all deployable provenance features independent of oracle specifications, terminal artifacts, and labels.

**Architecture:** Add `feature_plane` with an allowlisted input model and self-contained Tier-A filter. Keep `observability.features` as an adapter. Add a `label_plane` facade for terminal scoring, migrate every deployable consumer to neutral semantic features, and retain `output_only` as an explicitly retrospective baseline.

**Tech Stack:** Python 3.11+, standard-library dataclasses and JSON, pytest.

---

## File structure

- Create: `feature_plane/models.py` — immutable allowlisted feature input.
- Create: `feature_plane/extractors.py` — Tier-A filtering and neutral feature families.
- Create: `feature_plane/validation.py` — neutral semantic risk scoring.
- Create: `feature_plane/__init__.py` and `label_plane/__init__.py` — public plane APIs.
- Modify: `observability/features.py`, `baselines/features.py`, `baselines/compare.py`, `eval/h2_detection.py`, `eval/runner.py`, `wedge/check.py`, `pyproject.toml`.
- Create: `tests/test_feature_plane.py`.
- Modify: `tests/test_tier_ab.py`, `tests/test_h2_detection.py`, `tests/test_baselines.py`, `tests/test_wedge.py`.

### Task 1: Write the feature-plane acceptance tests

**Files:**
- Create: `tests/test_feature_plane.py`
- Modify: `tests/test_tier_ab.py`

- [ ] **Step 1: Write a failing allowlist test.**

```python
from feature_plane import FeatureEpisodeInput

def test_feature_input_copies_only_pre_final_episode_fields():
    source = {
        "intent_id": "RF-09", "task_family": "codegen", "variant": "smelly",
        "smell": {"type": "vague_threshold"}, "requirement_text": "late",
        "artifact": {"delay_threshold_minutes": 5}, "oracle_passed": True,
    }
    feature_input = FeatureEpisodeInput.from_episode(source)
    assert feature_input.requirement_text == "late"
    assert not hasattr(feature_input, "artifact")
```

- [ ] **Step 2: Run the test to prove RED.**

Run: `pytest tests/test_feature_plane.py::test_feature_input_copies_only_pre_final_episode_fields -v`

Expected: FAIL because `feature_plane` does not exist.

- [ ] **Step 3: Write failing temporal-isolation tests.**

Use a JSONL trace with two Tier-A events and one Tier-B `oracle_verdict`. Assert the extracted operational count is 2. Create two source episodes differing only in `artifact`, `oracle_spec`, `oracle_passed`, `semantic_label`, and `mutation_score`; after `FeatureEpisodeInput.from_episode`, assert equal feature results.

- [ ] **Step 4: Write failing architecture tests.**

```python
def test_feature_plane_cannot_import_label_plane():
    source = _package_source("feature_plane")
    for forbidden in ("label_plane", "eval.oracles", "pairs.loader", "oracle_spec"):
        assert forbidden not in source

def test_deployable_baseline_delegation_cannot_read_terminal_data():
    source = Path("baselines/features.py").read_text(encoding="utf-8")
    for forbidden in ("pairs.loader", "oracle_spec", 'episode.get("artifact")'):
        assert forbidden not in source
```

- [ ] **Step 5: Run the focused tests and confirm RED.**

Run: `pytest tests/test_feature_plane.py tests/test_tier_ab.py -v`

Expected: failure only because the neutral API and compatibility behavior are absent.

- [ ] **Step 6: Commit the tests.**

```bash
git add tests/test_feature_plane.py tests/test_tier_ab.py
git commit -m "test: specify pre-final feature isolation"
```

### Task 2: Implement the isolated feature plane

**Files:**
- Create: `feature_plane/__init__.py`, `feature_plane/models.py`, `feature_plane/extractors.py`, `feature_plane/validation.py`
- Modify: `observability/features.py`, `pyproject.toml`
- Test: `tests/test_feature_plane.py`, `tests/test_tier_ab.py`

- [ ] **Step 1: Implement `FeatureEpisodeInput` as a frozen dataclass.**

Its exact fields are `intent_id`, `task_family`, `variant`, `smell`, and `requirement_text`. `from_episode` copies exactly these fields and no terminal field.

- [ ] **Step 2: Run the model test to prove GREEN.**

Run: `pytest tests/test_feature_plane.py::test_feature_input_copies_only_pre_final_episode_fields -v`

Expected: PASS.

- [ ] **Step 3: Implement `extract_pre_final_features`.**

It loads JSONL itself, drops events with `tier == "B"` and events named `oracle_verdict`, then returns static-smell and operational features plus:

```python
"provenance_semantic": {
    "constraint_event_present": ...,
    "constraint_field_count": ...,
    "constraint_has_comparator": ...,
    "semantic_event_count": ...,
}
```

It must not receive or inspect an artifact, oracle, label, or mutation score. Implement `semantic_risk(features)`: return `1.0` when the constraint event is missing, otherwise `0.0`.

- [ ] **Step 4: Make the compatibility adapter delegate.**

Replace `observability.features.extract_tier_a_features` with:

```python
return extract_pre_final_features(FeatureEpisodeInput.from_episode(episode), provenance_path)
```

Remove the oracle loader, artifact comparison, and legacy semantic fields.

- [ ] **Step 5: Register packages and run focused tests.**

Run: `pytest tests/test_feature_plane.py tests/test_tier_ab.py -v`

Expected: PASS.

- [ ] **Step 6: Commit the implementation.**

```bash
git add feature_plane observability/features.py pyproject.toml tests/test_feature_plane.py tests/test_tier_ab.py
git commit -m "feat: isolate pre-final feature extraction"
```

### Task 3: Establish label-plane ownership

**Files:**
- Create: `label_plane/__init__.py`
- Modify: `eval/runner.py`, `wedge/check.py`, `pyproject.toml`
- Modify: `tests/test_wedge.py`

- [ ] **Step 1: Write a failing production-import test.**

Assert `eval.runner` and `wedge.check` import `score_artifact` and `score_test_gen_mutation` from `label_plane`; preserve existing direct unit tests of `eval.oracles` and `eval.mutation`.

- [ ] **Step 2: Verify RED.**

Run: `pytest tests/test_wedge.py -v`

Expected: FAIL because the facade or migrated imports are absent.

- [ ] **Step 3: Implement and migrate the facade.**

```python
from eval.mutation import score_test_gen_mutation
from eval.oracles import score_artifact

__all__ = ["score_artifact", "score_test_gen_mutation"]
```

Change only production evaluation callers to import from `label_plane`.

- [ ] **Step 4: Verify GREEN.**

Run: `pytest tests/test_oracles.py tests/test_oracles_tolerant.py tests/test_mutation.py tests/test_wedge.py -v`

Expected: PASS.

- [ ] **Step 5: Commit the label boundary.**

```bash
git add label_plane eval/runner.py wedge/check.py pyproject.toml tests/test_wedge.py
git commit -m "refactor: expose terminal scoring through label plane"
```

### Task 4: Migrate deployable consumers to the neutral contract

**Files:**
- Modify: `baselines/features.py`, `baselines/compare.py`, `eval/h2_detection.py`, `wedge/check.py`
- Modify: `tests/test_baselines.py`, `tests/test_h2_detection.py`, `tests/test_wedge.py`

- [ ] **Step 1: Write failing consumer regressions.**

Make H2, `compare_baselines`, and wedge Tier-A risk consume a semantic family with only `constraint_event_present`, `constraint_field_count`, `constraint_has_comparator`, and `semantic_event_count`. Assert no consumer requires `constraint_match` or `is_weak_comparator`.

- [ ] **Step 2: Verify RED.**

Run: `pytest tests/test_baselines.py tests/test_h2_detection.py tests/test_wedge.py -v`

Expected: failures limited to accesses to legacy semantic fields.

- [ ] **Step 3: Delegate baseline deployable features.**

Have `baselines.features.extract_features` delegate static, operational, and provenance-semantic families to `feature_plane`. Keep local `output_only` as a terminal retrospective baseline and do not route it through the feature plane.

- [ ] **Step 4: Use the neutral semantic risk.**

Replace score logic in `baselines.compare`, `eval.h2_detection`, and wedge Tier-A risk with `feature_plane.semantic_risk`. Preserve the independent label-plane warnings in wedge.

- [ ] **Step 5: Verify GREEN.**

Run: `pytest tests/test_baselines.py tests/test_h2_detection.py tests/test_wedge.py -v`

Expected: PASS.

- [ ] **Step 6: Commit the migration.**

```bash
git add baselines/features.py baselines/compare.py eval/h2_detection.py wedge/check.py tests/test_baselines.py tests/test_h2_detection.py tests/test_wedge.py
git commit -m "refactor: consume neutral provenance features"
```

### Task 5: Verify the complete harness behavior

**Files:**
- Test: `tests/`

- [ ] **Step 1: Run all tests.**

Run: `pytest -q`

Expected: all tests pass.

- [ ] **Step 2: Run the offline acceptance flow.**

Run: `make all`

Expected: test, evaluation, simulation, and gate steps complete without credentials.

- [ ] **Step 3: Perform final static and clean-code review.**

Run: `git diff main...HEAD --check && git diff main...HEAD`

Expected: no whitespace errors; one-way dependencies from feature-plane to neither labels nor domains.

- [ ] **Step 4: Commit verification-only corrections if needed.**

```bash
git add <verified-files>
git commit -m "test: verify feature plane isolation"
```

