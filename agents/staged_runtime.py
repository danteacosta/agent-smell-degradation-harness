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

from .checkpoints import (
    AgentExecution,
    CheckpointObservation,
    validate_agent_execution,
    validate_checkpoint_payload,
)
from .providers import Provider, ProviderRequest, provider_visible_pair
from protocol.atomic_obligations import (
    materialize_atomic_obligation_observations,
    summarize_atomic_obligations,
    validate_atomic_obligations,
)
from protocol.conditional_semantics import validate_conditional_semantics
from protocol.context_management import (
    ContextManager,
    NoCompactionManager,
    build_context_event,
    summarize_context_events,
)


Clock = Callable[[], datetime]
StageCompletion = Callable[[ProviderRequest, str, int], str]


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


_STAGE_FIELDS = {
    "interpretation": (
        "constraints",
        "quantities",
        "unresolved_references",
        "assumptions",
        "contradictions",
        "conditional_semantics",
        "atomic_obligations",
    ),
    "plan": ("validation_checks", "planned_tools", "coverage_targets"),
}

# These are the exact prompt templates used by the runtime.  Keeping them as
# named protocol inputs makes the pre-pilot hash the behavior that is sent to
# a provider, rather than a copy of an implementation detail in a report.
GENERATION_PROMPT_TEMPLATES = {
    "T1": (
        "Task family: {task_family}\nRequirement:\n{requirement}\n\n"
        "Return JSON with exactly: constraints, quantities, unresolved_references, "
        "assumptions, contradictions, conditional_semantics, atomic_obligations. "
        "Every top-level value must be a list. "
        "conditional_semantics items must contain antecedent, consequent, necessity_status "
        "(sufficient_only|also_necessary|undetermined), temporal_relation "
        "(during|next_state|eventually|irrelevant|undetermined), and negative_case "
        "({status: specified|not_specified|not_applicable, description: string|null}). "
        "atomic_obligations items must contain only constraint_index (1-based), "
        "atom_type (actor|action|object|condition|threshold|scope|temporal|exception|modality), "
        "and status (present|absent|uncertain); do not include raw obligation text. "
        "Use an empty list when no atomic observation is available. "
        "This is an observable task summary; do not reveal hidden reasoning, labels, "
        "variants, or an artifact."
    ),
    "T2": (
        "Task family: {task_family}\nRequirement:\n{requirement}\n\n"
        "Observable interpretation:\n{interpretation_json}\n"
        "Return JSON with exactly: validation_checks, planned_tools, coverage_targets. "
        "Every value must be a list. Do not reveal hidden reasoning, labels, variants, "
        "or a terminal artifact."
    ),
    "artifact": (
        "Task family: {task_family}\nRequirement:\n{requirement}\n\n"
        "Observable interpretation:\n{interpretation_json}\n"
        "Observable plan:\n{plan_json}\n"
        "Return one minimal JSON object containing exactly these keys: {output_keys}. "
        "Keep every value concise: use at most three short list items and one short sentence "
        "for scalar text. Do not emit explanations, reasoning, test inventories, markdown, "
        "or commentary."
    ),
}

GENERATION_OUTPUT_SCHEMA = {
    "schema_version": "staged-generation/v2",
    "stages": {
        "T1": {
            "type": "object",
            "fields": list(_STAGE_FIELDS["interpretation"]),
            "all_values": "array",
            "conditional_semantics": {
                "fields": [
                    "antecedent",
                    "consequent",
                    "necessity_status",
                    "temporal_relation",
                    "negative_case",
                ]
            },
            "atomic_obligations": {
                "fields": ["constraint_index", "atom_type", "status"]
            },
        },
        "T2": {
            "type": "object",
            "fields": list(_STAGE_FIELDS["plan"]),
            "all_values": "array",
        },
        "artifact": {
            "type": "object",
            "fields": "task_generation_contract.output_keys",
            "exact_fields": True,
        },
    },
}


def _render_generation_prompt(template: str, **values: Any) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{" + key + "}", str(value))
    return rendered


