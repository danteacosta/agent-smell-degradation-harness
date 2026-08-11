# Thesis and Product Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the replay policy executable, connect supported trace exports to a strict ARP replay bundle, validate product utility inputs, improve quickstart reproducibility, and freeze a defensible master's thesis boundary.

**Architecture:** ASD owns the strict replay contract, policy evaluation, adapter-to-bundle builder, and thesis boundary documentation. RAG owns its broader lifecycle product adapter and utility aggregation; it must not import ASD internals. Both consumers exchange only the published ARP contract and keep product diagnostics out of the thesis plane.

**Tech Stack:** Python 3.11+, pytest, JSON/JSONL, ARP wire 2.0.5/package 2.0.6, Make, Markdown.

---

### Task 1: Make the replay policy executable and deterministic

**Files:**
- Modify: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/replay/policy.py`
- Modify: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/replay/runner.py`
- Modify: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/replay/__main__.py`
- Test: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/tests/test_replay_policy.py`
- Test: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/tests/test_replay_cli.py`

- [ ] **Step 1: Write failing policy tests.** Define the exact JSON policy schema, reject unknown keys/rules/duplicates/non-string values, reject bool-as-int/non-finite/missing fact values, prove block precedence over warn, and assert a same-version custom unresolved-reference policy changes the warning fixture to `block` and changes the policy hash while the immutable default remains unchanged.
- [ ] **Step 2: Run focused tests to verify failure.** Run `pytest tests/test_replay_policy.py tests/test_replay_cli.py -q`; expect missing policy loader/injection/hash behavior.
- [ ] **Step 3: Implement the minimal policy model.** Add schema/version validation, normalized tuple conversion, typed rule predicates, policy SHA-256 using canonical JSON without a newline, and a `policy_facts`/`evaluate` API returning decision plus evidence.
- [ ] **Step 4: Inject policy through the runner and CLI.** Add `run_bundle(..., policy=...)`, `--policy PATH`, report `policy_version` and `policy_hash`, and convert malformed policy/facts to the existing invalid-contract exit 30.
- [ ] **Step 5: Prove thesis isolation.** Add a regression test showing policy changes affect only replay reports and do not alter feature manifests, labels, split manifests, or H1/H2 analysis inputs.
- [ ] **Step 6: Run focused tests and commit.** Expect all policy/CLI tests green; commit `feat: make replay policy executable`.

### Task 2: Build strict ARP bundles from vendor-shaped exports

**Files:**
- Modify: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/replay/integrations.py`
- Modify: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/replay/schema.py`
- Modify: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/replay/runner.py`
- Test: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/tests/test_product_moat.py`
- Test: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/tests/test_replay_integrations.py`

- [ ] **Step 1: Write failing builder tests.** Supply complete Phoenix, Langfuse, and Braintrust exports plus explicit requirement and product identity context; assert exactly one T1/T2/T3 event, ARP envelope fields, parent chain, deterministic JSONL bytes, manifest trace hash, replay decision, and `status=non_confirmatory_adapter_demo`.
- [ ] **Step 2: Write fail-closed tests.** Cover partial exports, duplicate checkpoints, missing timestamps/identity/context, missing or tampered parent IDs, non-chronological events, malformed payloads, terminal/mutation keys in unknown spans, top-level metadata, requirement, and manifest, and unknown deployable keys. Assert audit metadata is accepted only in a non-deployable sidecar, normalization can remain diagnostic, and strict building fails.
- [ ] **Step 3: Write provenance non-fabrication tests.** Assert the product builder never invents provider/model/config IDs, source event IDs, request/response hashes, or cutoff timestamps; those fields remain absent or explicitly supplied in a separate thesis provider manifest and the resulting bundle cannot be marked confirmatory.
- [ ] **Step 4: Run focused tests to verify failure.** Run `pytest tests/test_replay_integrations.py tests/test_product_moat.py -q`; expect no builder and current partial normalizer behavior.
- [ ] **Step 5: Implement source normalization without silent leakage.** Scan every raw record before filtering, map source fields to the frozen typed pre-final payload, preserve only non-deployable source metadata, and reject terminal/mutation keys using the same terminal-key policy as `replay.schema`.
- [ ] **Step 6: Implement `build_replay_bundle`.** Require product context, construct ARP 2.0.5 identity/timestamp/parent fields, serialize each event with sorted compact UTF-8 JSON and exactly one final newline, set `_trace_raw` and `manifest.trace_sha256`, mark the bundle `non_confirmatory_adapter_demo`, and never populate thesis provider provenance fields.
- [ ] **Step 7: Tighten deployable allowlists.** Reject unknown deployable manifest/requirement/event keys as well as terminal/mutation keys; isolate audit metadata in a non-deployable sidecar; keep RAG’s broader lifecycle stream separate and do not import RAG code into ASD.
- [ ] **Step 8: Run focused tests and commit.** Expect adapter-to-gate integration and mutation tests green; commit `feat: build strict replay bundles from trace exports`.

### Task 3: Validate utility metrics at the boundary

**Files:**
- Modify: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/replay/utility.py`
- Test: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/tests/test_product_moat.py`
- Modify: `/Users/dantecosta/Projects/rag-reliability-harness/.worktrees/thesis-product-hardening/product/utility.py`
- Test: `/Users/dantecosta/Projects/rag-reliability-harness/.worktrees/thesis-product-hardening/tests/test_product_utility.py`

