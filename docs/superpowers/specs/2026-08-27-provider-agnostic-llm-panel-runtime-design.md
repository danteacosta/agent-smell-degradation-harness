# Provider-agnostic LLM panel runtime

## Decision

The panel protocol identifies independent judges by opaque, configurable slot
IDs. It does not require OpenAI, Anthropic, Kimi, or any other vendor. A
private runtime configuration selects an adapter, endpoint, model, and
environment-variable name for each slot. The default study design remains
three judges with a 2-of-3 consensus rule, but the implementation accepts a
different configured judge set and threshold.

## Boundaries

- `label_plane/llm_panel.py` owns the blinded prompt, annotation contract and
  configurable consensus rule. Historical `kimi/gpt/claude` task files remain
  readable for compatibility.
- `label_plane/panel_runtime.py` owns task routing, adapter calls, retries,
  response normalization, hashes, latency, usage and private JSONL output.
- `scripts/run_llm_panel.py` is the operator entry point. Smoke mode runs ten
  tasks per judge; full mode requires `--full-run --confirm-full-run`.
- `tasks/llm_panel_runtime.example.json` is a secret-free example. Endpoint,
  model and key values are read from environment variables.
- Raw tasks, prompts, model responses and keys stay outside the repository.
  Tracked manifests contain only non-secret identities, hashes, counts and
  operational aggregates.

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

## Acceptance criteria

Given a private blinded task file and a secret-free runtime config, when a
smoke run is invoked, then exactly the configured limit is routed to every
judge, normalized responses and errors are written privately, and a manifest
records hashes and counts without secrets or requirement text.

Given arbitrary judge IDs and a configured consensus threshold, when responses
are merged, then consensus is computed without relying on vendor names.

Given a missing key or malformed endpoint, when execution starts, then it
fails closed before the first network request.
