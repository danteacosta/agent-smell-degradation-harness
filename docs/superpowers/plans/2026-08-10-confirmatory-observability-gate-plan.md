# Confirmatory observability and product-gate Implementation Plan

> For agentic workers: use executing-plans or subagent-driven-development to implement this plan task-by-task.

**Goal:** Close the remaining P0/P1 validity gaps and expose an actionable semantic pre-merge gate.

**Architecture:** Keep the feature plane independent from labels/oracles. Extract typed, variable summaries from T1-T3 events, bind confirmatory rows to trace/checkpoint manifests, and let a product adapter render evidence without modifying scientific estimands.

**Tech Stack:** Python 3.11+, pytest, JSONL/ARP 2.0.6, SARIF.

---

### Task 1: Make provenance features payload-sensitive

**Files:**
- Modify: feature_plane/extractors.py
- Modify: feature_plane/validation.py
- Test: tests/test_feature_plane.py

- [ ] Add failing tests for two T1-T3 payloads with identical event names but different constraints, ambiguities, contradictions, checks, and errors.
- [ ] Run the focused tests and confirm they fail because current extraction only observes constraint_extract presence/field count.
- [ ] Implement typed extraction from interpretation.completed, plan.completed, tool.completed, and legacy constraint_extract.
- [ ] Implement a bounded semantic-risk score using counts/coverage, not variant/smell/oracle fields.
- [ ] Run focused tests and the existing feature-plane suite.

### Task 2: Harden confirmatory feature manifests

**Files:**
- Modify: eval/feature_manifest.py
- Modify: eval/h2_detection.py
- Test: tests/test_h2_labels_and_feature_manifest.py

- [ ] Add failing tests for missing trace hash, missing checkpoint binding, non-finite scores, and embedded score injection.
- [ ] Run the focused tests and confirm each rejection.
- [ ] Require h2-features/v2, a feature version, trace hash, checkpoint event IDs, cutoff sequence, and finite family scores.
- [ ] Reject episode-level h2_scores/feature_scores in all confirmatory calls.
- [ ] Run focused tests and the full H2 suite.

### Task 3: Expand confirmatory H2 reporting

**Files:**
- Modify: eval/h2_detection.py
- Modify: eval/calibration.py
- Test: tests/test_h2_robustness.py

- [ ] Add a failing assertion requiring test-set PR-AUC for every family, prevalence, calibrated false-alert rate, lead time placeholder/status, and automatic claim decision.
- [ ] Implement the report fields without selecting a family after observing test labels.
- [ ] Preserve clustered delta CI and negative controls.
- [ ] Run the H2 suite and inspect the JSON report shape.

### Task 4: Make the product gate actionable

**Files:**
- Modify: wedge/check.py
- Modify: wedge/fixtures.py
- Test: tests/test_wedge.py

- [ ] Add failing tests requiring constraint/checkpoint/confidence/recommended-action evidence in warn/block results and SARIF.
- [ ] Implement deterministic evidence mapping from pre-final features to product messages.
- [ ] Add utility summary fields for captured regressions and review cost.
- [ ] Run wedge, utility, and integration tests.

### Task 5: Document data-dependent blockers and replay acceptance

**Files:**
- Modify: README.md
- Modify: docs/thesis/preregistration.md
- Create: docs/research/confirmatory-data-acquisition.md
- Test: tests/test_reproducible_bundle.py

- [ ] Add a failing replay acceptance test requiring provider mode, label source, dataset hash, and feature-manifest hash in the bundle.
- [ ] Implement the manifest/report metadata and explicit blocked status for the current seven-source seed.
- [ ] Document that external dataset, human annotation, and live providers remain required before a confirmatory claim.
- [ ] Run the complete suite and a clean replay.

### Task 6: Verify and integrate

- [ ] Run ASD full suite in a writable clean copy with ARP 2.0.6.
- [ ] Run RAG full suite and product smoke bundle.
- [ ] Review the diff for leakage, SOLID, and clean-code issues.
- [ ] Commit each coherent slice and push the branches.
- [ ] Merge only after all fresh verification commands pass.

