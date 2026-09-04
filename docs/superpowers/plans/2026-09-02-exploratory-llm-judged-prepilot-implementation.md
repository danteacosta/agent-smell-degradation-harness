# Exploratory LLM-Judged Pre-Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a bounded, blinded, non-confirmatory pre-pilot that generates the fixed 120-episode matrix with the two qualified providers, cross-judges every generated artifact, and stops safely at a total US$1.00 cap.

**Architecture:** Keep the existing fail-closed `prepilot/v1` readiness evaluator and human annotation contract authoritative. Add a separate exploratory workflow: private corpus freeze and verification, a dedicated acceptance-criteria judge contract, deterministic call-plan/duplicate construction, a single append-only cost ledger, and an operator CLI that reuses the runtime-native generation path while keeping raw evidence private.

**Tech Stack:** Python 3.14, pytest, existing `RuntimeCheckpointAgent`/`StagedProviderRuntime`, existing OpenAI-compatible provider adapters, JSON/JSONL manifests, `Decimal` for money, and connected Google Drive/Docs for redacted documentation updates.

---

## File map and ownership

Create or modify only the following scoped files:

- `eval/corpus_intake.py` — add the explicit validated-candidate → frozen-manifest transition and private-record/hash verification; preserve the existing candidate validator.
- `scripts/freeze_corpus_manifest.py` — secret-free CLI for freezing a validated redacted candidate manifest into the one canonical repository path.
- `tests/test_corpus_freeze.py` — corpus freeze, rights, hash, and raw-text non-disclosure behavior.
- `data/prepilot/corpus-manifest.json` — generated redacted runtime artifact at the sole authoritative path; create/track it only after a real candidate passes the freeze gate, never as a placeholder and never with raw source text.
- `tasks/acceptance_criteria_llm_judge_rubric.json` — frozen exploratory judge labels, fields, bounds, and constraint-assessment statuses.
- `label_plane/exploratory_judge.py` — request/response schema, blinded prompt, strict parser, and two-judge conservative consolidation.
- `tests/test_exploratory_judge_contract.py` — public-boundary tests for blindness, schema, parsing, and disagreement.
- `eval/exploratory_call_plan.py` — 120-episode expansion, provider artifact joins, opaque IDs, and 20% duplicate selection.
- `tests/test_exploratory_call_plan.py` — deterministic count and ID invariants.
- `eval/exploratory_cost.py` — frozen pricing snapshot, `Decimal` reservations, append-only ledger, and budgeted provider wrapper.
- `tests/test_exploratory_cost.py` — worst-case preflight, reservation/finalization, rounding, and stop conditions.
- `eval/provider_runtime_config.py` — shared secret-safe provider construction for smoke and exploratory workflows, if the existing smoke helper cannot be reused without private coupling.
- `eval/native_provider_smoke.py` — use the shared provider construction seam without changing the smoke report contract.
- `agents/providers.py` — add an optional stage marker to the existing provider request without exposing private metadata; preserve backward compatibility for existing adapters/tests.
- `agents/staged_runtime.py` — expose canonical generation prompt/schema templates and a stage-scoped retry seam used by the exploratory runner; preserve the existing one-shot execution behavior for other callers.
- `agents/runtime.py` — pass the stage-retry/call-accounting seam through `RuntimeCheckpointAgent.from_provider` without changing its public execution result.
- `eval/protocol_hashes.py` — canonicalize and hash the actual generation/judge prompts, output/response schemas, rubric, and runtime protocol inputs.
- `scripts/run_native_provider_smoke.py` — accept the same private env-file path for the prerequisite smoke while preserving its redacted report contract.
- `tests/test_provider_runtime_config.py` — provider config identity and secret non-disclosure regression coverage.
- `tasks/exploratory_llm_judged_prepilot.example.json` — secret-free runtime configuration for the two explicit model snapshots, pricing, limits, and key environment names.
- `eval/exploratory_prepilot.py` — orchestration, preflight, native generation, cross-judging, private evidence, redacted report, and explicit state transitions.
- `scripts/run_exploratory_llm_judged_prepilot.py` — CLI with dry-run/preflight and explicit live-run confirmation.
- `tests/test_exploratory_prepilot.py` — orchestration tests using replay providers; no live keys.
- `data/prepilot/launch-plan.candidate.json` — add only the separate exploratory block; leave all official human/confirmatory fields and `status: blocked` unchanged.
- `tests/test_exploratory_launch_plan_isolation.py` — prove exploratory fields cannot affect `evaluate_launch_plan`.
- `docs/research/` — update repository research notes only if implementation creates new evidence conventions; do not put raw corpus or responses here.
- Connected Google Docs — update the three already identified documents with redacted methodology/status and verify revisions after writing.

