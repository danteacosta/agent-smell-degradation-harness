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

- [ ] **Step 1: Write failing tests** for `constraint-replay/v1`, required requirement/trace fields, deterministic canonical hash, raw-byte SHA-256, exact ARP wire/package versions (`2.0.5`/`2.0.6`), and rejection of terminal/oracle fields. Freeze exactly one ordered ARP lifecycle event for each rank: T1=`interpretation.completed`, T2=`plan.completed`, T3=`tool.completed`, with every ARP-required envelope field (`experiment_id`, `run_id`, `episode_id`, `replication_id`, timestamps, `content_reference`, `parent_event_id`), shared identity, sequence numbers `1/2/3`, chronological timestamps, T1 `parent_event_id=null`, and T2/T3 parent IDs referencing the preceding event. Events use `schema_version=2.0.5` and `pre-final/v1` checkpoint payload schemas. Typed validation covers trace-byte/hash, checkpoint-order/schema, replay-version, and ARP-compatibility mutations. CLI invalid-contract reports and exit code `30` are covered in Task 4.
- [ ] **Step 2: Run** `pytest -q tests/test_replay_contract.py` and verify the new imports/API fail.
- [ ] **Step 3: Implement** a small typed mapping validator and canonical hash helper; require exactly one ordered T1/T2/T3 event with the frozen ARP names/envelope/fields, reject malformed provider evidence, and keep expected labels/mutation metadata out of the deployable path.
- [ ] **Step 4: Run** the focused tests and verify they pass.
- [ ] **Step 5: Commit** `test/replay-contract`.

### Task 2: Add public clean/loss replay fixtures

**Files:**
- Create: `replay/fixtures/manifest.json`
- Create: `replay/fixtures/traces/clean.jsonl`
- Create: `replay/fixtures/traces/constraint-loss.jsonl`
- Create: `replay/fixtures/traces/negative-control.jsonl`
- Create: `replay/fixtures/traces/latency-only.jsonl`
- Create: `replay/fixtures/traces/constraint-warning.jsonl`
- Create: `replay/fixtures/requirement.json`
- Create: `replay/fixtures/expected.json` (test-only sidecar)
- Create: `tests/test_replay_fixtures.py`

- [ ] **Step 1: Write failing tests** proving all five fixtures validate, contain exactly ordered typed T1/T2/T3 events, and differ only in the declared mutation operator. Pin clean/negative/latency to `approve`, controlled loss to `block`, and weak loss to `warn`. Validate the `expected.json` sidecar schema; runtime sidecar non-loading is covered in Task 3.
- [ ] **Step 2: Run** the focused fixture tests and verify they fail because the files do not exist.
- [ ] **Step 3: Add** clean, controlled constraint-loss, weak-loss, non-relevant-field negative-control, and operational-latency cases with no terminal labels or final artifacts; keep expected decisions only in the sidecar.
- [ ] **Step 4: Run** the focused tests and inspect the fixture hashes.
- [ ] **Step 5: Commit** `feat/replay-fixtures`.

### Task 3: Implement deterministic replay and generic baselines

**Files:**
- Create: `replay/runner.py`
- Create: `tests/test_replay_runner.py`
- Modify: `README.md`

- [ ] **Step 1: Write failing tests** for `--bundle DIR` arbitrary input, clean `approve`, exact constraint-loss `block`, valid below-threshold `warn`, negative-control/latency `approve`, stable report hash, required report fields, and false-alert rate (false alerts / 2 negative cases, expected `0`). Assert evidence `confidence` is in `[0,1]` and `recommended_action` is one of `review|clarify|block`; mutate terminal labels/final artifacts/output-only values and prove deployable decision/features/baselines are unchanged. Retrospective output-only values may change, but remain namespaced and never feed the gate; report hashes exclude non-deployable diagnostics.
- [ ] **Step 2: Run** `pytest -q tests/test_replay_runner.py` and verify the runner is missing.
- [ ] **Step 3: Implement** replay loading through the installed ARP 2.0.6 validator plus existing strict deployable extraction/checkpoint validation, fail-closed invalid-contract reports, bounded evidence schema, namespaced non-deployable baseline calculation, stable canonical serialization (UTF-8 sorted compact JSON, finite number normalization, no trailing newline, excluding only `report_sha256` plus paths/timestamps/environment and non-deployable diagnostics while retaining `trace_sha256`), and explicit `non_confirmatory_demo` status.
- [ ] **Step 4: Run** focused tests twice and assert identical hashes.
- [ ] **Step 5: Document** the exact ten-minute commands `python -m replay --fixture clean --json out/report.json --sarif out/report.sarif` and `python -m replay --bundle path/to/bundle --json out/report.json --sarif out/report.sarif`, expected outputs, generic-baseline comparison, explicit cross-links to ARP/RAG, the differentiation statement, and coexistence with the legacy `wedge` `clarify` command in `docs/thesis-product-boundary.md` or `docs/wedge.md`.
- [ ] **Step 6: Commit** `feat: add reproducible constraint replay benchmark`.

