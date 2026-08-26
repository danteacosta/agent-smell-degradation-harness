# Requirements-smell verification efficacy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Measure whether an oracle-free verifier can flag behaviorally degraded requirement-smell episodes before terminal evaluation, with reproducible artifacts and honest efficiency criteria.

**Architecture:** Extend the existing discovery bundle with portable pre-final ARP-compatible trace projections. Add a focused `eval/discovery_verifier.py` module that consumes only an allowlisted episode projection and observable trace, emits a frozen risk/action decision, and evaluates that decision against a separate behavioral label plane. Keep the existing replay/wedge, confirmatory feature plane, and ARP repositories unchanged unless a contract gap is found.

**Tech Stack:** Python 3.9+, JSONL/JSON artifacts, existing `feature_plane` extractor, existing behavioral sandbox/oracle, pytest when available, Google Docs connector for the proposal.

---

### Task 1: Define the verifier API with failing behavioral tests

**Files:**
- Create: `tests/test_discovery_verifier.py`
- Create: `eval/discovery_verifier.py`

- [ ] **Step 1: Write failing tests for the observable input boundary**

  Cover an allowlisted episode projection, terminal-field rejection in an observable trace, deterministic scoring, and a smelly textual signal that is higher than its clean counterpart without reading `variant` or `smell`.

- [ ] **Step 2: Run the focused tests and confirm the expected failure**

  Run: `python3 -m pytest -q tests/test_discovery_verifier.py`

  Expected: collection or assertion failure because `eval.discovery_verifier` does not exist yet. If pytest is unavailable, record that limitation and run the equivalent assertions with a temporary in-memory Python command after implementation.

- [ ] **Step 3: Implement the smallest observable projection and rule-pack API**

  Add typed constants/dataclasses or plain mappings for the schema version, frozen thresholds, allowed fields, text signals, score, action, signal checkpoint, and leakage rejection. Reuse `DeployableFeatureInput` and `extract_deployable_features`; do not import `label_plane`, `eval.oracles`, or read terminal episode keys while deciding.

- [ ] **Step 4: Run the focused tests and confirm they pass**

  Run: `python3 -m pytest -q tests/test_discovery_verifier.py`

  Expected: all focused verifier tests pass.

### Task 2: Add efficacy metrics and grouped strata

**Files:**
- Modify: `eval/discovery_verifier.py`
- Modify: `tests/test_discovery_verifier.py`

- [ ] **Step 1: Write failing metric assertions**

  Assert confusion counts, recall, precision, F1, false-alert rate, balanced accuracy, paired score discrimination, repeated-run reproducibility, and project/smell strata. Include an empty/ineligible-label case that reports a non-success status rather than fabricating a pass.

- [ ] **Step 2: Run the focused test and confirm it fails for the missing metrics**

  Run: `python3 -m pytest -q tests/test_discovery_verifier.py -k metrics`

- [ ] **Step 3: Implement metric aggregation**

  Evaluate only behavior episodes with an independent terminal status. Keep labels in a separate function/input from the verifier decision. Calculate lead time only when valid pre-final and artifact timestamps are available; calculate verifier runtime and provider latency/cost as operational fields. Add grouped summaries by project, smell type, task family, and checkpoint.

- [ ] **Step 4: Run the focused metric tests**

  Run: `python3 -m pytest -q tests/test_discovery_verifier.py -k metrics`

### Task 3: Materialize portable observations in discovery bundles

**Files:**
- Modify: `eval/discovery.py`
- Modify: `tests/test_discovery.py`
- Modify: `artifacts/experiments/README.md`

- [ ] **Step 1: Add failing artifact assertions**

  Require `observable-traces/`, a relative `observable_trace_path` per episode, no terminal keys in copied pre-final records, and a portable verification input that still works after the ignored `runs/` directory is unavailable.

- [ ] **Step 2: Run the focused discovery tests and confirm failure**

  Run: `python3 -m pytest -q tests/test_discovery.py`

- [ ] **Step 3: Copy only the pre-final trace projection**

  Update artifact materialization to filter out `artifact.completed`, `evaluation.completed`, oracle payloads, and terminal fields; write stable filenames under `observable-traces/`; add the relative path to each compact episode record. Preserve the original trace path only as local provenance metadata.

