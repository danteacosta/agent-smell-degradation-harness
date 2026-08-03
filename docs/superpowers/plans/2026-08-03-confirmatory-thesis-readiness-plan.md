# Confirmatory Thesis Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Make the thesis evidence-ready by enforcing the 12×2×5 multi-project design, implementing a real grouped H2 protocol, adding blinded human annotation/IRR, enabling provider-backed runs and traceability tasks, and freezing a reproducible preregistered package.

**Architecture:** The scientific harness remains the sole owner of dataset, labels, estimands, and analysis artifacts. Provider adapters emit neutral ARP events; traceability is an explicit task manifest rather than a heuristic validator. Product repositories consume only the resulting neutral protocol and never enter thesis estimands.

**Tech Stack:** Python 3.11+, pytest, stdlib CSV/JSON, optional provider callables, ARP 2.0.5 wire schema / package 2.0.6.

---

### Task 1: Confirmatory dataset manifest

**Files:**
- Modify: `pairs/*.json`, `pairs/schema.py`, `pairs/loader.py`
- Modify: `label_plane/datasets.py`, `eval/prepilot.py`
- Test: `tests/test_confirmatory_dataset.py`

- [ ] Write failing tests for 12 unique source intents, non-empty project IDs spanning ≥3 projects, two natural variants, five replications, unique design keys, and near-clone rejection.
- [ ] Add five genuinely independent source intents with provenance/source URLs and declared project/defect-family metadata; do not duplicate or rename existing intents.
- [ ] Emit a deterministic manifest containing source hash, project holdout groups, similarity threshold, approved-paraphrase exceptions, and 12×2×5 counts.
- [ ] Make pre-pilot fail closed before agent execution when any metadata or provenance requirement is incomplete.
- [ ] Run focused dataset tests and commit.

### Task 2: H2 train/calibration/test protocol

**Files:**
- Modify: `eval/h2_detection.py`, `eval/prepilot.py`, `protocol/paired_stats.py`
- Create: `eval/splits.py`, `eval/calibration.py`
- Test: `tests/test_h2_confirmatory.py`, `tests/test_split_manifest.py`

- [ ] Write failing tests proving train, calibration, and test source-intent/project groups are pairwise disjoint and variants/replications remain together.
- [ ] Implement deterministic project-aware grouped splits and a train-only feature/model selection step.
- [ ] Fit calibration and threshold only on calibration groups; evaluate PR-AUC, false-alert rate, warning coverage, and practical-margin decisions only on held-out test groups.
- [ ] Export split manifest, selected model/configuration, calibration parameters, threshold provenance, and missing-group behavior.
- [ ] Run focused H2 tests and commit.

### Task 3: Blinded human annotation and IRR

**Files:**
- Modify: `label_plane/human_annotation/__init__.py`, `label_plane/adjudication/__init__.py`, `protocol/irr.py`
- Create: `label_plane/annotation_protocol.py`, `label_plane/irr.py`
- Test: `tests/test_human_annotation_contract.py`, `tests/test_krippendorff_alpha.py`

- [ ] Write failing tests for blinded fields, annotator IDs, double-coded duplicate subset, missing labels, disagreement export, adjudication provenance, and secondary-judge separation.
- [ ] Implement annotation records with variant/defect/oracle/model/artifact redaction and rubric/version metadata.
- [ ] Implement Krippendorff’s alpha for nominal/ordinal labels, deterministic bootstrap CI, ≥0.70 target, and <0.60 adjudication/claim-narrowing decision.
- [ ] Export raw labels, missing labels, disagreement rows, adjudicated labels, and annotator/rubric provenance.
- [ ] Run focused annotation tests and commit.

### Task 4: Provider-backed runs and traceability task manifest

**Files:**
- Modify: `eval/runner.py`, `eval/experiment.py`, `eval/task_adapters.py`, `eval/prepilot.py`
- Create: `eval/provider_manifest.py`, `tasks/traceability.json`
- Test: `tests/test_provider_run_manifest.py`, `tests/test_traceability_manifest.py`

- [ ] Write failing tests requiring provider/model/version/configuration/seed/cost/latency metadata and explicit stub-vs-real run labels.
- [ ] Add a provider adapter interface that records request/response metadata without storing secrets or terminal artifacts in deployable traces.
- [ ] Add a versioned traceability task manifest with claim paths, artifact hashes, missing/stale/tampered/self-reported cases, and make the pre-pilot execute it explicitly.
- [ ] Validate each episode against ARP manifest/envelope and export task-level traceability outcomes.
- [ ] Run focused provider and traceability tests and commit.

### Task 5: Preregistration, power analysis, and reproducible package

**Files:**
- Create: `docs/thesis/preregistration.md`, `docs/thesis/power_analysis.md`, `docs/thesis/data_dictionary.md`
- Modify: `eval/dissertation_bundle.py`, `docs/thesis-product-boundary.md`, `README.md`
- Test: `tests/test_reproducible_bundle.py`, `tests/test_preregistration.py`

- [ ] Write failing tests requiring frozen hypothesis IDs, estimands, exclusions, thresholds, sample-size rationale, dataset hash, code SHA, environment lock, and analysis version.
- [ ] Add the preregistration and power-analysis artifacts with explicit pilot-versus-confirmatory boundaries.
- [ ] Extend the dissertation bundle with manifest, raw labels, disagreement/adjudication exports, split manifest, H1/H2 reports, and checksums.
- [ ] Add a one-command reproducibility check that validates hashes and reruns analysis without network access.
- [ ] Run packaging tests and commit.

### Task 6: Final verification and publication

- [ ] Run all focused and full scientific suites in a clean environment.
- [ ] Run `git diff --check`, static import/security checks, SOLID/clean-code review, and ARP cross-consumer fixtures.
- [ ] Run a real-provider smoke test only when credentials are explicitly configured; otherwise prove the offline path and record the limitation.
- [ ] Update the Google thesis document with the final acceptance matrix and unresolved empirical prerequisites.
- [ ] Push branches, open/update PRs, and publish release notes only after all checks pass.
