"""Instrumented provider runtime that materializes pre-final checkpoints.

The runtime deliberately exposes only bounded summaries.  It never requests
or records hidden reasoning.  T1 and T2 are separate provider responses, T3
is emitted by a deterministic contract-validation tool, and only then is the
terminal artifact requested.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

from .checkpoints import AgentExecution, CheckpointObservation, validate_agent_execution
from .providers import Provider, ProviderRequest


Clock = Callable[[], datetime]


def _now_iso(clock: Clock) -> str:
    value = clock()
    if value.tzinfo is None:
        raise ValueError("runtime clock must return timezone-aware datetimes")
    return value.isoformat()


def _json_object(text: str) -> dict[str, Any]:
    candidate = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", candidate, re.DOTALL)
    if fence:
        candidate = fence.group(1)
    else:
        start, end = candidate.find("{"), candidate.rfind("}")
        if start >= 0 and end > start:
            candidate = candidate[start : end + 1]
    parsed = json.loads(candidate)
    if not isinstance(parsed, dict):
        raise ValueError("provider response must be a JSON object")
    return parsed


def _requirement(pair: Mapping[str, Any], variant: str) -> str:
    key = "clean_requirement" if variant == "clean" else "smelly_requirement"
    value = pair.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"pair is missing {key}")
    return value


def _contract_errors(pair: Mapping[str, Any], task_family: str) -> list[str]:
    contract = pair.get("generation_contract", {})
    task = contract.get(task_family, {}) if isinstance(contract, Mapping) else {}
    keys = task.get("output_keys") if isinstance(task, Mapping) else None
    errors: list[str] = []
    if not isinstance(keys, list) or not keys:
        errors.append("generation contract has no output keys")
    elif any(not isinstance(key, str) or not key.strip() for key in keys):
        errors.append("generation contract contains an invalid output key")
    elif len(set(keys)) != len(keys):
        errors.append("generation contract contains duplicate output keys")
    return errors


class StagedProviderRuntime:
    """A real provider-backed executor for :class:`RuntimeCheckpointAgent`.

    ``runtime_native`` means emitted by this instrumented runtime during the
    same episode, not access to provider chain-of-thought or hidden state.
    """

    def __init__(self, provider: Provider, *, clock: Clock | None = None) -> None:
        self._provider = provider
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def _complete(
        self,
        prompt: str,
        pair: dict[str, Any],
        variant: str,
        task_family: str,
        stage: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        started = _now_iso(self._clock)
        start_perf = time.perf_counter()
        response = self._provider.complete(
            ProviderRequest(prompt=prompt, pair=pair, variant=variant, task_family=task_family)
        )
        latency_ms = (time.perf_counter() - start_perf) * 1000.0
        ended = _now_iso(self._clock)
        return _json_object(response), {
            "stage": stage,
            "started_at": started,
            "ended_at": ended,
            "latency_ms": round(latency_ms, 3),
            "request_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "response_sha256": hashlib.sha256(response.encode("utf-8")).hexdigest(),
        }

    def execute(
        self,
        pair: dict[str, Any],
        variant: str,
        task_family: str,
    ) -> AgentExecution:
        requirement = _requirement(pair, variant)
        base = f"Task family: {task_family}\nRequirement:\n{requirement}\n\n"
        interpretation, t1 = self._complete(
            base
            + "Return JSON with exactly: constraints, quantities, unresolved_references, "
            "assumptions, contradictions. Every value must be a list. This is an observable "
            "task summary; do not reveal hidden reasoning, labels, variants, or an artifact.",
            pair,
            variant,
            task_family,
            "T1",
        )
        plan, t2 = self._complete(
            base
            + "Observable interpretation:\n"
            + json.dumps(interpretation, sort_keys=True)
            + "\nReturn JSON with exactly: validation_checks, planned_tools, coverage_targets. "
            "Every value must be a list. Do not reveal hidden reasoning, labels, variants, "
            "or a terminal artifact.",
            pair,
            variant,
            task_family,
            "T2",
        )

        execution_started = _now_iso(self._clock)
        tool_started = _now_iso(self._clock)
        errors = _contract_errors(pair, task_family)
        tool_ended = _now_iso(self._clock)
        execution = {
            "revisions": 0,
            "validation_attempts": 1,
            "errors": errors,
            "retrieval_events": 0,
        }

        output_keys = pair["generation_contract"][task_family]["output_keys"]
        artifact, final = self._complete(
            base
            + "Observable interpretation:\n"
            + json.dumps(interpretation, sort_keys=True)
            + "\nObservable plan:\n"
            + json.dumps(plan, sort_keys=True)
            + f"\nReturn one JSON object containing exactly these keys: {list(output_keys)}. "
            "Do not include markdown or commentary.",
            pair,
            variant,
            task_family,
            "artifact",
        )
        observations = (
            CheckpointObservation("interpretation.completed", interpretation, t1["started_at"], t1["ended_at"]),
            CheckpointObservation("plan.completed", plan, t2["started_at"], t2["ended_at"]),
            CheckpointObservation("execution.started", {}, execution_started, execution_started),
            CheckpointObservation("tool.completed", execution, tool_started, tool_ended),
        )
        total_latency = sum(float(stage["latency_ms"]) for stage in (t1, t2, final))
        return validate_agent_execution(
            AgentExecution(
                observations,
                artifact,
                {
                    "provider": self._provider.name,
                    "checkpoint_schema": "pre-final/v1",
                    "runtime": "staged-provider/v1",
                    "runtime_semantics": "externally-materialized-bounded-summaries",
                    "latency_ms": round(total_latency, 3),
                    "stages": [t1, t2, final],
                },
            )
        )


__all__ = ["StagedProviderRuntime"]