The existing `label_plane/llm_panel.py` and `tasks/llm_panel_annotation_rubric.json` remain unchanged: they implement the separate natural-language-smell panel and have incompatible `clean/smelly`/`target_family` semantics.

## Task 1: Freeze and verify the private corpus boundary

**Files:**
- Modify: `eval/corpus_intake.py`
- Create: `scripts/freeze_corpus_manifest.py`
- Test: `tests/test_corpus_freeze.py`

- [ ] **Step 1: Write failing tests for the freeze transition.**

Test that a `prepilot-corpus/v4` manifest with `status: validated_candidate`, exactly 12 unique records, at least 6 projects, immutable `source_revision_url` and `source_revision_id` provenance for every record, all required rights and manipulation checks, valid record hashes, `raw_text_exported: false`, an ISO-8601 `frozen_at`, and a non-placeholder `freeze_reviewer_id` becomes a canonical `status: frozen` manifest without raw text.

Also test rejection of fewer than 12 records, fewer than 6 projects, missing external-provider rights, placeholder reviewer/timestamp, tampered record hash, duplicate intent/hash, and any raw text field in the emitted manifest.

Run: `pytest tests/test_corpus_freeze.py -q`
Expected: FAIL because the freeze and verification functions do not exist.

- [ ] **Step 2: Implement the minimal freeze and raw-record verification API.**

Add `freeze_validated_manifest(candidate, *, frozen_at, freeze_reviewer_id)`. It must accept only the output shape produced by `build_redacted_manifest`, set the explicit frozen metadata, preserve only redacted records, and compute a canonical manifest hash without mutating source text.

Add `validate_private_records_against_frozen_manifest(records, frozen_manifest)`. It must revalidate the private records through the existing intake rules, compare source-intent IDs, project IDs, all three source hashes, rights decisions, and record hashes, and return a private normalized join. It must never return raw text in an object intended for a tracked report.

- [ ] **Step 3: Add the secret-free freeze CLI.**

Implement `scripts/freeze_corpus_manifest.py` with `--candidate`, `--frozen-at`, and `--freeze-reviewer-id`. The output is always exactly `repository_root/data/prepilot/corpus-manifest.json`; do not accept an alternate frozen-manifest destination. The candidate may be private or outside the repository, but the output contains only the redacted frozen manifest and prints counts, status, and hash.

- [ ] **Step 4: Run the focused tests.**

Run: `pytest tests/test_corpus_freeze.py -q`
Expected: PASS, including assertions that source text and secrets never appear in output or error messages.

- [ ] **Step 5: Commit the corpus-boundary change.**

If and only if a real candidate passes the gate, include the generated redacted `data/prepilot/corpus-manifest.json`; otherwise leave that path absent and report the blocker.

```bash
git add eval/corpus_intake.py scripts/freeze_corpus_manifest.py tests/test_corpus_freeze.py
# After a real freeze succeeds, also stage the generated redacted manifest:
git add data/prepilot/corpus-manifest.json
git commit -m "Add explicit pre-pilot corpus freeze boundary"
```

## Task 2: Implement the dedicated acceptance-criteria judge contract

**Files:**
- Create: `tasks/acceptance_criteria_llm_judge_rubric.json`
- Create: `label_plane/exploratory_judge.py`
- Test: `tests/test_exploratory_judge_contract.py`

- [ ] **Step 1: Write failing contract tests.**

Cover:

