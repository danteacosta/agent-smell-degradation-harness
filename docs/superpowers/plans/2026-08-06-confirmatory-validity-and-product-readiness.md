# Confirmatory Validity and Product Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the thesis protocol scientifically valid and the sister product demonstrable, while keeping the current external-data gates fail closed.

**Architecture:** The ASD repository owns confirmatory data, provider checkpoints, feature extraction, annotations, and H2 analysis. The RAG repository owns candidate-memory ingestion, semantic QA, persistence, and the pre-merge product report. They exchange only versioned ARP/provenance contracts; thesis labels never enter the product gate.

**Tech Stack:** Python 3.11, pytest, JSONL manifests, ARP 2.x, deterministic bootstrap/statistics, JSON/SARIF product reports.

---

### Task 1: Freeze protocol and ARP compatibility before collection

**Files:**
- Create: `docs/thesis/arp-compatibility-matrix.md`
- Create: `docs/thesis/confirmatory-freeze.json`
- Modify: `docs/thesis/preregistration.md`

- [ ] **Step 1: Write tests** requiring the wire schema `2.0.5`, documenting tested package versions, and rejecting provider runs whose freeze hashes do not match.
- [ ] **Step 2: Run** the focused preflight and verify the current un-frozen state fails closed.
- [ ] **Step 3: Implement** the compatibility matrix and canonical freeze manifest with SHA-256 hashes for preregistration, feature schema, annotation rubric, split algorithm, and analysis code.
- [ ] **Step 4: Commit** the freeze before any confirmatory provider execution.

### Task 2: Add failing tests for genuine provider checkpoints

**Files:**
- Test: `tests/test_provider_checkpoints.py`
- Modify: `eval/runner.py`
- Modify: `agents/live.py` or provider adapter contract

- [ ] **Step 1: Write tests** proving a provider-generated interpretation and plan are recorded in T1/T2, and that experiment-only `variant`/`smell` metadata is absent from deployable attributes.
- [ ] **Step 2: Run** `pytest tests/test_provider_checkpoints.py -q` and verify failure against the current deterministic runner.
- [ ] **Step 3: Implement** a provider checkpoint interface returning structured interpretation/plan summaries; record only allowlisted fields in pre-final events.
- [ ] **Step 4: Run** the focused test and the lifecycle tests.
- [ ] **Step 5: Commit** `feat: capture provider-generated pre-final checkpoints`.

### Task 3: Replace degenerate provenance features

**Files:**
- Test: `tests/test_deployable_features.py`
- Modify: `feature_plane/deployable.py`
- Modify: `feature_plane/validation.py`
- Modify: `eval/runner.py`

- [ ] **Step 1: Write tests** for constraint counts/types, quantity detection, unresolved references, assumptions, contradictions, revisions, and validation coverage; assert terminal keys are rejected.
- [ ] **Step 2: Run** the focused tests and confirm the current constant feature output fails.
- [ ] **Step 3: Implement** the versioned allowlisted feature schema and an informative-feature preflight that marks constant families non-informative.
- [ ] **Step 4: Add an ablation/negative-control test** showing shuffled provenance cannot be mistaken for valid provenance.
- [ ] **Step 5: Run** feature, leakage, and architecture tests.
- [ ] **Step 6: Commit** `feat: make provenance features behaviorally informative`.

### Task 4: Bind H2 to primary human labels and frozen feature manifests

**Files:**
- Test: `tests/test_h2_labels_and_feature_manifest.py`
- Modify: `eval/h2_detection.py`
- Modify: `label_plane/human_annotation/__init__.py`
- Create: `eval/feature_manifest.py`

- [ ] **Step 1: Write tests** requiring a versioned annotation manifest, rejecting `oracle_passed` as the confirmatory label, and rejecting unbound `h2_scores` injection.
- [ ] **Step 2: Run** focused tests and verify they fail.
- [ ] **Step 3: Implement** label loading with missing-label fail-closed behavior, a frozen 20% duplicate subset, adjudication records, and feature-score binding to dataset/trace/feature hashes.
- [ ] **Step 4: Preserve a clearly named non-confirmatory demo path** for oracle/stub examples.
- [ ] **Step 5: Run** H2 and annotation tests.
- [ ] **Step 6: Commit** `feat: bind confirmatory H2 to labels and feature manifests`.

### Task 5: Complete H2 delta, clustered CI, and claim decision

**Files:**
- Test: `tests/test_h2_confirmatory.py`
- Modify: `eval/h2_detection.py`
- Create: `eval/confirmatory_report.py`
- Modify: `protocol/paired_stats.py`

