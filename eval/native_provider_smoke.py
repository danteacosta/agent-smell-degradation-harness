"""Qualification smoke for real provider-backed, runtime-native episodes.

The smoke is intentionally smaller than the pre-pilot.  It proves that each
configured provider can emit T1, T2, deterministic T3, and a terminal artifact
through the same staged runtime, while exporting only redacted metadata.  A
passing smoke is evidence for the provider gate; it is not thesis evidence and
does not change the launch plan automatically.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from agents.providers import DeepSeekProvider, OpenAIProvider
from agents.runtime import RuntimeCheckpointAgent
from pairs.loader import load_all_pairs
from protocol.context_management import NoCompactionManager

SCHEMA_VERSION = "native-provider-smoke/v1"
PROVIDER_KINDS = {"openai", "deepseek"}
_ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
_SECRET_ENV_NAMES = {"OPENAI_API_KEY", "DEEPSEEK_API_KEY", "AGENT_LIVE_API_KEY"}


class NativeSmokeConfigurationError(ValueError):
    """Raised when a provider smoke configuration is incomplete or unsafe."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _git_revision(repository_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    revision = result.stdout.strip()
    return revision or None


def _env_name(value: Any, field: str) -> str:
    name = str(value or "").strip()
    if not _ENV_NAME.fullmatch(name):
        raise NativeSmokeConfigurationError(
            f"{field} must be an uppercase environment-variable name"
        )
    return name


def _required_env(name: str, environ: Mapping[str, str]) -> str:
    value = str(environ.get(name, ""))
    if not value.strip():
        raise NativeSmokeConfigurationError(
            f"required private environment variable is missing: {name}"
        )
    return value


def _optional_float(
    spec: Mapping[str, Any],
    field: str,
    environ: Mapping[str, str],
) -> float | None:
    env_field = spec.get(field)
    if env_field is None:
        return None
    name = _env_name(env_field, field)
    value = _required_env(name, environ)
    try:
        parsed = float(value)
    except ValueError as error:
        raise NativeSmokeConfigurationError(f"{name} must contain a number") from error
    if parsed < 0:
        raise NativeSmokeConfigurationError(f"{name} must be non-negative")
    return parsed


