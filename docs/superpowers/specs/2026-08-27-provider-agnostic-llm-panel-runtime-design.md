# Provider-agnostic LLM panel runtime

## Decision

The panel protocol identifies independent judges by opaque, configurable slot
IDs. It does not require OpenAI, Anthropic, Kimi, or any other vendor. A
private runtime configuration selects an adapter, endpoint, model, and
environment-variable name for each slot. The default study design remains
three judges with a 2-of-3 consensus rule, but the implementation accepts a
different configured judge set and threshold.

The panel is a triage and robustness instrument, not the ground truth. Its
agreement, disagreement, and human/model comparison metrics are reported
separately as `panel_consensus`; final claims remain based on independent
reference behavior, hidden tests, and blinded human adjudication.

## Boundaries

- `label_plane/llm_panel.py` owns the blinded prompt, annotation contract and
  configurable consensus rule. Historical `kimi/gpt/claude` task files remain
  readable for compatibility.
- `label_plane/panel_runtime.py` owns task routing, adapter calls, retries,
  response normalization, hashes, latency, usage and private JSONL output.
- `scripts/run_llm_panel.py` is the operator entry point. Smoke mode runs ten
  tasks per judge; full mode requires `--full-run --confirm-full-run` and a
  `stage=full_panel` configuration.
- The runtime has three explicit study stages: `prepilot`, `pilot`, and
  `full_panel`. The stage plan distinguishes episodes, candidates, tasks per
  judge, and provider calls; these units must not be conflated.
- `tasks/llm_panel_runtime.example.json` is a secret-free example. Endpoint,
  model, snapshot and key values are read from environment variables.
- Raw tasks, prompts, model responses and keys stay outside the repository.
  Tracked manifests contain only non-secret identities, hashes, counts and
  operational aggregates.
- `max_total_cost_usd` is a fail-closed budget guard. If pricing or usage is
  unavailable, the runner stops before issuing another call.
- Resume is explicit and idempotent. Successful `(item_id, judge_id)` tasks
  are skipped, prior errors may be retried, and the JSONL checkpoint is written
  atomically after each task.
- Full-panel runs validate the expected count per judge and total count before
  the first adapter call. Judges must receive the same item set.

## Adapter contract

The runner depends on a small `PanelAdapter.complete(prompt, judge)` seam. The
repository ships wire adapters for OpenAI-compatible chat-completions and
Anthropic Messages formats, but arbitrary judge IDs can use either adapter.
Adding a provider-specific SDK later requires one new adapter; it does not
change the blinded prompt, response schema, consensus, or experiment metrics.

## Validity guardrails

- Missing credentials or endpoint/model settings fail before a network call.
- Prompt hashes are checked before execution.
- Responses cannot supply their own item, judge or model identity.
- Retryable transport failures are separated from parse/annotation failures.
- The full run is opt-in to control accidental cost.
- Model/provider latency and token usage are measured only when the adapter
  returns them; no cost is inferred without a declared per-judge or fallback
  pricing table.
- `temperature=0` is recorded but is not described as complete determinism for
  reasoning models or provider endpoints.
- An optional private control matrix supports four conditions:
  `clear_clean_control`, `surface_only_control`, `real_defect_control`, and
  `lexically_discreet_defect_control`. The condition is carried as private
  metadata and is never included in the blinded prompt. The matrix contract
  rejects expected/gold labels so it cannot become a panel oracle.

## Execution stages

The study schedule is recorded in `tasks/panel_stage_plan.example.json`:

- `prepilot`: 12 intents × 2 variants × 1 task × 5 repetitions = 120
  episodes. One primary judge is sufficient for this path-validation stage;
  it is not a panel-consensus result.
- `pilot`: approximately 480 episodes with two real model configurations to
  estimate error rate, variance, cost, and annotation quality.
- `full_panel`: up to 240 candidates per judge and 720 tasks for three judge
  slots, only after the gates pass. The third judge is a robustness analysis,
  not a third confirmatory treatment.

The runtime does not manufacture these cases or infer their labels. The
private task file must be prepared from a frozen, project-held-out corpus with
human-reviewed clean/defective pairs and the four control strata. The full
panel configuration therefore sets `require_negative_controls=true` and
fails before network execution when the matrix is incomplete.

## Disagreement analysis

`scripts/merge_llm_panel.py` writes `agreement` metrics alongside the
consensus summary:

- `agreement_rate`: mean per-item majority agreement;
- `model_disagreement`: count, rate, and item IDs for non-unanimous panels;
- `human_model_disagreement`: explicitly `not_available` until a separate
  adjudication file is supplied, then reported against both consensus and each
  judge.
- `--metadata` optionally joins private item IDs to project and intent IDs so
  the same summary can be stratified at family, project, and intent levels
  without placing those fields in the blinded prompt or tracked artifacts.

These are descriptive variables. They do not convert a 2-of-3 vote into a
gold label, and they must be stratified by family, project/intent in the
private analysis layer, and judge/model configuration.

## Acceptance criteria

Given a private blinded task file and a secret-free runtime config, when a
smoke run is invoked, then exactly the configured limit is routed to every
judge, normalized responses and errors are written privately, and a manifest
records hashes and counts without secrets or requirement text.

Given arbitrary judge IDs and a configured consensus threshold, when responses
are merged, then consensus is computed without relying on vendor names.

Given a missing key or malformed endpoint, when execution starts, then it
fails closed before the first network request.

Given a full-panel configuration, when the private task file has an unexpected
per-judge or total count, then execution fails before the first network call.

Given a budgeted run, when measured cost reaches the configured cap, then the
runner checkpoints completed results and stops before the next task.

Given a previously checkpointed run, when it is resumed with the same run ID,
task selection and configuration hash, then successful tasks are not repeated
and an error record is replaced by a later successful response.