- [ ] **Step 1: Write tests** for the frozen binary label mapping, train-only baseline selection, source-intent cluster unit, provenance-minus-best-baseline delta, cluster bootstrap CI with degenerate resamples retained, frozen `0.05` margin, and deterministic claim status.
- [ ] **Step 2: Run** focused tests and verify missing report fields fail.
- [ ] **Step 3: Implement** report generation using source-intent/project clusters and no test-set model selection.
- [ ] **Step 4: Keep** false-alert, warning-coverage, lead-time, and decision-utility metrics in the RAG product report, not in the primary H2 estimand.
- [ ] **Step 5: Run** all H2/statistics tests.
- [ ] **Step 6: Commit** `feat: emit confirmatory H2 delta and claim report`.

### Task 6: Add sample-size/project gates and reproducibility manifest

**Files:**
- Test: `tests/test_confirmatory_dataset.py`
- Test: `tests/test_reproducibility_manifest.py`
- Modify: `label_plane/datasets.py`
- Create: `eval/reproducibility_manifest.py`
- Modify: `docs/thesis/preregistration.md`

- [ ] **Step 1: Write tests** distinguishing pilot/descriptive from confirmatory status and requiring 24 independent intents, 6 projects, at least 4 intents per project, and at least 8 intents in every split after holdout. A frozen power/precision simulation may raise these minima but may not lower them.
- [ ] **Step 2: Run** focused tests and verify the current seven-source seed remains blocked.
- [ ] **Step 3: Implement** explicit sample-size policy, dataset/code/environment/provider/feature/split hashes, and a dry-run manifest.
- [ ] **Step 4: Update** the thesis wording to state the narrowed primary construct, project minimum, and exploratory fallback.
- [ ] **Step 5: Commit** `docs: freeze confirmatory validity and reproducibility gates`.

### Task 7: Make product memory and semantic QA end-to-end

**Files (RAG worktree `/Users/dantecosta/Projects/rag-reliability-harness/.worktrees/product-layer`):**
- Test: `tests/test_product_memory_ingress.py`
- Test: `tests/test_semantic_quality.py`
- Modify: `product_memory/candidates.py`
- Modify: `observability/semantic_lint.py`
- Modify: `loop/run.py`
- Modify: `docs/product/README.md`

- [ ] **Step 1: Write tests** for session-handoff ingestion, source-reference validation, payload limits, retention metadata, deletion/access audit, reviewer audit, rule versions/order, stale-worker behavior, policy findings, and a product decision that includes ROI metrics.
- [ ] **Step 2: Run** focused tests and verify the current library-only behavior fails.
- [ ] **Step 3: Implement** a typed ingress adapter, bounded retention/PII policy hooks, deterministic rule registry, atomic/concurrent append boundary, explicit stale/unknown fail-closed semantics, and product report wiring.
- [ ] **Step 4: Keep** thesis labels and estimands out of the product data path.
- [ ] **Step 5: Run** product integration and smoke tests.
- [ ] **Step 6: Commit** `feat: connect product memory and semantic QA to sessions`.

### Task 8: Align ARP versions and clean-environment execution

**Files:**
- Modify: `pyproject.toml` in `/Users/dantecosta/Projects/rag-reliability-harness/.worktrees/product-layer`
- Test: `tests/test_protocol_interchange.py` in `/Users/dantecosta/Projects/rag-reliability-harness/.worktrees/product-layer`
- Create: `docs/thesis/arp-compatibility-matrix.md`

- [ ] **Step 1: Write a test** that reports the supported wire schema/package versions and rejects incompatible runtimes without an explicit compatibility path.
- [ ] **Step 2: Run** the test in a clean environment and confirm the current overlay-dependent behavior.
- [ ] **Step 3: Align** the dependency pins or add the tested compatibility matrix.
- [ ] **Step 4: Run** both repositories without `PYTHONPATH` overlays.
- [ ] **Step 5: Commit** `build: make ARP compatibility reproducible`.

### Task 9: Add related-work and artifact-evaluation documentation

**Files:**
- Modify: `docs/thesis/preregistration.md`
- Modify: `docs/thesis-product-boundary.md`
- Modify: `README.md` in both repositories
- Create: `docs/research/artifact-evaluation.md`

- [ ] **Step 1: Add** explicit positioning against requirements-smell impact studies, clarification systems, and prefix monitors.
- [ ] **Step 2: Document** the novelty boundary and non-claims.
- [ ] **Step 3: Document** replay bundle, negative controls, ablations, provider matrix, and artifact-evaluation checklist.
- [ ] **Step 4: Commit** `docs: position novelty and artifact evaluation`.

### Task 10: Verification gate

- [ ] **Step 1:** Run ASD full tests in a clean copy.
- [ ] **Step 2:** Run RAG full tests in a clean copy without overlays.
- [ ] **Step 3:** Run static import/leakage checks and product smoke tests.
- [ ] **Step 4:** Inspect git diffs for SOLID/clean-code issues and confirm no thesis labels enter product paths.
- [ ] **Step 5:** Push branches, open/update PRs, inspect checks/comments, and merge only verified PRs.