- request exact fields: `schema_version`, `occurrence_id`, `generated_acceptance_criteria`, and `reference_constraints`;
- no `target_family`, variant, provider/model, oracle, detector, checkpoint, T4, source-label, or credential fields in the serialized request;
- response exact fields and types, including finite `confidence` in `[0, 1]`, bounded rationale/evidence strings, exact constraint-ID cardinality, and allowed statuses `covered|omitted|uncertain`;
- rejection of malformed JSON, extra/missing fields, invalid labels, duplicate/missing constraint IDs, non-finite confidence, and overlong fields;
- exact two-judge agreement produces the shared label, while any disagreement produces `uncertain` with no adjudicator field.

Run: `pytest tests/test_exploratory_judge_contract.py -q`
Expected: FAIL because the dedicated contract does not exist.

- [ ] **Step 2: Freeze the rubric JSON.**

Create `acceptance-criteria-llm-judge/v1` with labels `clean`, `minor`, `moderate`, `severe`, `not_visible`; visible inputs; forbidden metadata; maximum lengths; and the severity anchors approved in the design. Keep this separate from the natural-smell panel rubric.

- [ ] **Step 3: Implement the public judge module.**

Add immutable request/response representations, `build_judge_prompt`, `validate_judge_request`, `parse_judge_response`, and `consolidate_two_judges`. The parser must attach no provider identity; the caller adds private identity only after validation. `build_judge_prompt` must explain coverage/operationalization of the supplied reference constraints without naming the hidden defect family.

- [ ] **Step 4: Add the concrete blindness fixture.**

Use an opaque `occurrence_id` and opaque constraint IDs. Add a serialized-payload test that fails on the exact private target-family value `incompleteness_missing_condition` and all forbidden metadata values, while allowing ordinary natural-language words such as “missing” in constraint text.

- [ ] **Step 5: Run the focused tests and commit.**

Run: `pytest tests/test_exploratory_judge_contract.py -q`
Expected: PASS.

```bash
git add tasks/acceptance_criteria_llm_judge_rubric.json label_plane/exploratory_judge.py tests/test_exploratory_judge_contract.py
git commit -m "Add blinded acceptance-criteria LLM judge contract"
```

## Task 3: Build the deterministic episode, artifact, and duplicate plan

**Files:**
- Create: `eval/exploratory_call_plan.py`
- Test: `tests/test_exploratory_call_plan.py`

- [ ] **Step 1: Write failing count and ID tests.**

Given 12 normalized private records and two provider slots, assert:

- 120 base episodes = 12 intents × 2 variants × 5 replications;
- 240 generated artifacts = 120 episodes per provider;
- 240 base judging tasks;
- exactly 48 base tasks selected for duplication using the fixed seed before any judge outcome;
- 288 judging occurrences per judge and 576 logical judging calls;
- 816 logical operations and 1,296 provider API calls because each runtime-native generation episode has T1, T2, and artifact provider calls, while T3 is deterministic;
- every `occurrence_id` is unique, opaque, and not derived from a visible provider/variant/label string;
- original and duplicate occurrences share a private `base_task_id` but have different occurrence IDs.

Run: `pytest tests/test_exploratory_call_plan.py -q`
Expected: FAIL because the call-plan module does not exist.

- [ ] **Step 2: Implement the frozen call-plan data model.**

Generate a fresh 256-bit cryptographic `run_nonce` once per run and keep it only in the private run bundle. For each ID namespace, compute `HMAC-SHA256(run_nonce, length-prefixed canonical fields)` over a canonical ASCII ordinal, truncate to 16 bytes, and encode as lowercase base32 without a semantic prefix. Assign the private base-task ordinal from the sorted private task sequence; derive `base_task_id` from that ordinal, then derive every `occurrence_id` as `HMAC-SHA256(run_nonce, length_prefixed("occurrence", base_task_id, canonical_occurrence_index))` so the approved run-nonce/base-task/index binding is explicit and delimiter-safe. Derive `episode_id` and `artifact_id` the same way from private ordinals. No HMAC input may contain source intent, label, defect family, provider, model, variant, or replication text. Produce all joins as separate private fields. Use the existing seeded sampling semantics (`round(240 * 0.2) == 48`) and freeze the duplicate set before constructing any judge response. Test that regenerating from the same private nonce and plan is stable while changing any visible metadata does not change or reveal an ID.

