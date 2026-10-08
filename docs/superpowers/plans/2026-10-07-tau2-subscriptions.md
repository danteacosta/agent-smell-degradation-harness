# τ² subscription bridge implementation plan

**Goal:** run the pinned airline text simulator through existing official subscription CLIs, without API fallback or model calls during development.

**Contract:** Given a tau2 message history and tool schemas, when a subscription turn returns a valid JSON response, then tau2 receives native completion content/tool calls, and only tau2 executes tools. Unknown models, malformed JSON, exhausted call budget, stale/missing quota and provider failures stop without retries. Agent, user and evaluator calls use the same fail-closed routing; no hidden API path.

**Architecture:** adapt the pinned llm_utils completion boundary at runtime; preserve upstream files. CLI transports remain isolated text-only. A private quota snapshot is refreshed from public official telemetry externally, checked before every call. An explicit call budget bounds each process. Record unsupported seed/temperature controls and null monetary cost; label protocol exploratory, not native API-equivalent.

**Tradeoffs:** native MCP tool execution would change the agent harness and introduce a second executor. An API proxy would increase exposure and lifecycle complexity. A local completion boundary with serialized tools/history is smaller, but requires its own feasibility check and can affect model behavior.

- [ ] Add failing tests for tool round-trip, invalid output, no API fallback, quota/budget stops, unknown cost and restoration.
- [ ] Implement agents/tau2_subscription.py with strict response conversion and bounded completion routing.
- [ ] Implement an explicit single-task runner; no collection scheduling, retries, auto-review or automatic resumption.
- [ ] Document the wrapper format, public quota snapshot, fixed tau2 commit and scientific limitations in the draft.
- [ ] Run offline tests and static checks, review security, SOLID and clean code. Publish reviewable follow-up against #201; no live probe.

Verification: bundled Python -m pytest tests/test_tau2_subscription.py tests/test_policy_adequacy.py tests/test_codex_cli.py; python -m compileall agents/tau2_subscription.py scripts/tau2_subscription.py.