- [ ] **Step 1: Write failing ASD utility tests.** Reject unknown decisions, non-boolean flags, bool-as-number values, negative/non-finite durations/costs, invalid failure times, and inconsistent failure-time semantics.
- [ ] **Step 2: Write failing RAG utility tests.** Reject malformed observation rows, negative/non-finite costs and latencies, and non-boolean alert/incident fields while preserving the existing valid summary.
- [ ] **Step 3: Run focused tests to verify failure.** Run both repository-specific utility test files and record the current permissive behavior.
- [ ] **Step 4: Implement boundary validation.** Use small public validators/dataclass post-init checks; avoid silently coercing booleans or numeric strings; reject a non-`None` failure time unless the outcome is a true regression with an alerting decision; keep empty-input behavior explicit.
- [ ] **Step 5: Run focused tests and commit each repository.** Commit ASD as `fix: validate replay utility outcomes` and RAG as `fix: validate product utility observations`.

### Task 4: Make quickstarts and Make targets interpreter-stable

**Files:**
- Modify: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/Makefile`
- Modify: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/README.md`
- Modify: `/Users/dantecosta/Projects/rag-reliability-harness/.worktrees/thesis-product-hardening/README.md`
- Test: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/tests/test_quickstart_contract.py`
- Test: `/Users/dantecosta/Projects/rag-reliability-harness/.worktrees/thesis-product-hardening/tests/test_acceptance.py`

- [ ] **Step 1: Write a regression test.** Shadow `PATH` so no global `pytest` is available and run ASD’s `test`, `eval`, `simulate`, and `gate` targets through `PYTHON=.venv/bin/python`; assert the commands use that interpreter. Verify RAG’s existing `PYTHON` wrapper remains stable.
- [ ] **Step 2: Run the test to verify current ASD failure.** Expect bare `pytest`/`python` usage to fail or use the wrong interpreter.
- [ ] **Step 3: Implement explicit interpreter selection.** Add an ASD `PYTHON` variable with `.venv/bin/python` fallback and route all targets through `$(PYTHON) -m ...`; preserve RAG’s existing pattern.
- [ ] **Step 4: Correct offline wording.** State that constraints are the source of truth and offline execution is post-acquisition; do not promise an empty-wheelhouse bootstrap for the direct ARP VCS dependency.
- [ ] **Step 5: Run quickstart tests and commit.** Commit `docs: make quickstarts interpreter-stable`.

### Task 5: Freeze the master's thesis scope and claims

**Files:**
- Create: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/docs/thesis/masters-scope.md`
- Modify: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/docs/thesis-product-boundary.md`
- Modify: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/docs/research/2026-08-10-orientation-review.md`
- Modify: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/README.md`
- Test: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/tests/test_thesis_scope_docs.py`

- [ ] **Step 1: Write documentation acceptance tests.** Assert the scope document names acceptance-criteria/test generation as primary, H1/H2 as planned conditional claims, traceability as external validation, product as demonstrator, the `ΔPR-AUC ≥ 0.05` margin, and the 24-intent/6-project/real-provider/human-label/shadow-pilot/preregistration gates.
- [ ] **Step 2: Run tests to verify the new scope file is absent.** Expect failure.
- [ ] **Step 3: Write the master's scope document.** Explain academic contribution, related-work boundary, practical impact, novelty hypothesis, limitations, expected thesis chapters, and explicit non-claims.
- [ ] **Step 4: Update boundary/orientation docs.** Replace unconditional claim language with conditional language and cross-link the confirmatory data-acquisition gate and non-confirmatory pre-pilot status.
- [ ] **Step 5: Run documentation tests and commit.** Commit `docs: freeze master's thesis scope and claims`.

### Task 6: Cross-repository contract and clean-code review

**Files:**
- Modify only if required by tests: ASD/RAG files above.
- Review: `/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product-hardening/docs/superpowers/specs/2026-08-11-thesis-product-hardening-design.md`
- Review: `/Users/dantecosta/Projects/rag-reliability-harness/.worktrees/thesis-product-hardening/docs/product/README.md`

- [ ] **Step 1: Add cross-repository boundary tests.** Static-scan RAG imports/report payloads for ASD modules and thesis-label keys (`oracle_passed`, `semantic_label`, `variant`, `mutation`); assert product reports remain free of them while shared ARP fields still validate.
- [ ] **Step 2: Run both repositories’ focused suites.** Verify the boundary tests and no thesis labels enter product reports.
- [ ] **Step 3: Perform SOLID/clean-code review.** Check policy ownership, adapter boundary, validation responsibility, naming, and duplicate rule logic; simplify if abstractions are decorative.
- [ ] **Step 4: Run full verification.** ASD: `PYTHON=.venv/bin/python make all` and full pytest; RAG: `make all` with its wrapper; ARP: full pytest. Record elapsed time and exact counts.
- [ ] **Step 5: Run final replay stress mutations.** Re-test policy, trace hash, expected-sidecar independence, terminal-key rejection, SARIF filtering, and adapter-to-bundle decisions.
- [ ] **Step 6: Review diffs and worktree cleanliness.** Confirm no generated artifacts are tracked and all three canonical `main` branches remain untouched.

### Task 7: Handoff and integration decision

- [ ] **Step 1: Summarize remaining external gates.** Explicitly list dataset acquisition, real providers, human annotation, project-cluster uncertainty, customer shadow pilot, and ROI evidence as unresolved external work.
- [ ] **Step 2: Prepare branch commits/PRs.** Keep ASD and RAG commits separate and provide merge order; do not push or merge automatically.
- [ ] **Step 3: Report verification evidence and thesis verdict.** State what is implementation-complete, what is protocol-ready, and what cannot be claimed before external data.