- [ ] **Step 3: Implement reference-constraint loading.**

Require a private `prepilot-reference-constraints/v1` file with one record per admitted source intent and stable opaque constraint IDs/text. Check exact intent coverage and uniqueness; never derive the reference constraints from T4, oracle fields, or observed outputs.

- [ ] **Step 4: Run tests and commit.**

Run: `pytest tests/test_exploratory_call_plan.py -q`
Expected: PASS.

```bash
git add eval/exploratory_call_plan.py tests/test_exploratory_call_plan.py
git commit -m "Define exploratory pre-pilot call plan and duplicates"
```

## Task 4: Add the single hard-cap cost ledger

**Files:**
- Create: `eval/exploratory_cost.py`
- Test: `tests/test_exploratory_cost.py`

- [ ] **Step 1: Write failing ledger tests.**

Test that the ledger:

- uses `Decimal` micro-US-dollars and rounds every ceiling upward;
- freezes provider/model snapshot, price snapshot date, input/cached-input/output rates, input-token bound, and output-token bound;
- rejects a preflight whose 1,296 provider API calls × 2 attempts exceed US$1.00;
- reports the direct estimate, the retry-inclusive envelope, and the exact 25% contingency/headroom calculation before any provider call;
- appends one reservation before every attempt and one reconciliation after every response;
- retains unused reservation as an explicit released amount but never creates extra calls from it;
- stops before a call that could exceed the remaining cap;
- transitions to `stopped_cost_unverified` on missing usage, missing price, over-bound usage, or ledger mismatch;
- never serializes an API key, prompt, response, or raw requirement.

Run: `pytest tests/test_exploratory_cost.py -q`
Expected: FAIL because the ledger does not exist.

- [ ] **Step 2: Implement pricing and reservation primitives.**

Use the checked-in provider-selection evidence as the price source, but copy exact rates into the private run configuration. Do not perform a live price lookup. Compute ceilings from declared input/output token bounds and frozen prices; use an append-only JSONL ledger with a monotonic sequence and atomic line append. The report must expose `direct_expected_cost_usd`, `retry_inclusive_worst_case_usd`, `contingency_reserve_usd`, `approved_cap_usd`, `unused_headroom_usd`, and `budget_status`. `contingency_reserve_usd` is inside the US$1.00 cap, and a reservation that would exceed the cap maps to `stopped_budget_exhausted` before the provider call.

- [ ] **Step 3: Implement the budgeted provider wrapper.**

Wrap the existing `Provider` protocol. Before delegating, reserve the attempt. After delegating, read only bounded usage/cost metadata, reconcile the reservation, and re-raise the provider error after recording its safe class. Keep provider-specific generation behavior in the existing adapters. The ledger uses integer micro-US-dollars and a hash chain: each canonical event is hashed with the previous event hash, and the current `ledger_head_hash` is written into every atomic checkpoint and the final report.

- [ ] **Step 4: Run tests and commit.**

Run: `pytest tests/test_exploratory_cost.py -q`
Expected: PASS.

```bash
git add eval/exploratory_cost.py tests/test_exploratory_cost.py
git commit -m "Add append-only exploratory cost ledger"
```

## Task 5: Share safe provider construction and freeze the runtime config

**Files:**
- Create: `eval/provider_runtime_config.py`
- Modify: `eval/native_provider_smoke.py`
- Modify: `scripts/run_native_provider_smoke.py`
- Create: `eval/protocol_hashes.py`
- Create: `tests/test_provider_runtime_config.py`
- Create: `tasks/exploratory_llm_judged_prepilot.example.json`

- [ ] **Step 1: Write provider-construction regression tests.**