_COVERAGE_STOPWORDS = {
    "a", "an", "and", "as", "at", "be", "by", "for", "from", "in", "is",
    "of", "on", "or", "the", "to", "with",
}


def _stage_lists(
    payload: Mapping[str, Any], stage: str
) -> tuple[dict[str, list[Any]], list[str]]:
    expected = _STAGE_FIELDS[stage]
    errors: list[str] = []
    values: dict[str, list[Any]] = {}
    unexpected = sorted(set(payload) - set(expected))
    if unexpected:
        errors.append(f"{stage} contains unexpected keys: {unexpected}")
    for field in expected:
        value = payload.get(field)
        if not isinstance(value, list):
            errors.append(f"{stage}.{field} must be a list")
            values[field] = []
            continue
        values[field] = value
        if field == "conditional_semantics":
            try:
                values[field] = validate_conditional_semantics(value)
            except ValueError as error:
                errors.append(str(error))
            continue
        if field == "atomic_obligations":
            try:
                values[field] = validate_atomic_obligations(
                    value,
                    values["constraints"],
                )
            except ValueError as error:
                errors.append(str(error))
            continue
        if any(not isinstance(item, str) or not item.strip() for item in value):
            errors.append(f"{stage}.{field} contains a non-text or empty item")
    return values, errors


def _validate_provider_stage(
    payload: Mapping[str, Any],
    stage: str,
) -> dict[str, Any]:
    """Validate a provider response before the runtime requests the artifact."""

    empty_interpretation = {
        "constraints": [],
        "quantities": [],
        "unresolved_references": [],
        "assumptions": [],
        "contradictions": [],
        "conditional_semantics": [],
        "atomic_obligations": [],
    }
    empty_plan = {
        "validation_checks": [],
        "planned_tools": [],
        "coverage_targets": [],
    }
    empty_execution = {
        "revisions": 0,
        "validation_attempts": 0,
        "errors": [],
        "retrieval_events": 0,
        "constraint_lineage": [],
        "context_management": [],
        "atomic_obligation_observations": [],
    }
    sections: dict[str, Mapping[str, Any]] = {
        "interpretation": empty_interpretation,
        "plan": empty_plan,
        "execution": empty_execution,
    }
    sections[stage] = payload
    return validate_checkpoint_payload(
        sections,
        require_conditional_semantics=True,
        require_atomic_obligations=True,
    )[stage]


def _validate_artifact_shape(
    payload: dict[str, Any], output_keys: list[Any]
) -> dict[str, Any]:
    expected = {str(key) for key in output_keys}
    if set(payload) != expected:
        raise ValueError("terminal artifact keys do not match the generation contract")
    return dict(payload)


def _constraint_lineage(
    constraints: list[Any], coverage_evidence: list[Any]
) -> list[dict[str, Any]]:
    """Create opaque, T3-available links from interpreted constraints to checks.

    The trace carries stable IDs and hashes, not hidden reasoning, terminal
    criteria, labels, or oracle outcomes.  T4 may later join its independent
    reference constraints by ID outside the feature plane.
    """

    result: list[dict[str, Any]] = []
    for index, value in enumerate(constraints, start=1):
        text = str(value).strip()
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        matched = [
            hashlib.sha256(str(candidate).strip().encode("utf-8")).hexdigest()[:16]
            for candidate in coverage_evidence
            if _covered(value, [candidate])
        ]
        result.append(
            {
                "constraint_id": f"c{index:03d}-{digest[:12]}",
                "constraint_sha256": digest,
                "planned_check_ids": matched,
                "observation_id": "semantic-plan-contract-validator/v3",
                "status": "covered" if matched else "uncovered",
                "available_at": "T3",
            }
        )
    return result


def _tokens(value: Any) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", str(value).lower())
        if token not in _COVERAGE_STOPWORDS and len(token) > 1
    }


def _covered(item: Any, evidence: list[Any]) -> bool:
    target = _tokens(item)
    if not target:
        return False
    for candidate in evidence:
        observed = _tokens(candidate)
        if target <= observed or len(target & observed) / len(target) >= 0.5:
            return True
    return False



