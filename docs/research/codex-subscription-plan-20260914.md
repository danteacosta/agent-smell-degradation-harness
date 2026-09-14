# Local Codex subscription adapter and bounded original experiment

The user requested review/merge, a paired behavioral experiment, and use of
their Codex quota instead of a Platform key. This is a local exploratory path.
It does not reopen quarantined discovery or qualify source-derived oracles.

## Acceptance contract (before implementation)

1. Given saved ChatGPT login, when a completion is requested, use official
   `codex exec` and return only final text plus observed usage/latency. Never
   invoke the Platform API or silently fall back to API-key authentication.
2. Given credentials in the parent environment, send no API-key variables to
   the child; require ChatGPT login. Give each call an empty temporary working
   directory and disable project instructions, tools, MCP/plugins and web.
   Send only the prompt, never the paired alternative, oracle, or pair metadata.
3. Given a failed/incomplete/tool-using run, timeout or missing usage, reject
   the completion. Do not retry an ambiguous call. Do not describe subscription
   consumption as a measured zero-dollar API cost or fabricate model snapshots.
4. Given a bounded original contract, freeze prompts, identical tests, order,
   repetitions and configuration before generation. Preserve all outcomes,
   including null/reverse contrasts and runtime failures. Use the existing
   planned-pair analyzer and real isolated executor, never trusted-fixture
   execution for model output. No source-derived scientific claim.
5. Existing API-backed and confirmatory runners retain their gates. A request
   for an unsupported strict output-token cap is rejected, not ignored.

## Design and verification

`agents/codex_cli.py` implements the existing completion boundary as an Adapter:
CLI subprocess variation stays outside API providers. A narrow separate original
control experiment avoids imposing API cost semantics on subscription quota.
Integration tests use a local fake CLI executable to test auth, prompt isolation,
success, errors, tools, usage and timeout without paid inference. Then one real
smoke and a frozen small run verify availability. No new general framework.

Official sources inspected 2026-09-14:
- https://learn.chatgpt.com/docs/auth (subscription login vs API billing)
- https://learn.chatgpt.com/docs/non-interactive-mode (saved auth, JSONL, ephemeral)
- https://learn.chatgpt.com/docs/config-file/config-reference (forced login, tools)

Local discovery: system `codex` is 0.3.0; the installed plugin appserver binary
is 0.154.0-alpha.6.2 and reports `Logged in using ChatGPT`. Select the executable
explicitly. macOS executor fails its address-space limit; use qualified Linux
execution before collecting behavioral outcomes. Subscription runs are a
different runtime configuration from raw OpenAI API and cannot be pooled as
the same treatment configuration.