Test explicit model/version values for `gpt-5.6-luna`/`gpt-5.6-luna` and `deepseek-v4-pro`/`DeepSeek-V4-Pro-0813`, API-key environment names `PANEL_OPENAI_API_KEY` and `PANEL_DEEPSEEK_API_KEY`, price fields, and safe public metadata. Assert that missing keys fail before client construction and secrets never appear in metadata/errors. Add protocol-hash fixtures covering newline normalization, canonical JSON serialization, every prompt/schema/rubric input, and pre-network rejection on any drift. Add provider-specific token-fit fixtures proving each configured prompt and response schema either fits the exact phase bound or blocks preflight.

Run: `pytest tests/test_provider_runtime_config.py -q`
Expected: FAIL until the shared seam exists.

- [ ] **Step 2: Implement the shared config seam.**

Support explicit non-secret model/version/pricing values and environment-resolved key values. If modifying the smoke helper, preserve its current `native-provider-smoke/v1` public report and configuration hashes. Do not copy or rename the user’s secret values; the runtime config points to the existing `PANEL_*` variables.

- [ ] **Step 3: Add the secret-free exploratory example.**

Declare stage `exploratory_llm_judged_pre_pilot`, task family `test_gen`, primary condition `no_compaction`, two provider slots, `max_total_cost_usd: 1.0`, `max_attempts_per_api_call: 2`, duplicate fraction `0.2`, duplicate seed `0`, and this exact initial token-bound table (tokens per API attempt; zero cached-token credit for the reservation): `generation.T1={input:192,output:128}`, `generation.T2={input:192,output:64}`, `generation.artifact={input:192,output:48}`, and `judge={input:128,output:64}`. The implementation must use the same bounds as provider request limits and reject the run if the actual compact prompt/schema cannot fit; it may not silently increase them. Compute each reservation as `ceil(1_000_000 * (input_bound/1000 * input_rate + output_bound/1000 * output_rate))` integer micro-US-dollars, multiply by two attempts, sum all 1,296 planned API calls by provider/phase, and reserve a 25% contingency on the direct estimate inside the same US$1.00 cap; if this exact envelope does not fit, classify preflight as blocked rather than changing the bounds or cap. Keep the exact resulting table and formula in the example config and test fixture so a preflight can prove (or fail closed on) the cap mathematically. Include `pricing_source_ref` and a dated price snapshot, but no key values. Freeze `generation_prompt_template_sha256`, `judge_prompt_template_sha256`, `generation_output_schema_sha256`, `judge_response_schema_sha256`, `rubric_sha256`, `temperature` (explicitly `0.0` or `null` where the provider default is part of the frozen config), `reasoning_effort`, model snapshots, and source revision. Each hash is derived from canonical UTF-8 bytes after newline normalization and JSON serialization with `sort_keys=true`, compact separators, and `ensure_ascii=false`; preflight recomputes every hash from the runtime constants and rejects drift. Per-call prompt hashes are recorded in private evidence and the template hashes are part of the configuration hash.

- [ ] **Step 4: Run tests and commit.**

Run: `pytest tests/test_provider_runtime_config.py -q`
Expected: PASS.

```bash
git add eval/provider_runtime_config.py eval/native_provider_smoke.py scripts/run_native_provider_smoke.py eval/protocol_hashes.py tests/test_provider_runtime_config.py tasks/exploratory_llm_judged_prepilot.example.json
git commit -m "Share secret-safe provider runtime configuration"
```

## Task 6: Implement the exploratory runner and CLI

**Files:**
- Create: `eval/exploratory_prepilot.py`
- Create: `scripts/run_exploratory_llm_judged_prepilot.py`
- Test: `tests/test_exploratory_prepilot.py`
- Modify: `agents/providers.py`
- Modify: `agents/staged_runtime.py`
- Modify: `agents/runtime.py`

- [ ] **Step 1: Write failing orchestration tests with replay providers.**

Cover:

