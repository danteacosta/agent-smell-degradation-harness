# Thesis and Product Layers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the thesis protocol evidence-ready and expose a separate product reliability-gate layer across the three repositories.

**Architecture:** ARP owns only neutral lifecycle, manifest, decision, and serialization contracts. Agent-smell owns scientific dataset, feature/label separation, grouped estimands, and thesis reports. RAG owns product policy/reporting and consumes ARP instead of duplicating domain contracts.

**Tech Stack:** Python 3.11+, Pydantic/dataclasses already used by each repository, pytest, JSONL/JSON Schema, SARIF-compatible JSON.

---

### Task 1: Freeze the shared ARP envelope

**Files:**
- Modify: `src/agent_reliability_protocol/contracts.py`
- Modify: `src/agent_reliability_protocol/events.py`
- Modify: `src/agent_reliability_protocol/interchange.py`
- Create: `tests/test_cross_consumer_envelope.py`

- [ ] Add failing tests for ARP 2.0.5 lifecycle event round-trip, monotonic sequence, checkpoint/order, schema negotiation, run/intent/project identity, and hard failure on invalid envelopes.
- [ ] Implement only neutral ARP v2 fields and validation; keep package pinning at `v2.0.5`.
- [ ] Add a real agent-smell thesis-run producer test emitting `RunManifest` plus ordered T0–T3 events, a shared fixture replayed by both consumers, and a runtime import guard proving `protocol_next` is fixture-only.
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
- [ ] Add deterministic versioned policy config, approve/warn/block exit-code semantics, stable reason/evidence IDs, and hard-fail contract errors.
- [ ] Test every policy branch: precedence block>warn>approve; exit codes 0/10/20; contract error 30; SARIF note/warning/error; neutral ARP pass/fail remains distinct.
- [ ] Add isolation tests proving RAG operational metrics cannot enter H1-H3 artifacts.
- [ ] Run the RAG suite and commit.

### Task 3: Make the thesis feature and label planes explicit

**Files:**
- Modify: `feature_plane/models.py`
- Modify: `feature_plane/extractors.py`
- Modify: `eval/runner.py`
- Create: `feature_plane/deployable.py`
- Create: `feature_plane/upper_bound.py`
- Test: `tests/`

- [ ] Add failing tests that reject smell/variant/oracle/final-artifact/terminal-validation/label fields, including nested and serialized payloads and post-cutoff events.
- [ ] Implement separate deployable and metadata-upper-bound schemas.
- [ ] Make checkpoint extraction consume provider-produced ARP T0-T3 events only; assert upper-bound features are not used by primary selection or estimands.
- [ ] Add a static import guard against label/oracle modules and a training API test that rejects upper-bound features.
- [ ] Run focused tests and commit.

### Task 4: Align confirmatory estimands and splits

**Files:**
- Modify: `protocol/paired_stats.py`
- Modify: `eval/h2_detection.py`
- Modify: `eval/analysis_report.py`
- Modify: `eval/prepilot.py`
- Test: `tests/`

- [ ] Add failing tests for ordinal paired deltas, intent-clustered bootstrap/permutation, PR-AUC, calibration, false-alert rate, warning coverage, practical margins, and estimand IDs.
- [ ] Implement grouped train/calibration/test selection with disjoint source-intent/project groups; select models on train groups, fit calibration/thresholds on calibration groups, and evaluate only on held-out test groups. Emit the exact ordinal-delta and PR-AUC estimand IDs and CI/p-value methods.
- [ ] Reject duplicated/near-cloned source intents before counting, using canonicalized token hashes plus a declared similarity threshold and explicit approved-paraphrase exceptions; require project holdouts, enforce 12×2×5 counts, and emit deterministic split manifests.
- [ ] Remove boolean-only acceptance gates and define missing-group behavior explicitly.
- [ ] Run the full scientific suite and commit.

### Task 5: Add real traceability and annotation contracts

**Files:**
- Modify: `eval/prepilot.py`
- Modify: `label_plane/human_annotation/__init__.py`
- Modify: `label_plane/adjudication/`
- Create: `tasks/traceability.py`
- Test: `tests/`

- [ ] Add failing tests for traceability links with artifact IDs, hashes, claim/line spans, and missing/stale/tampered/self-reported links.
- [ ] Implement an acceptance-criteria rubric, blinded sampling metadata, duplicate subset, IRR statistic and CI, disagreement/missing-label policy, adjudication provenance, and raw-label export.
- [ ] Predeclare Krippendorff alpha, bootstrap CI, ≥0.70 target, <0.60 adjudication/claim-narrowing policy, blinded fields, rubric training, and duplicate-subset size in the annotation schema and BDD tests.
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
- [ ] Add import-dependency and artifact-schema isolation tests; thesis never imports product policy and product never consumes thesis labels.
- [ ] Run all repository suites, diff checks, and cross-consumer fixture checks.
- [ ] Push branches, open/update PRs, and publish release notes.