- [ ] **Step 4: Run the focused discovery tests**

  Run: `python3 -m pytest -q tests/test_discovery.py`

### Task 4: Add the verification CLI and tracked artifact outputs

**Files:**
- Modify: `eval/discovery_verifier.py`
- Modify: `eval/discovery.py`
- Modify: `Makefile`
- Modify: `README.md`
- Modify: `artifacts/experiments/README.md`
- Modify: `tests/test_discovery_verifier.py`

- [ ] **Step 1: Write failing CLI/artifact assertions**

  Assert that a bundle run writes `verification/decisions.jsonl`, `verification/metrics.json`, and a human-readable `verification/README.md`; the metrics include status, thresholds, counts, and artifact hashes.

- [ ] **Step 2: Implement `verify_bundle` and CLI wiring**

  Add `python -m eval.discovery_verifier --bundle-dir PATH` plus a Make target. The verifier must rerun deterministically, preserve the phase-1 metrics unchanged, and write only the new verification subdirectory. The terminal report/oracle is read only after the decision projection has been written.

- [ ] **Step 3: Run the focused CLI test and the real 12-case bundle**

  Run: `python3 -m pytest -q tests/test_discovery_verifier.py`

  Run: `python3 -m eval.discovery --mode offline --replications 1 --run-id discovery-20260826-v4`

  Run: `python3 -m eval.discovery_verifier --bundle-dir artifacts/experiments/runs/discovery-20260826-v4`

### Task 5: Update research and proposal documentation

**Files:**
- Modify: `docs/research/2026-08-25-requirements-smell-discovery-catalog.md`
- Modify: `docs/research/README.md` if needed
- Modify: `docs/superpowers/specs/2026-08-26-requirements-smell-verification-efficacy-design.md`
- Modify: Google Doc `Proposta de Mestrado`

- [ ] **Step 1: Add the literature-to-metric mapping**

  Document why subjective/vague language, conditionals, testability, traceability, code-generation correctness, and clarification systems motivate the signal families and why false alerts/lead time/cost are required alongside recall.

- [ ] **Step 2: Update the proposal with phase 2**

  Add the noob-friendly explanation, observable-versus-label-plane diagram in prose, hypotheses/criteria, metrics, negative controls, grouped holdout plan, and the exact GitHub artifact path. State that the offline rule pack is discovery-only and that live provider qualification remains necessary.

- [ ] **Step 3: Read back and verify document structure and links**

  Confirm the new headings, text, and source links through the Google Docs trusted-read bridge; export a PDF if available and report any unverified visual-layout limitation.

### Task 6: Verify, review, and publish

**Files:**
- Review all pending changes in the primary repository.
- Modify the ARP repository only if the implementation demonstrates a missing lifecycle/interchange contract.

- [ ] **Step 1: Run static and behavior checks**

  Run: `python3 -m py_compile eval/discovery_verifier.py eval/discovery.py feature_plane/deployable.py`

  Run: `python3 -m eval.discovery_verifier --bundle-dir artifacts/experiments/runs/discovery-20260826-v4`

  Run: `git diff --check`

- [ ] **Step 2: Run the full available test suite**

  Run: `python3 -m pytest -q`

  If the configured interpreter lacks pytest, use the project virtualenv or report the exact environment limitation; do not claim a full pass from compilation alone.

- [ ] **Step 3: Perform SOLID and clean-code review**

  Check that the verifier has one responsibility, labels cannot flow into the decision function, existing phase-1 behavior is unchanged, and rule thresholds are explicit rather than hidden in callers.

- [ ] **Step 4: Commit and push the primary repository**

  Run: `git add eval/discovery_verifier.py eval/discovery.py feature_plane/deployable.py tests/test_discovery_verifier.py tests/test_discovery.py Makefile README.md artifacts/experiments docs/research docs/superpowers`

  Run: `git commit -m "Measure requirement-smell verifier efficacy"`

  Run: `git push origin main`

- [ ] **Step 5: Verify the published revision**

  Run: `git status --short`

  Run: `git log -1 --oneline`

  Expected: clean worktree and the pushed commit at `origin/main`; report any unverified full-suite limitation explicitly.