- missing or non-frozen corpus blocks before the first provider call;
- private raw records must hash-match the frozen manifest;
- full preflight reports expected counts and worst-case cost before network activity;
- native generation uses `RuntimeCheckpointAgent` with `NoCompactionManager`, preserving T1/T2/T3/artifact evidence;
- one stage failure after its retry yields `incomplete_generation` and no judging calls;
- all 240 artifacts are required before duplicate selection;
- every artifact is judged by both configured providers through the dedicated request schema;
- exact agreement is `consensus`, disagreement is `uncertain`, and no adjudicator is recorded;
- judge-level malformed/transport errors become item-level `uncertain` after one retry;
- cost-unverified or blindness failures stop subsequent calls;
- raw evidence is outside the repository and the redacted report contains only hashes, counts, usage, latency, cost, safe error classes, and claim boundary;
- atomic checkpoints contain the current state and ledger head, and `--resume-run` rejects mismatched identities, missing/corrupt checkpoints, and terminal budget/cost/protocol states;
- every terminal state is emitted and tested: `completed`, `completed_with_uncertainty`, `incomplete_generation`, `stopped_budget_exhausted`, `stopped_cost_unverified`, and `stopped_protocol_violation`;
- resumability requires matching run/corpus/rubric/config/source/ledger hashes.

Run: `pytest tests/test_exploratory_prepilot.py -q`
Expected: FAIL because the runner does not exist.

- [ ] **Step 2: Implement preflight and private-input normalization.**

Require `--private-corpus` and `--reference-constraints`; resolve the frozen manifest only from the exact canonical path `repository_root/data/prepilot/corpus-manifest.json` and reject any override or substitute. Load private records, verify them against the frozen redacted manifest, require per-record `generation_contract.test_gen.output_keys`, and construct a private normalized pair without exporting source text.

- [ ] **Step 3: Implement the generation phase.**

For each of the two providers, expand the 120 episodes and invoke `RuntimeCheckpointAgent.from_provider` with `NoCompactionManager`, task family `test_gen`, and a budgeted provider. Use the new stage-scoped seam in `agents/staged_runtime.py`: T1, T2, and artifact each get at most one retry of that same stage, including response parsing/contract failure; never retry the whole episode and never reissue a successful stage. Pass a private `(episode_id, stage)` call key to the ledger while keeping it out of provider-visible requests. Track each T1/T2/artifact API attempt in the same ledger; T3 remains deterministic. Abort the run as `incomplete_generation` if any artifact cannot be completed after its single stage retry.

- [ ] **Step 4: Implement the blinded judging phase.**

After all 240 artifacts exist, select the 48 base tasks with the frozen seed, create 288 occurrences per judge, build the strict request, validate it before each call, and route each request to both providers. Save raw prompts/responses only in a private run directory. Attach provider/model identity only to private evidence after response validation.

- [ ] **Step 5: Implement report/state output and the safe CLI.**

Add `--config`, `--env-file`, `--output`, `--private-corpus`, `--reference-constraints`, `--dry-run`, `--resume-run`, and an explicit live-run confirmation flag. Do not expose a frozen-manifest override. The default private run directory is sibling `<output>.run/` outside the repository and contains `run-manifest.json`, `checkpoint.json`, `cost-ledger.jsonl`, and raw evidence; checkpoint writes use temp-file + fsync + atomic rename, while ledger writes are single-writer append-only. Before any call capture `git rev-parse HEAD` as the immutable `source_revision`; include it in the run manifest and hash it into the resume identity. `--resume-run` accepts only that private run directory, validates run/corpus/rubric/config/source/ledger-head hashes before reopening states `generating`, `judging`, or item-error partial, and rejects terminal budget/cost/protocol states or mismatches with a new-run-required error. Recovery is ledger-authoritative: reconcile every `reserved` event that has a matching private response/usage record before checkpoint reconstruction; if a reservation has no unambiguous response, mark the run `stopped_cost_unverified` and never repeat that call; if the ledger is reconciled but the checkpoint lags, replay finalized ledger events idempotently before continuing. A successful stage is never reissued merely because checkpoint commit followed the provider response. Enforce output outside the repository. Load the env file with the existing secret-safe parser; do not print or upload its contents. Return exit 0 for a completed exploratory report, a nonzero code for blocked/partial terminal states, and never alter official readiness automatically.

