# Confirmatory Validity and Product Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the thesis protocol scientifically valid and the sister product demonstrable, while keeping the current external-data gates fail closed.

**Architecture:** The ASD repository owns confirmatory data, provider checkpoints, feature extraction, annotations, and H2 analysis. The RAG repository owns candidate-memory ingestion, semantic QA, persistence, and the pre-merge product report. They exchange only versioned ARP/provenance contracts; thesis labels never enter the product gate.

**Tech Stack:** Python 3.11, pytest, JSONL manifests, ARP 2.x, deterministic bootstrap/statistics, JSON/SARIF product reports.

---

### Task 1: Add failing tests for genuine provider checkpoints

**Files:**
- Test: `tests/test_provider_checkpoints.py`
- Modify: `eval/runner.py`
- Modify: `agents/live.py` or provider adapter contract

- [ ] **Step 1: Write tests** proving a provider-generated interpretation and plan are recorded in T1/T2, and that experiment-only `variant`/`smell` metadata is absent from deployable attributes.
- [ ] **Step 2: Run** `pytest tests/test_provider_checkpoints.py -q` and verify failure against the current deterministic runner.
- [ ] **Step 3: Implement** a provider checkpoint interface returning structured interpretation/plan summaries; record only allowlisted fields in pre-final events.
- [ ] **Step 4: Run** the focused test and the lifecycle tests.
- [ ] **Step 5: Commit** `feat: capture provider-generated pre-final checkpoints`.

### Task 2: Replace degenerate provenance features

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

### Task 3: Bind H2 to primary human labels and frozen feature manifests

**Files:**
- Test: `tests/test_h2_labels_and_feature_manifest.py`
- Modify: `eval/h2_detection.py`
- Modify: `label_plane/human_annotation/__init__.py`
- Create: `eval/feature_manifest.py`

- [ ] **Step 1: Write tests** requiring a versioned annotation manifest, rejecting `oracle_passed` as the confirmatory label, and rejecting unbound `h2_scores` injection.
- [ ] **Step 2: Run** focused tests and verify they fail.
- [ ] **Step 3: Implement** label loading with missing-label fail-closed behavior and feature-score binding to dataset/trace/feature hashes.
- [ ] **Step 4: Preserve a clearly named non-confirmatory demo path** for oracle/stub examples.
- [ ] **Step 5: Run** H2 and annotation tests.
- [ ] **Step 6: Commit** `feat: bind confirmatory H2 to labels and feature manifests`.

### Task 4: Complete H2 delta, clustered CI, and claim decision

**Files:**
- Test: `tests/test_h2_confirmatory.py`
- Modify: `eval/h2_detection.py`
- Create: `eval/confirmatory_report.py`
- Modify: `protocol/paired_stats.py`

- [ ] **Step 1: Write tests** for baseline PR-AUCs, provenance-minus-best-baseline delta, cluster bootstrap CI, frozen `0.05` margin, and deterministic claim status.
- [ ] **Step 2: Run** focused tests and verify missing report fields fail.
- [ ] **Step 3: Implement** report generation using source-intent/project clusters and no test-set model selection.
- [ ] **Step 4: Add false-alert, warning-coverage, lead-time, and decision-utility secondary metrics.
- [ ] **Step 5: Run** all H2/statistics tests.
- [ ] **Step 6: Commit** `feat: emit confirmatory H2 delta and claim report`.

### Task 5: Add sample-size/project gates and reproducibility manifest

**Files:**
- Test: `tests/test_confirmatory_dataset.py`
- Test: `tests/test_reproducibility_manifest.py`
- Modify: `label_plane/datasets.py`
- Create: `eval/reproducibility_manifest.py`
- Modify: `docs/thesis/preregistration.md`

- [ ] **Step 1: Write tests** distinguishing pilot/descriptive from confirmatory status and requiring the configured project/intention precision target.
- [ ] **Step 2: Run** focused tests and verify the current seven-source seed remains blocked.
- [ ] **Step 3: Implement** explicit sample-size policy, dataset/code/environment/provider/feature/split hashes, and a dry-run manifest.
- [ ] **Step 4: Update** the thesis wording to state the narrowed primary construct, project minimum, and exploratory fallback.
- [ ] **Step 5: Commit** `docs: freeze confirmatory validity and reproducibility gates`.

### Task 6: Align ARP versions and clean-environment execution

**Files:**
- Modify: `pyproject.toml` in both repositories
- Test: `tests/test_protocol_interchange.py` in RAG
- Create/modify: lock or setup documentation as supported by the repositories

- [ ] **Step 1: Write a test** that reports the supported ARP version and rejects an incompatible runtime without an explicit compatibility path.
- [ ] **Step 2: Run** the test in a clean environment and confirm the current overlay-dependent behavior.
- [ ] **Step 3: Align the dependency pins or add a tested compatibility matrix.
- [ ] **Step 4: Run** both repositories without `PYTHONPATH` overlays.
- [ ] **Step 5: Commit** `build: make ARP compatibility reproducible`.

### Task 7: Make product memory and semantic QA end-to-end

**Files:**
- Test: `tests/test_product_memory_ingress.py`
- Test: `tests/test_semantic_quality.py`
- Modify: `product_memory/candidates.py`
- Modify: `observability/semantic_lint.py`
- Modify: `loop/run.py`
- Modify: `docs/product/README.md`

- [ ] **Step 1: Write tests** for session-handoff ingestion, source-reference validation, retention metadata, reviewer audit, policy findings, and a product decision that includes ROI metrics.
- [ ] **Step 2: Run** focused tests and verify the current library-only behavior fails.
- [ ] **Step 3: Implement** a typed ingress adapter, bounded retention/PII policy hooks, deterministic rule registry, and product report wiring.
- [ ] **Step 4: Keep thesis labels and estimands out of the product data path.
- [ ] **Step 5: Run** product integration and smoke tests.
- [ ] **Step 6: Commit** `feat: connect product memory and semantic QA to sessions`.

### Task 8: Add related-work and artifact-evaluation documentation

**Files:**
- Modify: `docs/thesis/preregistration.md`
- Modify: `docs/thesis-product-boundary.md`
- Modify: `README.md` in both repositories
- Create: `docs/research/artifact-evaluation.md`

- [ ] **Step 1: Add** explicit positioning against requirements-smell impact studies, clarification systems, and prefix monitors.
- [ ] **Step 2: Document** the novelty boundary and non-claims.
- [ ] **Step 3: Document** replay bundle, negative controls, ablations, provider matrix, and artifact-evaluation checklist.
- [ ] **Step 4: Commit** `docs: position novelty and artifact evaluation`.

### Task 9: Verification gate

- [ ] **Step 1:** Run ASD full tests in a clean copy.
- [ ] **Step 2:** Run RAG full tests in a clean copy without overlays.
- [ ] **Step 3:** Run static import/leakage checks and product smoke tests.
- [ ] **Step 4:** Inspect git diffs for SOLID/clean-code issues and confirm no thesis labels enter product paths.
- [ ] **Step 5:** Push branches, open/update PRs, inspect checks/comments, and merge only verified PRs.