def load_smoke_config(path: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise NativeSmokeConfigurationError(f"cannot read smoke config: {path}") from error
    if not isinstance(payload, dict):
        raise NativeSmokeConfigurationError("smoke config must be an object")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise NativeSmokeConfigurationError(
            f"smoke config schema_version must be {SCHEMA_VERSION}"
        )
    task_family = str(payload.get("task_family", "test_gen")).strip()
    if not task_family:
        raise NativeSmokeConfigurationError("task_family is required")
    condition = str(payload.get("context_condition", "no_compaction")).strip()
    if condition != "no_compaction":
        raise NativeSmokeConfigurationError(
            "provider qualification smoke must use the primary no_compaction condition"
        )
    providers = payload.get("providers")
    if not isinstance(providers, list) or len(providers) < 2:
        raise NativeSmokeConfigurationError(
            "provider smoke requires at least two configured provider slots"
        )
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(providers):
        if not isinstance(raw, Mapping):
            raise NativeSmokeConfigurationError(f"providers[{index}] must be an object")
        provider_id = str(raw.get("id", "")).strip()
        kind = str(raw.get("kind", "")).strip().lower()
        if not provider_id or provider_id in seen:
            raise NativeSmokeConfigurationError(
                "provider slots require unique, non-empty ids"
            )
        if kind not in PROVIDER_KINDS:
            raise NativeSmokeConfigurationError(
                f"providers[{index}].kind must be one of {sorted(PROVIDER_KINDS)}"
            )
        for forbidden in ("api_key", "secret", "token"):
            if forbidden in raw:
                raise NativeSmokeConfigurationError(
                    f"providers[{index}] cannot contain a credential field"
                )
        normalized_spec = dict(raw)
        normalized_spec["id"] = provider_id
        normalized_spec["kind"] = kind
        for field in ("api_key_env", "model_env", "model_version_env"):
            normalized_spec[field] = _env_name(normalized_spec.get(field), field)
        for field in ("base_url_env", "reasoning_effort_env"):
            if normalized_spec.get(field) is not None:
                normalized_spec[field] = _env_name(normalized_spec[field], field)
        seen.add(provider_id)
        normalized.append(normalized_spec)
    try:
        replications = int(payload.get("replications", 1))
    except (TypeError, ValueError) as error:
        raise NativeSmokeConfigurationError("replications must be an integer") from error
    if replications <= 0 or replications > 5:
        raise NativeSmokeConfigurationError("replications must be between 1 and 5")
    return {
        "schema_version": SCHEMA_VERSION,
        "task_family": task_family,
        "context_condition": condition,
        "replications": replications,
        "providers": normalized,
    }


def _provider_from_spec(
    spec: Mapping[str, Any],
    *,
    environ: Mapping[str, str],
) -> tuple[Any, dict[str, Any]]:
    api_key_env = str(spec["api_key_env"])
    model_env = str(spec["model_env"])
    model_version_env = str(spec["model_version_env"])
    api_key = _required_env(api_key_env, environ)
    model = _required_env(model_env, environ)
    model_version = _required_env(model_version_env, environ)
    base_url = None
    base_url_env = spec.get("base_url_env")
    if base_url_env:
        base_url = _required_env(str(base_url_env), environ)
    reasoning_effort = None
    reasoning_effort_env = spec.get("reasoning_effort_env")
    if reasoning_effort_env:
        reasoning_effort = _required_env(str(reasoning_effort_env), environ)
    kwargs = {
        "api_key": api_key,
        "model": model,
        "base_url": base_url,
        "max_tokens": int(spec.get("max_tokens", 4096)),
        "temperature": float(spec.get("temperature", 0.0)),
        "reasoning_effort": reasoning_effort,
        "input_usd_per_1k": _optional_float(spec, "input_usd_per_1k_env", environ),
        "cached_input_usd_per_1k": _optional_float(
            spec, "cached_input_usd_per_1k_env", environ
        ),
        "output_usd_per_1k": _optional_float(spec, "output_usd_per_1k_env", environ),
    }
    kind = str(spec["kind"])
    provider = (
        OpenAIProvider(**kwargs)
        if kind == "openai"
        else DeepSeekProvider(**kwargs)
    )
    provider_metadata = provider.configuration_metadata()
    public = {
        "id": str(spec["id"]),
        "kind": kind,
        "model": model,
        "model_version": model_version,
        "base_url": provider.base_url,
        "max_tokens": kwargs["max_tokens"],
        "temperature": provider_metadata["temperature"],
        "reasoning_effort": reasoning_effort,
        "api_key_env": api_key_env,
        "model_env": model_env,
        "model_version_env": model_version_env,
        "pricing_envs": {
            field: spec.get(field)
            for field in (
                "input_usd_per_1k_env",
                "cached_input_usd_per_1k_env",
                "output_usd_per_1k_env",
            )
            if spec.get(field)
        },
    }
    return provider, public


def _selected_pairs(
    *,
    intent_ids: Sequence[str] | None,
    limit: int | None,
) -> list[dict[str, Any]]:
    pairs = load_all_pairs()
    by_id = {str(pair["intent_id"]): pair for pair in pairs}
    if intent_ids:
        requested = [str(value).strip() for value in intent_ids if str(value).strip()]
        unknown = sorted(set(requested) - set(by_id))
        if unknown:
            raise NativeSmokeConfigurationError(
                f"unknown intent ids: {unknown}; available ids are {sorted(by_id)}"
            )
        selected = [by_id[value] for value in requested]
    else:
        selected = sorted(pairs, key=lambda pair: str(pair["intent_id"]))
        if limit is not None:
            if limit <= 0:
                raise NativeSmokeConfigurationError("limit must be positive")
            selected = selected[:limit]
    if not selected:
        raise NativeSmokeConfigurationError("smoke requires at least one pair")
    return selected


def _parse_iso(value: Any) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError as error:
        raise ValueError("runtime timestamp is not ISO-8601") from error
    if parsed.tzinfo is None:
        raise ValueError("runtime timestamp must include a timezone")
    return parsed


def summarize_execution(
    execution: Any,
    pair: Mapping[str, Any],
    *,
    task_family: str,
    variant: str,
) -> dict[str, Any]:
    """Check the provider/runtime contract without exporting terminal text."""

    checkpoints = tuple(execution.checkpoints)
    checkpoint_names = [item.checkpoint for item in checkpoints]
    expected_checkpoints = [
        "interpretation.completed",
        "plan.completed",
        "execution.started",
        "tool.completed",
    ]
    if checkpoint_names != expected_checkpoints:
        raise ValueError(f"unexpected checkpoint order: {checkpoint_names}")
    previous_end: datetime | None = None
    for checkpoint in checkpoints:
        started = _parse_iso(checkpoint.started_at)
        ended = _parse_iso(checkpoint.ended_at)
        if ended < started or (previous_end is not None and started < previous_end):
            raise ValueError("checkpoint timestamps are not monotonic")
        previous_end = ended
        if checkpoint.provenance != "runtime_native":
            raise ValueError("checkpoint provenance is not runtime_native")
    provider_meta = execution.provider_meta
    if not isinstance(provider_meta, Mapping):
        raise ValueError("provider metadata must be an object")
    stages = provider_meta.get("stages")
    if not isinstance(stages, list) or [stage.get("stage") for stage in stages] != [
        "T1", "T2", "T3", "artifact"
    ]:
        raise ValueError("native runtime must export T1, T2, T3, and artifact stages")
    final_stage = stages[-1]
    final_started = _parse_iso(final_stage.get("started_at"))
    if previous_end is None or final_started < previous_end:
        raise ValueError("terminal artifact request did not occur after T3")
    context = provider_meta.get("context_management")
    if not isinstance(context, Mapping):
        raise ValueError("context-management summary is missing")
    if (
        context.get("condition") != "no_compaction"
        or int(context.get("compaction_count", -1)) != 0
        or int(context.get("event_count", 0)) != 3
    ):
        raise ValueError("primary no_compaction contract failed")
    interpretation = checkpoints[0].payload
    tool = checkpoints[-1].payload
    if "atomic_obligations" not in interpretation:
        raise ValueError("T1 atomic obligations are missing")
    if "atomic_obligation_observations" not in tool:
        raise ValueError("T3 atomic-obligation observations are missing")
    expected_keys = sorted(
        str(key)
        for key in pair["generation_contract"][task_family]["output_keys"]
    )
    artifact_keys = sorted(str(key) for key in execution.artifact)
    if artifact_keys != expected_keys:
        raise ValueError("terminal artifact keys do not match the generation contract")
    usage = provider_meta.get("usage")
    usage_observed = isinstance(usage, Mapping) and bool(usage)
    return {
        "intent_id": str(pair["intent_id"]),
        "task_family": task_family,
        "variant": variant,
        "checkpoint_count": len(checkpoints),
        "checkpoint_provenance": "runtime_native",
        "timestamps_monotonic": True,
        "artifact_shape_matches_contract": artifact_keys == expected_keys,
        "artifact_field_count": len(artifact_keys),
        "atomic_obligations_present": True,
        "context_condition": context.get("condition"),
        "context_event_count": int(context["event_count"]),
        "compaction_count": int(context["compaction_count"]),
        "latency_ms": round(float(provider_meta.get("latency_ms", 0.0)), 3),
        "usage_observed": usage_observed,
        "usage": dict(sorted(usage.items())) if usage_observed else {},
        "cost_usd": (
            round(float(provider_meta["cost_usd"]), 8)
            if "cost_usd" in provider_meta
            else None
        ),
        "cost_status": str(provider_meta.get("cost_status", "not_configured")),
    }


def _safe_error(error: Exception, secret_values: Sequence[str]) -> str:
    message = str(error).replace("\n", " ").strip()
    for secret in secret_values:
        if secret:
            message = message.replace(secret, "<redacted>")
    return message[:240] or type(error).__name__


def _failed_call_metadata(provider: Any) -> dict[str, Any]:
    """Preserve bounded usage/cost when a provider response fails validation."""

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
        result["cost_status"] = "measured"
    return result


def _sum_usage(rows: Sequence[Mapping[str, Any]]) -> dict[str, int | float]:
    totals: dict[str, int | float] = {}
    for row in rows:
        usage = row.get("usage")
        if not isinstance(usage, Mapping):
            continue
        for key, value in usage.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                totals[str(key)] = totals.get(str(key), 0) + value
    return dict(sorted(totals.items()))


def run_native_provider_smoke(
    config_path: str | Path,
    output_path: str | Path,
    *,
    intent_ids: Sequence[str] | None = None,
    limit: int | None = 1,
    environ: Mapping[str, str] | None = None,
    repository_root: Path | None = None,
) -> dict[str, Any]:
    config = load_smoke_config(config_path)
    env = dict(os.environ if environ is None else environ)
    pairs = _selected_pairs(intent_ids=intent_ids, limit=limit)
    root = repository_root or Path(__file__).resolve().parents[1]
    started_at = datetime.now(UTC).isoformat()
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": f"native-smoke-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
        "started_at": started_at,
        "finished_at": None,
        "status": "fail",
        "qualification_status": "smoke_only",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "source_revision": _git_revision(root),
        "task_family": config["task_family"],
        "context_condition": config["context_condition"],
        "replications": config["replications"],
        "pair_count": len(pairs),
        "pair_ids": [str(pair["intent_id"]) for pair in pairs],
        "pair_hash": _sha256_json(
            [
                {
                    "intent_id": pair["intent_id"],
                    "clean_requirement_sha256": _sha256_text(pair["clean_requirement"]),
                    "smelly_requirement_sha256": _sha256_text(pair["smelly_requirement"]),
                    "output_keys": pair["generation_contract"][config["task_family"]]["output_keys"],
                }
                for pair in pairs
            ]
        ),
        "config_template_sha256": _sha256_json(config),
        "configuration_sha256": None,
        "providers": [],
    }
    failures = 0
    try:
        for spec in config["providers"]:
            public_spec = {
                "id": str(spec["id"]),
                "kind": str(spec["kind"]),
                "status": "fail",
                "episodes": [],
            }
            secret_values: list[str] = []
            provider = None
            for field in ("api_key_env", "model_env", "model_version_env"):
                value = env.get(str(spec[field]))
                if value:
                    secret_values.append(value)
            try:
                provider, resolved_public = _provider_from_spec(spec, environ=env)
                public_spec.update(resolved_public)
                agent = RuntimeCheckpointAgent.from_provider(
                    provider,
                    model=str(resolved_public["model"]),
                    model_version=str(resolved_public["model_version"]),
                    context_manager=NoCompactionManager(),
                )
                for replication in range(config["replications"]):
                    for pair in pairs:
                        for variant in ("clean", "smelly"):
                            try:
                                execution = agent.execute_with_checkpoints(
                                    pair,
                                    variant=variant,
                                    task_family=config["task_family"],
                                )
                                row = summarize_execution(
                                    execution,
                                    pair,
                                    task_family=config["task_family"],
                                    variant=variant,
                                )
                                row["replication"] = replication
                                public_spec["episodes"].append(row)
                            except Exception as error:
                                failures += 1
                                failure = {
                                    "intent_id": str(pair["intent_id"]),
                                    "variant": variant,
                                    "replication": replication,
                                    "status": "fail",
                                    "error": _safe_error(error, secret_values),
                                }
                                failure.update(_failed_call_metadata(provider))
                                public_spec["episodes"].append(failure)
                if not any(
                    row.get("status") == "fail"
                    for row in public_spec["episodes"]
                ):
                    public_spec["status"] = "pass"
                else:
                    failures += 1
            except Exception as error:
                failures += 1
                public_spec["error"] = _safe_error(error, secret_values)
            episodes = [
                row for row in public_spec["episodes"] if row.get("status") != "fail"
            ]
            public_spec["episode_count"] = len(public_spec["episodes"])
            public_spec["successful_episode_count"] = len(episodes)
            all_rows = public_spec["episodes"]
            public_spec["total_latency_ms"] = round(
                sum(float(row.get("latency_ms", 0.0)) for row in all_rows), 3
            )
            public_spec["total_usage"] = _sum_usage(all_rows)
            costs = [row["cost_usd"] for row in all_rows if row.get("cost_usd") is not None]
            public_spec["total_cost_usd"] = round(sum(costs), 8) if costs else None
            public_spec["cost_status"] = (
                "measured"
                if len(costs) == len(all_rows) and all_rows
                else "not_configured"
                if not costs
                else "partial"
            )
            public_spec["status"] = (
                "pass"
                if public_spec.get("status") == "pass" and episodes
                else "fail"
            )
            report["providers"].append(public_spec)
    finally:
        report["finished_at"] = datetime.now(UTC).isoformat()
    report["status"] = "pass" if failures == 0 else "fail"
    report["provider_count"] = len(report["providers"])
    report["budget_ready"] = bool(
        report["providers"]
        and all(item.get("cost_status") == "measured" for item in report["providers"])
    )
    public_configs = [
        {
            key: provider.get(key)
            for key in (
                "id",
                "kind",
                "model",
                "model_version",
                "base_url",
                "max_tokens",
                "temperature",
                "reasoning_effort",
                "pricing_envs",
            )
        }
        for provider in report["providers"]
    ]
    report["configuration_sha256"] = _sha256_json(
        {
            "config_template_sha256": report["config_template_sha256"],
            "resolved_provider_configs": public_configs,
        }
    )
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


__all__ = [
    "NativeSmokeConfigurationError",
    "SCHEMA_VERSION",
    "load_smoke_config",
    "run_native_provider_smoke",
    "summarize_execution",
]