- [ ] **Step 6: Run focused tests and commit.**

Run: `pytest tests/test_exploratory_prepilot.py -q`
Expected: PASS with replay providers and zero network calls, including all terminal-state and resume-path assertions.

```bash
git add eval/exploratory_prepilot.py scripts/run_exploratory_llm_judged_prepilot.py agents/providers.py agents/staged_runtime.py agents/runtime.py tests/test_exploratory_prepilot.py
git commit -m "Implement exploratory cross-judged pre-pilot runner"
```

## Task 7: Record the exploratory mode without weakening readiness

**Files:**
- Modify: `data/prepilot/launch-plan.candidate.json`
- Create: `tests/test_exploratory_launch_plan_isolation.py`

- [ ] **Step 1: Write the isolation regression test.**

Build a copy of the candidate launch plan with exploratory status changed from `planned` to `completed`, with arbitrary report values and hashes. Assert that `evaluate_launch_plan` returns the same official blockers, `decision: no_go`, `claim_level`, and `confirmatory_authorized` as the unmodified plan.

Run: `pytest tests/test_exploratory_launch_plan_isolation.py -q`
Expected: FAIL until the exploratory block and test exist.

- [ ] **Step 2: Add the separate exploratory block.**

Record the complete `exploratory-llm-judged-prepilot/v1` block: `scope_authorized: true` based on the researcher-reported advisor permission, `claim_level: non_confirmatory_exploratory`, `status: planned`, `corpus_manifest_sha256: null`, `configuration_sha256: null`, `judge_rubric_sha256: null`, `expected_logical_operations: 816`, `expected_provider_api_calls: 1296`, `observed_logical_operations: 0`, `observed_provider_api_calls: 0`, `observed_artifact_count: 0`, `observed_judge_occurrence_count: 0`, `observed_cost_usd: null`, `provider_configurations: [{provider: openai, model: gpt-5.6-luna, model_version: gpt-5.6-luna, role: generator_and_judge, qualification_status: smoke_qualified, qualification_report_reference: null}, {provider: deepseek, model: deepseek-v4-pro, model_version: DeepSeek-V4-Pro-0813, role: generator_and_judge, qualification_status: smoke_qualified, qualification_report_reference: null}]`, `judge_mode: llm_only_exploratory`, `annotation_status: machine_generated`, `adjudication: none_forced`, `human_adjudication_status: not_performed`, `max_total_cost_usd: 1.0`, `disagreement_policy: uncertain_no_forced_adjudication`, `human_annotation_substitute: false`, and `report_reference: null`. The three hash/reference fields may be null only in `planned`; when the block reaches `ready` or any terminal execution state, require exact SHA-256 values and a redacted report reference. Update observed counts/cost and report references only from the private run's reconciled report, never by estimation. Leave official `status: blocked`, `confirmatory_authorized: false`, human annotation count, ethics gate, and all existing `go_no_go` values untouched.

- [ ] **Step 3: Run the isolation test and commit.**

Run: `pytest tests/test_exploratory_launch_plan_isolation.py -q`
Expected: PASS.

```bash
git add data/prepilot/launch-plan.candidate.json tests/test_exploratory_launch_plan_isolation.py
git commit -m "Record exploratory mode without changing readiness"
```

## Task 8: Verify, attempt intake, execute only if admissible, and document evidence

**Files/artifacts:**
- Read/write private corpus candidate and raw records supplied by the researcher; never commit them.
- Private reports under `/private/tmp/` or another explicitly private directory.
- Update the three connected Google Docs with redacted evidence and status.

- [ ] **Step 1: Run the complete offline verification suite.**

Run: `pytest -q`
Expected: all existing tests plus the new tests pass; no secret-bearing fixture is written.

- [ ] **Step 2: Run corpus intake against the available 16 private candidates.**

Use only the private candidate path explicitly supplied by the researcher or already documented in the private operator environment; do not guess, search broadly, copy, or expose the path. Record the exact private path, intake command, timestamp, and source revision only in the private operator log. Run the v3 validator and inspect the redacted output. Require exactly 12 admitted records, at least 6 projects, complete rights/provenance, near-clone screening, manipulation checks, and a frozen manifest before proceeding. If the result remains `0/12`, stop the exploratory run and report the corpus blocker; do not pad with checked-in seeds or paraphrases.

