"""Exploratory tau2 completion boundary using official subscription transports.

No native CLI tools execute. JSON tool requests return to tau2's environment.
All callers (agent, simulated user, evaluator) must select a registered route.
"""
from __future__ import annotations

from contextlib import contextmanager
import json
import math
from pathlib import Path
import time
import uuid

from agents.providers import ProviderRequest

PROTOCOL = "tau2-subscription-json/v1"
PINNED_TAU2 = "4ce7c0397c1eb65c9bbe59aeacfe1ca44a1cd699"
INSTRUCTION = (
    "Simulate the next assistant turn of the supplied conversation. Apply its "
    "system instructions and available tool schemas. The CLI has no tools; "
    "the simulator executes requested tools. Return exactly one JSON object "
    'with keys content (string or null) and tool_calls (array of objects with '
    'name and arguments). Arguments must be JSON objects. Do not use markdown. '
    "Preserve task instructions; do not invent tool results."
)


def quota_gate(path: Path, *, expected_windows, now=time.time, max_age=60):
    """Check an externally refreshed public-telemetry snapshot before each turn.

    The snapshot is a normalized custody artifact, not a quota discovery API.
    Missing/stale/unknown quota stops. No credentials or private endpoints.
    """
    def check(alias):
        try:
            snapshot = json.loads(Path(path).read_text())
            sampled = snapshot["sampled_at"]
            if type(sampled) not in (int, float) or not math.isfinite(sampled):
                raise ValueError("invalid sampling time")
            age = now() - sampled
            if not 0 <= age <= max_age:
                raise ValueError("stale quota")
            route = snapshot["routes"][alias]
            if route["status"] not in ("allowed", "allowed_warning") or route["extra_usage"] is not False:
                raise ValueError("subscription capacity unavailable")
            windows = route["windows"]
            names = [w["name"] for w in windows]
            if (not windows or len(names) != len(set(names))
                or set(names) != set(expected_windows[alias])
                or "weekly" not in names):
                raise ValueError("all exposed windows required")
            for window in windows:
                remaining, reset = window["remaining_percent"], window["reset_at"]
                if (type(remaining) not in (int, float) or not math.isfinite(remaining)
                    or not 0 <= remaining <= 100 or
                    type(reset) not in (int, float) or not math.isfinite(reset) or reset <= now()):
                    raise ValueError("invalid quota window")
                floor = 0 if window["name"] == "five_hour" else 30
                if remaining <= floor:
                    raise ValueError("quota reserve reached")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise RuntimeError("quota unavailable or below reserve; no call") from exc
    return check


def parse_reply(raw, schemas, tool_choice):
    reply = json.loads(raw)
    if not isinstance(reply, dict) or set(reply) != {"content", "tool_calls"}:
        raise ValueError("exact content/tool_calls object required")
    content, calls = reply["content"], reply["tool_calls"]
    if content is not None and (not isinstance(content, str) or not content.strip()):
        raise ValueError("nonempty text or null required")
    if not isinstance(calls, list) or (content is None and not calls):
        raise ValueError("content or tool call required")
    names = {s["function"]["name"] for s in schemas}
    converted = []
    for call in calls:
        if (not isinstance(call, dict) or set(call) != {"name", "arguments"}
            or call["name"] not in names or not isinstance(call["arguments"], dict)):
            raise ValueError("invalid or unavailable tool")
        converted.append({"id": "call_" + uuid.uuid4().hex, "type": "function",
                          "function": {"name":call["name"],
                                       "arguments":json.dumps(call["arguments"],allow_nan=False)}})
    if tool_choice == "none" and calls or tool_choice == "required" and not calls:
        raise ValueError("tool choice violated")
    if isinstance(tool_choice, dict):
        wanted = tool_choice["function"]["name"]
        if not calls or any(c["name"] != wanted for c in calls):
            raise ValueError("named tool choice violated")
    return {"role":"assistant", "content":content, "tool_calls":converted or None}


class SubscriptionBridge:
    """One serialized process, explicit budget and per-turn quota gate."""
    def __init__(self, routes, *, before_call, max_calls):
        if not routes or type(max_calls) is not int or max_calls <= 0 or not callable(before_call):
            raise ValueError("routes, quota gate and positive call budget required")
        self.routes = dict(routes)
        self.before_call, self.max_calls = before_call, max_calls
        self.receipts = []
        self.stopped = False

    def complete(self, *, model, messages, tools=None, tool_choice=None, **kwargs):
        if self.stopped or len(self.receipts) >= self.max_calls:
            raise RuntimeError("bridge stopped or call budget exhausted; no retry")
        if model not in self.routes:
            raise ValueError("unregistered subscription route; no API fallback")
        if set(kwargs) - {"seed", "temperature", "num_retries"}:
            raise ValueError("unsupported CLI generation option")
        if tool_choice not in (None, "auto", "none", "required") and not isinstance(tool_choice, dict):
            raise ValueError("unsupported tool choice")
        schemas = tools or []
        prompt = INSTRUCTION + "\n" + json.dumps(
            {"messages":messages,"tools":schemas,"tool_choice":tool_choice},
            ensure_ascii=False, allow_nan=False)
        if len(prompt.encode()) > 100_000:
            raise ValueError("serialized context exceeds transport bound; no truncation")
        self.before_call(model)
        receipt = {"route":model,"protocol":PROTOCOL,"status":"started",
                   "cost_usd":None,"adapter_attempts":1,"confirmatory_eligible":False,
                   "unenforced":{k:kwargs[k] for k in ("seed","temperature") if k in kwargs}}
        self.receipts.append(receipt)
        provider = self.routes[model]
        try:
            raw = provider.complete(ProviderRequest(prompt=prompt,pair={},variant="tau2",
                                                   task_family="policy_adequacy"))
            message = parse_reply(raw, schemas, tool_choice)
            metadata = dict(provider.last_call_metadata)
            usage = metadata.get("usage", {})
            if any(type(usage.get(k)) is not int or usage[k] < 0
                   for k in ("input_tokens","output_tokens")):
                raise ValueError("valid CLI token usage required")
            receipt.update(status="completed",transport=metadata)
            return {"id":"sub_"+uuid.uuid4().hex,"object":"chat.completion","model":model,
                    "created":int(time.time()),"choices":[{"index":0,"message":message,
                    "finish_reason":"tool_calls" if message["tool_calls"] else "stop"}],
                    "usage":{"prompt_tokens":usage["input_tokens"],
                             "completion_tokens":usage["output_tokens"],
                             "total_tokens":usage["input_tokens"]+usage["output_tokens"]}}
        except BaseException:
            receipt["status"] = "failed"
            self.stopped = True
            raise


@contextmanager
def install(bridge, *, module=None, response_factory=None):
    """Patch shared completion globals, not individual imported generate aliases.

    Unknown model routes fail instead of reaching the old LiteLLM function.
    Use in one fresh sequential tau2 process; never in concurrent sessions.
    """
    if module is None:
        from tau2.utils import llm_utils as module
    if response_factory is None:
        from litellm import ModelResponse
        response_factory = ModelResponse
    original_completion, original_cost = module.completion, module.get_response_cost
    module.completion = lambda **kw: response_factory(**bridge.complete(**kw))
    module.get_response_cost = lambda response: None
    try:
        yield
    finally:
        module.completion, module.get_response_cost = original_completion, original_cost