def _bounded_provider_call_metadata(provider: Provider) -> dict[str, Any]:
    """Copy only numeric usage and non-secret response identity metadata."""

    raw = getattr(provider, "last_call_metadata", {})
    if not isinstance(raw, Mapping):
        return {}
    result: dict[str, Any] = {}
    usage = raw.get("usage")
    if isinstance(usage, Mapping):
        bounded_usage = {
            str(key): value
            for key, value in usage.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        }
        if bounded_usage:
            result["usage"] = dict(sorted(bounded_usage.items()))
    cost = raw.get("cost_usd")
    if isinstance(cost, (int, float)) and not isinstance(cost, bool) and cost >= 0:
        result["cost_usd"] = round(float(cost), 8)
    for key in ("response_model", "response_id"):
        value = raw.get(key)
        if value is not None and str(value).strip():
            result[key] = str(value).strip()
    return result


def _sum_provider_usage(stages: list[Mapping[str, Any]]) -> dict[str, int | float]:
    totals: dict[str, int | float] = {}
    for stage in stages:
        usage = stage.get("usage")
        if not isinstance(usage, Mapping):
            continue
        for key, value in usage.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                totals[str(key)] = totals.get(str(key), 0) + value
    return dict(sorted(totals.items()))


def _semantic_plan_diagnostics(
    pair: Mapping[str, Any],
    task_family: str,
    interpretation: Mapping[str, Any],
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    interpreted, interpretation_errors = _stage_lists(interpretation, "interpretation")
    planned, plan_errors = _stage_lists(plan, "plan")
    coverage_evidence = planned["validation_checks"] + planned["coverage_targets"]
    uncovered_constraints = [
        value
        for value in interpreted["constraints"]
        if not _covered(value, coverage_evidence)
    ]
    unresolved = (
        interpreted["unresolved_references"]
        + interpreted["assumptions"]
        + interpreted["contradictions"]
    )
    unacknowledged_uncertainty = [
        value for value in unresolved if not _covered(value, coverage_evidence)
    ]
    lineage = _constraint_lineage(interpreted["constraints"], coverage_evidence)
    atomic_obligation_observations = materialize_atomic_obligation_observations(
        interpreted["constraints"],
        interpreted["atomic_obligations"],
        lineage,
    )
    atomic_obligation_summary = summarize_atomic_obligations(
        atomic_obligation_observations
    )
    errors = _contract_errors(pair, task_family) + interpretation_errors + plan_errors
    if interpreted["constraints"] and not coverage_evidence:
        errors.append("plan has no validation checks or coverage targets")
    if uncovered_constraints:
        errors.append(
            f"plan leaves {len(uncovered_constraints)} interpreted constraints uncovered"
        )
    if unacknowledged_uncertainty:
        errors.append(
            "plan leaves "
            f"{len(unacknowledged_uncertainty)} unresolved references, assumptions, "
            "or contradictions unacknowledged"
        )
    return {
        "validator": "semantic-plan-contract-validator/v3",
        "errors": errors,
        "constraint_count": len(interpreted["constraints"]),
        "quantity_count": len(interpreted["quantities"]),
        "unresolved_reference_count": len(interpreted["unresolved_references"]),
        "assumption_count": len(interpreted["assumptions"]),
        "contradiction_count": len(interpreted["contradictions"]),
        "conditional_clause_count": len(interpreted["conditional_semantics"]),
        "conditional_negative_case_missing_count": sum(
            item["negative_case"]["status"] == "not_specified"
            for item in interpreted["conditional_semantics"]
        ),
        "validation_check_count": len(planned["validation_checks"]),
        "planned_tool_count": len(planned["planned_tools"]),
        "coverage_target_count": len(planned["coverage_targets"]),
        "uncovered_constraint_count": len(uncovered_constraints),
        "unacknowledged_uncertainty_count": len(unacknowledged_uncertainty),
        "constraint_lineage": lineage,
        "atomic_obligation_observations": atomic_obligation_observations,
        "atomic_obligation_summary": atomic_obligation_summary,
    }


class StagedProviderRuntime:
    """A real provider-backed executor for :class:`RuntimeCheckpointAgent`.

    ``runtime_native`` means emitted by this instrumented runtime during the
    same episode, not access to provider chain-of-thought or hidden state.
    """

    def __init__(
        self,
        provider: Provider,
        *,
        clock: Clock | None = None,
        context_manager: ContextManager | None = None,
        stage_completion: StageCompletion | None = None,
        max_stage_attempts: int = 1,
        stage_output_tokens: Mapping[str, int] | None = None,
    ) -> None:
        if (
            type(max_stage_attempts) is not int
            or max_stage_attempts < 1
            or max_stage_attempts > 2
        ):
            raise ValueError("max_stage_attempts must be one or two")
        self._provider = provider
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._context_manager = context_manager or NoCompactionManager()
        self._stage_completion = stage_completion
        self._max_stage_attempts = max_stage_attempts
        stage_limits = dict(stage_output_tokens or {})
        if set(stage_limits) - {"T1", "T2", "artifact"}:
            raise ValueError("stage_output_tokens contains an unknown stage")
        if any(type(value) is not int or value <= 0 for value in stage_limits.values()):
            raise ValueError("stage_output_tokens must contain positive integers")
        self._stage_output_tokens = stage_limits

    def _complete(
        self,
        prompt: str,
        pair: dict[str, Any],
        variant: str,
        task_family: str,
        stage: str,
        *,
        context_index: int,
        response_validator: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        context_started = _now_iso(self._clock)
        transformation = self._context_manager.prepare(prompt, stage=stage)
        context_ended = _now_iso(self._clock)
        context_event = build_context_event(
            transformation,
            event_id=f"context-{context_index:03d}",
            stage=stage,
            checkpoint_id=f"{stage}-context-{context_index:03d}",
            started_at=context_started,
            ended_at=context_ended,
        )
        request = ProviderRequest(
            prompt=transformation.prompt,
            pair=provider_visible_pair(pair, variant=variant, task_family=task_family),
            variant="opaque",
            task_family=task_family,
            max_output_tokens=self._stage_output_tokens.get(stage),
        )
        last_error: Exception | None = None
        for attempt in range(1, self._max_stage_attempts + 1):
            started = _now_iso(self._clock)
            start_perf = time.perf_counter()
            try:
                response = (
                    self._stage_completion(request, stage, attempt)
                    if self._stage_completion is not None
                    else self._provider.complete(request)
                )
                parsed = _json_object(response)
                if response_validator is not None:
                    parsed = response_validator(parsed)
            except Exception as error:
                last_error = error
                if attempt >= self._max_stage_attempts:
                    raise
                continue
            latency_ms = (time.perf_counter() - start_perf) * 1000.0
            ended = _now_iso(self._clock)
            break
        else:
            assert last_error is not None
            raise last_error
        metadata = {
            "stage": stage,
            "attempt": attempt,
            "started_at": started,
            "ended_at": ended,
            "latency_ms": round(latency_ms, 3),
            "request_sha256": hashlib.sha256(
                transformation.prompt.encode("utf-8")
            ).hexdigest(),
            "response_sha256": hashlib.sha256(response.encode("utf-8")).hexdigest(),
            "context_management_event": context_event,
        }
        metadata.update(_bounded_provider_call_metadata(self._provider))
        return parsed, metadata

    def execute(
        self,
        pair: dict[str, Any],
        variant: str,
        task_family: str,
    ) -> AgentExecution:
        context_events: list[dict[str, Any]] = []
        requirement = _requirement(pair, variant)
        interpretation, t1 = self._complete(
            _render_generation_prompt(
                GENERATION_PROMPT_TEMPLATES["T1"],
                task_family=task_family,
                requirement=requirement,
            ),
            pair,
            variant,
            task_family,
            "T1",
            context_index=1,
            response_validator=lambda value: _validate_provider_stage(
                value, "interpretation"
            ),
        )
        context_events.append(t1["context_management_event"])
        interpretation = _validate_provider_stage(interpretation, "interpretation")
        plan, t2 = self._complete(
            _render_generation_prompt(
                GENERATION_PROMPT_TEMPLATES["T2"],
                task_family=task_family,
                requirement=requirement,
                interpretation_json=json.dumps(interpretation, sort_keys=True),
            ),
            pair,
            variant,
            task_family,
            "T2",
            context_index=2,
            response_validator=lambda value: _validate_provider_stage(value, "plan"),
        )
        context_events.append(t2["context_management_event"])
        plan = _validate_provider_stage(plan, "plan")

        execution_started = _now_iso(self._clock)
        tool_started = _now_iso(self._clock)
        diagnostics = _semantic_plan_diagnostics(
            pair, task_family, interpretation, plan
        )
        tool_ended = _now_iso(self._clock)
        execution = {
            "revisions": 0,
            "validation_attempts": 1,
            "errors": diagnostics["errors"],
            "retrieval_events": 0,
            "constraint_lineage": diagnostics["constraint_lineage"],
            "context_management": context_events,
            "atomic_obligation_observations": diagnostics["atomic_obligation_observations"],
        }
        t3_metadata = {key: value for key, value in diagnostics.items() if key not in {"errors", "constraint_lineage"}}

        output_keys = pair["generation_contract"][task_family]["output_keys"]
        artifact, final = self._complete(
            _render_generation_prompt(
                GENERATION_PROMPT_TEMPLATES["artifact"],
                task_family=task_family,
                requirement=requirement,
                interpretation_json=json.dumps(interpretation, sort_keys=True),
                plan_json=json.dumps(plan, sort_keys=True),
                output_keys=list(output_keys),
            ),
            pair,
            variant,
            task_family,
            "artifact",
            context_index=3,
            response_validator=lambda value: _validate_artifact_shape(value, output_keys),
        )
        all_context_events = [*context_events, final["context_management_event"]]
        observations = (
            CheckpointObservation("interpretation.completed", interpretation, t1["started_at"], t1["ended_at"]),
            CheckpointObservation("plan.completed", plan, t2["started_at"], t2["ended_at"]),
            CheckpointObservation("execution.started", {}, execution_started, execution_started),
            CheckpointObservation("tool.completed", execution, tool_started, tool_ended),
        )
        stages = [t1, t2, {"stage": "T3", **t3_metadata}, final]
        provider_stages = [t1, t2, final]
        total_latency = sum(float(stage["latency_ms"]) for stage in provider_stages)
        total_usage = _sum_provider_usage(provider_stages)
        measured_costs = [
            float(stage["cost_usd"])
            for stage in provider_stages
            if isinstance(stage.get("cost_usd"), (int, float))
            and not isinstance(stage.get("cost_usd"), bool)
        ]
        provider_metadata: dict[str, Any] = {
            "provider": self._provider.name,
            "checkpoint_schema": "pre-final/v1",
            "runtime": "staged-provider/v2",
            "runtime_semantics": "externally-materialized-bounded-summaries",
            "latency_ms": round(total_latency, 3),
            "context_management": summarize_context_events(
                all_context_events,
                condition=self._context_manager.condition,
            ),
            "pre_final_context_management": summarize_context_events(
                context_events,
                condition=self._context_manager.condition,
            ),
            "atomic_obligations": diagnostics["atomic_obligation_summary"],
            "stages": stages,
        }
        if total_usage:
            provider_metadata["usage"] = total_usage
        if measured_costs:
            provider_metadata["cost_usd"] = round(sum(measured_costs), 8)
            provider_metadata["cost_reported"] = len(measured_costs) == len(provider_stages)
            provider_metadata["cost_status"] = (
                "measured"
                if len(measured_costs) == len(provider_stages)
                else "partial"
            )
        return validate_agent_execution(
            AgentExecution(
                observations,
                artifact,
                provider_metadata,
            ),
            require_conditional_semantics=True,
            require_constraint_lineage=True,
            require_atomic_obligations=True,
        )


__all__ = [
    "GENERATION_OUTPUT_SCHEMA",
    "GENERATION_PROMPT_TEMPLATES",
    "StageCompletion",
    "StagedProviderRuntime",
]
