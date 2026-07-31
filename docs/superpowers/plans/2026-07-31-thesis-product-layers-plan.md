# Thesis and Product Layers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the thesis protocol evidence-ready and expose a separate product reliability-gate layer across the three repositories.

**Architecture:** ARP owns only neutral lifecycle, manifest, decision, and serialization contracts. Agent-smell owns scientific dataset, feature/label separation, grouped estimands, and thesis reports. RAG owns product policy/reporting and consumes ARP instead of duplicating domain contracts.

**Tech Stack:** Python 3.11+, Pydantic/dataclasses already used by each repository, pytest, JSONL/JSON Schema, SARIF-compatible JSON.

---

### Task 1: Freeze the shared ARP envelope

**Files:**
- Modify: `src/agent_reliability_protocol/models.py`
- Modify: `src/agent_reliability_protocol/events.py`
- Create: `tests/test_cross_consumer_envelope.py`

- [ ] Add failing tests for lifecycle event round-trip, monotonic sequence, checkpoint, and manifest compatibility.
- [ ] Implement only neutral ARP v2 fields and validation.
- [ ] Run ARP tests and commit.

### Task 2: Migrate the RAG consumer to ARP

**Files:**
- Modify: `rag_harness/reliability.py`
- Modify: `loop/run.py`
- Modify: `protocol_next/events.py`
- Modify: `protocol_next/replay.py`
- Test: `tests/`

- [ ] Add a failing integration test proving the producer emits ARP `RunManifest` and lifecycle events.
- [ ] Replace duplicate local domain models with ARP imports; retain RAG-specific payloads as adapters.
- [ ] Add product gate report serialization and SARIF projection.
- [ ] Run the RAG suite and commit.

### Task 3: Make the thesis feature and label planes explicit

**Files:**
- Modify: `feature_plane/models.py`
- Modify: `feature_plane/extractors.py`
- Modify: `eval/runner.py`
- Create: `feature_plane/deployable.py`
- Create: `feature_plane/upper_bound.py`
- Test: `tests/`

- [ ] Add failing tests that reject smell/variant/oracle/final-artifact fields from deployable features.
- [ ] Implement separate deployable and metadata-upper-bound schemas.
- [ ] Make checkpoint extraction consume ARP events only.
- [ ] Run focused tests and commit.

### Task 4: Align confirmatory estimands and splits

**Files:**
- Modify: `protocol/paired_stats.py`
- Modify: `eval/h2_detection.py`
- Modify: `eval/analysis_report.py`
- Modify: `eval/prepilot.py`
- Test: `tests/`

- [ ] Add failing tests for ordinal paired deltas, intent-clustered bootstrap, paired permutation, PR-AUC, calibration, false-alert rate, warning coverage, and practical margins.
- [ ] Implement grouped train/test selection and calibrated thresholds within folds.
- [ ] Reject duplicated source intents and require explicit project/variant provenance.
- [ ] Remove boolean-only acceptance gates.
- [ ] Run the full scientific suite and commit.

### Task 5: Add real traceability and annotation contracts

**Files:**
- Modify: `eval/prepilot.py`
- Modify: `label_plane/human_annotation/__init__.py`
- Modify: `label_plane/adjudication/`
- Create: `tasks/traceability.py`
- Test: `tests/`

- [ ] Add failing tests for traceability links against target artifacts and blinded annotation metadata.
- [ ] Implement the task adapter, rubric, adjudication, and IRR export.
- [ ] Keep LLM judges secondary and never part of the primary label.
- [ ] Run tests and commit.

### Task 6: Publish the product layer and documentation

**Files:**
- Modify: RAG README and CLI modules.
- Create: `docs/product/` in RAG.
- Modify: ASD dissertation/protocol docs.
- Create: cross-repository acceptance checklist.

- [ ] Add a one-command product demo producing approve/warn/block plus SARIF/JSON evidence.
- [ ] Document thesis-vs-product boundaries and limitations.
- [ ] Run all repository suites, diff checks, and cross-consumer fixture checks.
- [ ] Push branches, open/update PRs, and publish release notes.