### Task 4: Add SARIF and stable CLI exit codes

**Files:**
- Create: `replay/__main__.py`
- Create: `tests/test_replay_cli.py`
- Modify: `replay/runner.py`

- [ ] **Step 1: Write failing tests** for JSON/SARIF output, `--bundle DIR`, exit codes `0/10/20/30`, malformed fixture failure, exact evidence properties (`constraint`, `checkpoint`, bounded `confidence`, `recommended_action`), and complete SARIF 2.1.0 structure (`version`, `$schema`, `runs`, tool driver/rules/results). Assert stable rule IDs/properties, JSON/SARIF decision consistency, and malformed/extra optional SARIF extensions being filtered without changing the deployable decision.
- [ ] **Step 2: Run** the focused CLI tests and verify failure.
- [ ] **Step 3: Implement** `python -m replay --fixture ...` and `--bundle DIR` with deterministic output and machine-readable errors; filter only untrusted optional SARIF extensions after the decision has been computed. Use stable rule IDs `constraint-preservation` and `constraint-contract` and duplicate every deployable evidence field in SARIF result properties.
- [ ] **Step 4: Run** CLI tests and the five-fixture benchmark smoke flow.
- [ ] **Step 5: Commit** `feat: expose replay gate as SARIF CLI`.

### Task 5: Add a no-secret GitHub Action

**Files:**
- Create: `.github/workflows/replay-gate.yml`
- Create: `tests/test_replay_workflow.py`

- [ ] **Step 1: Write failing tests** requiring the workflow to run clean and loss fixtures, upload SARIF with `if: always()`, declare only `security-events: write`, preserve nonzero gate exits, work on fork PRs without secrets, and not reference provider API secrets.
- [ ] **Step 2: Run** the focused workflow test and verify failure.
- [ ] **Step 3: Implement** the workflow using the package's normal Python setup and the replay CLI; use `if: always()` for SARIF upload, `security-events: write` when available, ordinary JSON/SARIF artifact upload on every run, and no provider secrets so fork PRs have a reviewable fallback.
- [ ] **Step 4: Run** workflow static tests and `git diff --check`.
- [ ] **Step 5: Commit** `ci: add no-secret replay gate workflow`.

### Task 6: License and release hygiene across the stack

**Files:**
- Create: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/moat-foundation/LICENSE`, `NOTICE`, `CONTRIBUTING.md`, `SECURITY.md` (Apache-2.0)
- Create: `/private/tmp/rag-p1.LSOAlz/LICENSE`, `NOTICE`, `CONTRIBUTING.md`, `SECURITY.md` (Apache-2.0)
- Create: `/private/tmp/arp-moat-foundation/LICENSE`, `NOTICE`, `CONTRIBUTING.md`, `SECURITY.md` (MIT, matching immutable v2.0.6 metadata)
- Modify: each repository `README.md`, `pyproject.toml`, `CHANGELOG.md`/release metadata, attribution, and release links

- [ ] **Step 1: Write repository acceptance checks** for license/NOTICE presence, explicit license metadata (Apache harnesses; MIT ARP v2.0.6), version/install commands, contribution/security links, dependency/fixture attribution, cross-repository links, replay quickstart, and consumer pins to ARP 2.0.6.
- [ ] **Step 2: Run** checks before adding metadata to prove the gap.
- [ ] **Step 3: Add** Apache-2.0 text to ASD/RAG, MIT text and matching metadata to ARP, NOTICE attribution, maintainer guidance, security disclosure route, and consistent release links. Do not rewrite or retag immutable ARP v2.0.6; verify both consumers remain pinned to it and do not claim Apache licensing for ARP.
- [ ] **Step 4: Run** all three repository suites, package/install smoke with network only for dependency setup, offline replay smoke with credentials/network disabled, exact elapsed-time check under ten minutes, and static documentation checks.
- [ ] **Step 5: Prepare** commits/tags and release notes independently; publish only after explicit user confirmation.

Implementation uses the active isolated worktrees (`/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/moat-foundation`,
`/private/tmp/rag-p1.LSOAlz`,
and `/private/tmp/arp-moat-foundation`). Canonical `main` paths are read-only
verification/release targets and are not edited during implementation.

### Task 7: Final verification and artifact handoff

**Files:**
- Modify: `docs/research/2026-08-10-moat-stress-test.md`
- Modify: `docs/research/README.md`

- [ ] **Step 1: Run** ASD, RAG, and ARP suites, replay twice, all five fixtures, SARIF validation, offline replay smoke, exact quickstart timing, and `git diff --check`.
- [ ] **Step 2: Record** exact commands, hashes, and remaining non-confirmatory limitations.
- [ ] **Step 3: Review** leakage boundaries, SOLID/clean-code, and release metadata.
- [ ] **Step 4: Verify** read-only that all three canonical refs are `main` and consumer pins resolve to ARP 2.0.6; record release-ready commits, tags, and handoff commands. Do not fast-forward, tag, or publish without explicit final confirmation.