- [ ] **Step 3: Run a no-network exploratory preflight.**

Use the explicit two-provider config and the existing private env file with `PANEL_OPENAI_API_KEY` and `PANEL_DEEPSEEK_API_KEY`. First rerun the existing native-provider smoke through `scripts/run_native_provider_smoke.py` with the same two model/version slots, current source revision, and a private output path; require `status: pass`, both providers qualified, `no_compaction`, runtime-native T1–T3/artifact evidence, usage/cost metadata, and a configuration hash matching the exploratory provider config. If smoke fails or configuration drifts, stop before exploratory calls. Then run the exploratory CLI with `--dry-run`. Verify it reports 240 artifacts, 48 duplicate base tasks, 576 judge calls, 1,296 provider API calls, the frozen hashes, and a worst-case reservation plus 25% contingency below US$1.00 without making a provider request.

- [ ] **Step 4: Update Google Drive before live execution.**

Using the connected Google Drive/Docs workflow, update these exact documents with: advisor authorization reported for this exploratory mode; LLM judges are not human annotators; no forced adjudication; the $1.00 total cap; the still-pending corpus/rights/ethics distinctions; and the fact that official readiness remains `no_go`.

1. `Requirements-smell Discovery Experiments: v8 Natural Screening` — document ID `1CYXDFRotj-01qyTpJrY00LnUE2sb06255l1V6W9e9vs` — owner: research-method status and corpus gate.
2. `Requirements-smell Discovery Experiments: Description, Evidence, Results, and Verifier Evaluation` — document ID `1wSv-khPmRusFKwk4PO02qmbY6eg1MTjJ0QGHTlZuzuI` — owner: evidence interpretation and claim boundary.
3. `Proposta de Mestrado` — document ID `1sio6UiAciypbKGu7mbs8nlQJv2xvc3t888SvaShmB2w` — owner: thesis-method summary and advisor authorization record.

The assistant may write only redacted methodological/status facts. The researcher must supply or confirm any advisor identity, date, ethics determination, or data-rights fact; none may be invented. Re-read each document and verify the new revision/paragraphs.

- [ ] **Step 5: Execute the live run only when preflight passes.**

Run the explicit live confirmation command with the two keys loaded from the existing env file. Stop on any budget, cost-reconciliation, blindness, config-drift, or corpus violation. Do not print raw prompts, responses, keys, or private requirement text.

- [ ] **Step 6: Reconcile the result.**

Verify the private raw bundle, redacted report, call counts, configuration/rubric/corpus hashes, usage and cost reconciliation, duplicate repeatability metrics, agreement/uncertainty counts, and official readiness output. A partial or uncertain run remains exploratory and cannot become `go`.

- [ ] **Step 7: Update the launch plan and Google Drive with actual evidence.**

Write only redacted status, hashes, counts, cost, and report references into the exploratory block and the three named documents. Preserve the official confirmatory fields. Re-read the documents and run the isolation test again.

- [ ] **Step 8: Run the final verification commands.**

Run: `pytest -q`
Expected: full offline suite passes and the official readiness report remains `decision: no_go` unless independently satisfied by the original gates.

## Execution notes

- Use `@superpowers:subagent-driven-development` or `@superpowers:executing-plans` for the task-by-task implementation handoff.
- Use TDD for every new module: failing public-behavior test, minimal implementation, focused pass, then full regression.
- Use the existing provider adapters as the external API boundary. The only justified shared construction seam is the one needed to keep smoke and exploratory provider identity/pricing behavior consistent.
- Treat all private corpus data, env files, prompts, responses, and raw judge evidence as sensitive. Only redacted hashes/counts/statuses may enter Git or Google Drive.
- If the corpus cannot be frozen by tomorrow, the correct deliverable is a tested, preflight-blocked exploratory runner plus the already-passing provider smoke—not a mislabeled partial experiment.
