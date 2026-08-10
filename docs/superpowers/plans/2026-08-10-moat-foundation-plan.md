# Moat Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a reproducible, licensed, public replay benchmark and CI/SARIF path that demonstrates constraint-level semantic risk before customer data exists.

**Architecture:** ASD owns the reference replay fixtures, strict pre-final feature extraction, deterministic baseline comparison, and CLI/SARIF adapter. ARP remains the versioned wire contract; RAG consumes the same artifact shape later. Public fixtures are synthetic and explicitly non-confirmatory. The existing `wedge` contract remains backward compatible; the replay CLI is the new strict `approve/warn/block` contract and is documented as the pre-merge path.

**Tech Stack:** Python 3.11+, pytest, stdlib JSON/SHA-256, existing ARP contracts, GitHub Actions, SARIF 2.1.0.

---

### Task 1: Freeze the replay contract with tests

**Files:**
- Create: `replay/__init__.py`
- Create: `replay/schema.py`
- Modify: `pyproject.toml` (include `replay*` package)
- Create: `tests/test_replay_contract.py`

- [ ] **Step 1: Write failing tests** for `constraint-replay/v1`, required fixture fields, deterministic canonical hash, raw-byte SHA-256, exact ARP wire/package versions (`2.0.5`/`2.0.6`), and rejection of terminal/oracle fields.
- [ ] **Step 2: Run** `pytest -q tests/test_replay_contract.py` and verify the new imports/API fail.
- [ ] **Step 3: Implement** a small typed mapping validator and canonical hash helper; require exactly one ordered T1/T2/T3 event with allowlisted `attributes`, and keep expected labels/mutation metadata out of the deployable path.
- [ ] **Step 4: Run** the focused tests and verify they pass.
- [ ] **Step 5: Commit** `test/replay-contract`.

### Task 2: Add public clean/loss replay fixtures

**Files:**
- Create: `replay/fixtures/manifest.json`
- Create: `replay/fixtures/traces/clean.jsonl`
- Create: `replay/fixtures/traces/constraint-loss.jsonl`
- Create: `replay/fixtures/traces/negative-control.jsonl`
- Create: `replay/fixtures/traces/latency-only.jsonl`
- Create: `replay/fixtures/expected.json` (test-only sidecar)
- Create: `tests/test_replay_fixtures.py`

- [ ] **Step 1: Write failing tests** proving all four fixtures validate, contain exactly ordered typed T1/T2/T3 events, and differ only in the declared mutation operator.
- [ ] **Step 2: Run** the focused fixture tests and verify they fail because the files do not exist.
- [ ] **Step 3: Add** clean, controlled constraint-loss, non-relevant-field negative-control, and operational-latency cases with no terminal labels or final artifacts; keep expected decisions only in the sidecar.
- [ ] **Step 4: Run** the focused tests and inspect the fixture hashes.
- [ ] **Step 5: Commit** `feat/replay-fixtures`.

### Task 3: Implement deterministic replay and generic baselines

**Files:**
- Create: `replay/runner.py`
- Create: `tests/test_replay_runner.py`
- Modify: `README.md`

- [ ] **Step 1: Write failing tests** for clean `approve`, exact constraint-loss `block`, valid below-threshold `warn`, stable report hash, required report fields, false-alert rate, output-only/operational baseline fields, and fixture-ID/expected-sidecar independence.
- [ ] **Step 2: Run** `pytest -q tests/test_replay_runner.py` and verify the runner is missing.
- [ ] **Step 3: Implement** replay loading through existing strict deployable extraction/checkpoint validation, fail-closed invalid-contract reports, bounded evidence schema, baseline calculation, stable canonical serialization (excluding paths/timestamps), and explicit `non_confirmatory_demo` status.
- [ ] **Step 4: Run** focused tests twice and assert identical hashes.
- [ ] **Step 5: Document** a ten-minute quickstart and the generic-baseline comparison in the README.
- [ ] **Step 6: Commit** `feat: add reproducible constraint replay benchmark`.

### Task 4: Add SARIF and stable CLI exit codes

**Files:**
- Create: `replay/__main__.py`
- Create: `tests/test_replay_cli.py`
- Modify: `replay/runner.py`

- [ ] **Step 1: Write failing tests** for JSON/SARIF output, exit codes `0/10/20/30`, malformed fixture failure, exact evidence properties, SARIF 2.1.0 rule IDs, and JSON/SARIF decision consistency.
- [ ] **Step 2: Run** the focused CLI tests and verify failure.
- [ ] **Step 3: Implement** `python -m replay --fixture ... --json ... --sarif ...` with deterministic output and machine-readable errors.
- [ ] **Step 4: Run** CLI tests and the two-fixture smoke flow.
- [ ] **Step 5: Commit** `feat: expose replay gate as SARIF CLI`.

### Task 5: Add a no-secret GitHub Action

**Files:**
- Create: `.github/workflows/replay-gate.yml`
- Create: `tests/test_replay_workflow.py`

- [ ] **Step 1: Write failing tests** requiring the workflow to run clean and loss fixtures, upload SARIF with `if: always()`, declare only `security-events: write`, preserve nonzero gate exits, work on fork PRs without secrets, and not reference provider API secrets.
- [ ] **Step 2: Run** the focused workflow test and verify failure.
- [ ] **Step 3: Implement** the workflow using the package's normal Python setup and the replay CLI.
- [ ] **Step 4: Run** workflow static tests and `git diff --check`.
- [ ] **Step 5: Commit** `ci: add no-secret replay gate workflow`.

### Task 6: License and release hygiene across the stack

**Files:**
- Create: `LICENSE` in ASD, RAG, and ARP (Apache-2.0; update ARP's current metadata explicitly)
- Create: `NOTICE` in ASD, RAG, and ARP
- Create: `CONTRIBUTING.md` in ASD, RAG, and ARP
- Create: `SECURITY.md` in ASD, RAG, and ARP
- Modify: each repository README, package metadata, attribution, and release links

- [ ] **Step 1: Write repository acceptance checks** for license/NOTICE presence, explicit license metadata (including the existing ARP MIT-to-Apache release decision), version/install commands, contribution/security links, dependency/fixture attribution, cross-repository links, and replay quickstart.
- [ ] **Step 2: Run** checks before adding metadata to prove the gap.
- [ ] **Step 3: Add** Apache-2.0 text, NOTICE attribution, maintainer guidance, security disclosure route, and consistent release metadata; do not silently change ARP's published license without recording the release decision.
- [ ] **Step 4: Run** all three repository suites, package/install smoke with network only for dependency installation, offline replay smoke with credentials/network disabled, and static documentation checks.
- [ ] **Step 5: Prepare** commits/tags and release notes independently; publish only after explicit user confirmation.

### Task 7: Final verification and artifact handoff

**Files:**
- Modify: `docs/research/2026-08-10-moat-stress-test.md`
- Modify: `docs/research/README.md`

- [ ] **Step 1: Run** ASD, RAG, and ARP suites, replay twice, SARIF validation, offline install smoke, and `git diff --check`.
- [ ] **Step 2: Record** exact commands, hashes, and remaining non-confirmatory limitations.
- [ ] **Step 3: Review** leakage boundaries, SOLID/clean-code, and release metadata.
- [ ] **Step 4: Record** release-ready commits, tags, and exact handoff commands; do not fast-forward or publish without explicit final confirmation.
