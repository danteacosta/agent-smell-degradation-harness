"""Provider-agnostic runtime for blinded requirements-smell panel tasks.

The runner owns orchestration, provenance, retries and private I/O.  Provider
specific behavior is isolated behind small adapters.  The core protocol only
knows a configured judge ID, so changing vendors or using an OpenAI-compatible
endpoint does not change the annotation or consensus contract.

Raw prompts and model responses must stay outside the repository.  Tracked
manifests contain hashes, counts and non-secret configuration identities only.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Protocol
from urllib.parse import urlparse

from label_plane.control_matrix import validate_control_matrix
from label_plane.llm_panel import load_jsonl, validate_panel_annotation

RUNTIME_SCHEMA_VERSION = "requirements-smell-panel-runtime/v1"
RESPONSE_SCHEMA_VERSION = "requirements-smell-panel-response/v1"
_HTTP_ADAPTERS = frozenset({"openai_compatible", "anthropic_messages"})
PANEL_STAGES = ("prepilot", "pilot", "full_panel")
_ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")


class PanelConfigurationError(ValueError):
    """Raised when a private runtime configuration is incomplete or unsafe."""


class PanelAdapterError(RuntimeError):
    """Raised by an adapter, with an explicit retry decision."""

    def __init__(self, message: str, *, retryable: bool = False, status_code: int | None = None) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.status_code = status_code


@dataclass(frozen=True)
class AdapterResponse:
    """Normalized provider response before it becomes an annotation record."""

    text: str
    usage: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class JudgeConfig:
    """A vendor-neutral judge slot from the private panel configuration."""

    judge_id: str
    adapter: str
    model: str | None = None
    model_env: str | None = None
    model_snapshot: str | None = None
    model_snapshot_env: str | None = None
    reasoning_effort: str | None = None
    endpoint: str | None = None
    endpoint_env: str | None = None
    api_key_env: str | None = None
    api_version: str = "2023-06-01"
    max_tokens: int | None = None
    temperature: float | None = None
    timeout_seconds: float | None = None
    max_retries: int | None = None
    input_usd_per_1k: float | None = None
    cached_input_usd_per_1k: float | None = None
    output_usd_per_1k: float | None = None

    def resolve(self, defaults: "PanelRunConfig") -> "ResolvedJudgeConfig":
        model = _resolve_value(self.model, self.model_env, f"model for {self.judge_id}")
        snapshot = _resolve_value(
            self.model_snapshot,
            self.model_snapshot_env,
            f"model snapshot for {self.judge_id}",
        )
        endpoint = _resolve_value(self.endpoint, self.endpoint_env, f"endpoint for {self.judge_id}")
        configuration_errors: list[str] = []
        if not model:
            configuration_errors.append(
                f"missing model for judge {self.judge_id}; set {self.model_env or 'model'}"
            )
        if defaults.stage in {"pilot", "full_panel"} and not snapshot:
            configuration_errors.append(
                f"missing model snapshot for judge {self.judge_id}; set "
                f"{self.model_snapshot_env or 'model_snapshot'}"
            )
        if self.adapter in _HTTP_ADAPTERS:
            if not endpoint:
                configuration_errors.append(
                    f"missing endpoint for judge {self.judge_id}; set {self.endpoint_env or 'endpoint'}"
                )
            else:
                _validate_endpoint(endpoint, self.judge_id)
            if not self.api_key_env or not _ENV_NAME.fullmatch(self.api_key_env):
                configuration_errors.append(
                    f"judge {self.judge_id} requires a valid api_key_env variable name"
                )
                api_key = None
            else:
                api_key = os.environ.get(self.api_key_env)
                if not api_key:
                    configuration_errors.append(
                        f"missing API key environment variable {self.api_key_env} for judge {self.judge_id}"
                    )
        else:
            api_key = None
        if configuration_errors:
            raise PanelConfigurationError("; ".join(configuration_errors))
        return ResolvedJudgeConfig(
            judge_id=self.judge_id,
            adapter=self.adapter,
            model=model,
            model_snapshot=snapshot or str(model),
            model_snapshot_declared=snapshot is not None,
            reasoning_effort=self.reasoning_effort or defaults.reasoning_effort,
            endpoint=endpoint,
            api_key=api_key,
            api_version=self.api_version,
            max_tokens=self.max_tokens if self.max_tokens is not None else defaults.max_tokens,
            temperature=self.temperature if self.temperature is not None else defaults.temperature,
            timeout_seconds=(
                self.timeout_seconds
                if self.timeout_seconds is not None
                else defaults.timeout_seconds
            ),
            max_retries=self.max_retries if self.max_retries is not None else defaults.max_retries,
            input_usd_per_1k=(
                self.input_usd_per_1k
                if self.input_usd_per_1k is not None
                else defaults.input_usd_per_1k
            ),
            cached_input_usd_per_1k=(
                self.cached_input_usd_per_1k
                if self.cached_input_usd_per_1k is not None
                else defaults.cached_input_usd_per_1k
            ),
            output_usd_per_1k=(
                self.output_usd_per_1k
                if self.output_usd_per_1k is not None
                else defaults.output_usd_per_1k
            ),
        )


@dataclass(frozen=True)
class ResolvedJudgeConfig:
    """Resolved runtime settings; the API key is deliberately non-repr-able."""

    judge_id: str
    adapter: str
    model: str
    model_snapshot: str
    endpoint: str | None
    model_snapshot_declared: bool = False
    reasoning_effort: str | None = None
    api_key: str | None = field(default=None, repr=False)
    api_version: str = "2023-06-01"
    max_tokens: int = 512
    temperature: float = 0.0
    timeout_seconds: float = 60.0
    max_retries: int = 2
    input_usd_per_1k: float | None = None
    cached_input_usd_per_1k: float | None = None
    output_usd_per_1k: float | None = None


@dataclass(frozen=True)
class PanelRunConfig:
    """Validated, vendor-neutral configuration for one panel run."""

    judges: tuple[JudgeConfig, ...]
    stage: str = "prepilot"
    expected_tasks_per_judge: int | None = None
    expected_total_tasks: int | None = None
    require_negative_controls: bool = False
    max_total_cost_usd: float | None = None
    consensus_required: int = 2
    timeout_seconds: float = 60.0
    max_retries: int = 2
    retry_backoff_seconds: float = 1.0
    max_tokens: int = 512
    temperature: float = 0.0
    reasoning_effort: str | None = None
    input_usd_per_1k: float | None = None
    cached_input_usd_per_1k: float | None = None
    output_usd_per_1k: float | None = None
    schema_version: str = RUNTIME_SCHEMA_VERSION

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "PanelRunConfig":
        _reject_unknown_keys(
            raw,
            {
                "schema_version",
                "stage",
                "expected_tasks_per_judge",
                "expected_total_tasks",
                "require_negative_controls",
                "max_total_cost_usd",
                "judges",
                "consensus_required",
                "timeout_seconds",
                "max_retries",
                "retry_backoff_seconds",
                "max_tokens",
                "temperature",
                "reasoning_effort",
                "pricing",
            },
            "panel config",
        )
        if raw.get("schema_version") != RUNTIME_SCHEMA_VERSION:
            raise PanelConfigurationError(
                f"schema_version must be {RUNTIME_SCHEMA_VERSION}"
            )
        stage = str(raw.get("stage", "prepilot")).strip()
        if stage not in PANEL_STAGES:
            raise PanelConfigurationError(f"stage must be one of {PANEL_STAGES}")
        raw_judges = raw.get("judges")
        minimum_judges = 1 if stage == "prepilot" else 2
        if not isinstance(raw_judges, list) or len(raw_judges) < minimum_judges:
            raise PanelConfigurationError(
                f"{stage} panel config requires at least {minimum_judges} judge(s)"
            )
        judges: list[JudgeConfig] = []
        for index, value in enumerate(raw_judges):
            if not isinstance(value, Mapping):
                raise PanelConfigurationError(f"judge {index} must be an object")
            _reject_unknown_keys(
                value,
                {
                    "judge_id",
                    "adapter",
                    "model",
                    "model_env",
                    "model_snapshot",
                    "model_snapshot_env",
                    "reasoning_effort",
                    "endpoint",
                    "endpoint_env",
                    "api_key_env",
                    "api_version",
                    "max_tokens",
                    "temperature",
                    "timeout_seconds",
                    "max_retries",
                    "pricing",
                },
                f"judge {index}",
            )
            judge_id = str(value.get("judge_id", "")).strip()
            adapter = str(value.get("adapter", "")).strip()
            if not judge_id or not adapter:
                raise PanelConfigurationError(f"judge {index} requires judge_id and adapter")
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", judge_id):
                raise PanelConfigurationError(f"invalid judge_id: {judge_id}")
            for key in ("api_key_env", "model_env", "model_snapshot_env", "endpoint_env"):
                configured = value.get(key)
                if configured is not None and not _ENV_NAME.fullmatch(str(configured)):
                    raise PanelConfigurationError(f"{key} must be an environment variable name")
            if value.get("model") is not None and value.get("model_env") is not None:
                raise PanelConfigurationError(f"judge {judge_id} cannot set model and model_env together")
            if value.get("model_snapshot") is not None and value.get("model_snapshot_env") is not None:
                raise PanelConfigurationError(
                    f"judge {judge_id} cannot set model_snapshot and model_snapshot_env together"
                )
            if value.get("endpoint") is not None and value.get("endpoint_env") is not None:
                raise PanelConfigurationError(f"judge {judge_id} cannot set endpoint and endpoint_env together")
            judge_pricing = value.get("pricing", {})
            if not isinstance(judge_pricing, Mapping):
                raise PanelConfigurationError(f"{judge_id}.pricing must be an object")
            judges.append(
                JudgeConfig(
                    judge_id=judge_id,
                    adapter=adapter,
                    model=_optional_text(value.get("model")),
                    model_env=_optional_text(value.get("model_env")),
                    model_snapshot=_optional_text(value.get("model_snapshot")),
                    model_snapshot_env=_optional_text(value.get("model_snapshot_env")),
                    reasoning_effort=_optional_text(value.get("reasoning_effort")),
                    endpoint=_optional_text(value.get("endpoint")),
                    endpoint_env=_optional_text(value.get("endpoint_env")),
                    api_key_env=_optional_text(value.get("api_key_env")),
                    api_version=str(value.get("api_version", "2023-06-01")),
                    max_tokens=_optional_positive_int(value.get("max_tokens"), f"{judge_id}.max_tokens"),
                    temperature=_optional_float(value.get("temperature"), f"{judge_id}.temperature"),
                    timeout_seconds=_optional_positive_float(value.get("timeout_seconds"), f"{judge_id}.timeout_seconds"),
                    max_retries=_optional_nonnegative_int(value.get("max_retries"), f"{judge_id}.max_retries"),
                    input_usd_per_1k=_optional_nonnegative_float(
                        judge_pricing.get("input_usd_per_1k"), f"{judge_id}.pricing.input_usd_per_1k"
                    ),
                    cached_input_usd_per_1k=_optional_nonnegative_float(
                        judge_pricing.get("cached_input_usd_per_1k"),
                        f"{judge_id}.pricing.cached_input_usd_per_1k",
                    ),
                    output_usd_per_1k=_optional_nonnegative_float(
                        judge_pricing.get("output_usd_per_1k"), f"{judge_id}.pricing.output_usd_per_1k"
                    ),
                )
            )
        ids = tuple(judge.judge_id for judge in judges)
        if len(set(ids)) != len(ids):
            raise PanelConfigurationError("judge IDs must be unique")
        consensus_required = _positive_int(raw.get("consensus_required", 2), "consensus_required")
        if not 1 <= consensus_required <= len(judges):
            raise PanelConfigurationError("consensus_required must be between 1 and the judge count")
        timeout_seconds = _positive_float(raw.get("timeout_seconds", 60), "timeout_seconds")
        max_retries = _nonnegative_int(raw.get("max_retries", 2), "max_retries")
        retry_backoff_seconds = _nonnegative_float(
            raw.get("retry_backoff_seconds", 1), "retry_backoff_seconds"
        )
        max_tokens = _positive_int(raw.get("max_tokens", 512), "max_tokens")
        temperature = _bounded_float(raw.get("temperature", 0), "temperature", 0, 2)
        reasoning_effort = _optional_text(raw.get("reasoning_effort"))
        pricing = raw.get("pricing", {})
        if not isinstance(pricing, Mapping):
            raise PanelConfigurationError("pricing must be an object")
        input_usd_per_1k = _optional_nonnegative_float(
            pricing.get("input_usd_per_1k"), "pricing.input_usd_per_1k"
        )
        cached_input_usd_per_1k = _optional_nonnegative_float(
            pricing.get("cached_input_usd_per_1k"), "pricing.cached_input_usd_per_1k"
        )
        output_usd_per_1k = _optional_nonnegative_float(
            pricing.get("output_usd_per_1k"), "pricing.output_usd_per_1k"
        )
        expected_tasks_per_judge = _optional_positive_int(
            raw.get("expected_tasks_per_judge"), "expected_tasks_per_judge"
        )
        expected_total_tasks = _optional_positive_int(
            raw.get("expected_total_tasks"), "expected_total_tasks"
        )
        require_negative_controls = raw.get("require_negative_controls", False)
        if not isinstance(require_negative_controls, bool):
            raise PanelConfigurationError("require_negative_controls must be boolean")
        max_total_cost_usd = _optional_nonnegative_float(
            raw.get("max_total_cost_usd"), "max_total_cost_usd"
        )
        if stage == "full_panel" and (
            expected_tasks_per_judge is None or expected_total_tasks is None
        ):
            raise PanelConfigurationError(
                "full_panel requires expected_tasks_per_judge and expected_total_tasks"
            )
        if (
            expected_tasks_per_judge is not None
            and expected_total_tasks is not None
            and expected_total_tasks != expected_tasks_per_judge * len(judges)
        ):
            raise PanelConfigurationError(
                "expected_total_tasks must equal expected_tasks_per_judge times the judge count"
            )
        if stage in {"pilot", "full_panel"}:
            missing_snapshots = [
                judge.judge_id
                for judge in judges
                if judge.model_snapshot is None and judge.model_snapshot_env is None
            ]
            if missing_snapshots:
                raise PanelConfigurationError(
                    "pilot/full_panel requires an explicit model_snapshot for judges: "
                    + ", ".join(missing_snapshots)
                )
        return cls(
            judges=tuple(judges),
            stage=stage,
            expected_tasks_per_judge=expected_tasks_per_judge,
            expected_total_tasks=expected_total_tasks,
            require_negative_controls=require_negative_controls,
            max_total_cost_usd=max_total_cost_usd,
            consensus_required=consensus_required,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            retry_backoff_seconds=retry_backoff_seconds,
            max_tokens=max_tokens,
            temperature=temperature,
            reasoning_effort=reasoning_effort,
            input_usd_per_1k=input_usd_per_1k,
            cached_input_usd_per_1k=cached_input_usd_per_1k,
            output_usd_per_1k=output_usd_per_1k,
        )

    @classmethod
    def from_json(cls, path: str | Path) -> "PanelRunConfig":
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(value, Mapping):
            raise PanelConfigurationError("panel config JSON must contain an object")
        return cls.from_mapping(value)


class PanelAdapter(Protocol):
    """Provider adapter seam used by the runner and test doubles."""

    def complete(self, *, prompt: str, judge: ResolvedJudgeConfig) -> AdapterResponse: ...


class _HttpAdapter:
    def __init__(self, *, opener: Callable[..., Any] | None = None) -> None:
        self._opener = opener or urllib.request.urlopen

    def _post(
        self,
        *,
        judge: ResolvedJudgeConfig,
        headers: Mapping[str, str],
        body: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        if not judge.endpoint or not judge.api_key:
            raise PanelConfigurationError(f"judge {judge.judge_id} is not configured for HTTP execution")
        request = urllib.request.Request(
            judge.endpoint,
            data=_canonical_json(body).encode("utf-8"),
            headers=dict(headers),
            method="POST",
        )
        try:
            with self._opener(request, timeout=judge.timeout_seconds) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            retryable = exc.code in {408, 409, 425, 429, 500, 502, 503, 504}
            raise PanelAdapterError(
                f"HTTP request failed with status {exc.code}",
                retryable=retryable,
                status_code=exc.code,
            ) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise PanelAdapterError("network request failed", retryable=True) from exc
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PanelAdapterError("provider returned invalid JSON", retryable=False) from exc
        if not isinstance(value, Mapping):
            raise PanelAdapterError("provider returned a non-object JSON payload", retryable=False)
        return value


class OpenAICompatibleAdapter(_HttpAdapter):
    """Adapter for chat-completions-compatible endpoints."""

    name = "openai_compatible"

    def complete(self, *, prompt: str, judge: ResolvedJudgeConfig) -> AdapterResponse:
        body: dict[str, Any] = {
            "model": judge.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if judge.reasoning_effort:
            body["reasoning_effort"] = judge.reasoning_effort
            body["max_completion_tokens"] = judge.max_tokens
        else:
            body["temperature"] = judge.temperature
            body["max_tokens"] = judge.max_tokens
        payload = self._post(
            judge=judge,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {judge.api_key}",
            },
            body=body,
        )
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], Mapping):
            raise PanelAdapterError("chat-completions response has no choices", retryable=False)
        message = choices[0].get("message")
        if not isinstance(message, Mapping):
            raise PanelAdapterError("chat-completions response has no message", retryable=False)
        text = _content_to_text(message.get("content"))
        if not text:
            raise PanelAdapterError("chat-completions response has no text content", retryable=False)
        usage = payload.get("usage")
        return AdapterResponse(text=text, usage=dict(usage) if isinstance(usage, Mapping) else {})


class AnthropicMessagesAdapter(_HttpAdapter):
    """Adapter for the Anthropic Messages wire format."""

    name = "anthropic_messages"

    def complete(self, *, prompt: str, judge: ResolvedJudgeConfig) -> AdapterResponse:
        payload = self._post(
            judge=judge,
            headers={
                "Content-Type": "application/json",
                "x-api-key": str(judge.api_key),
                "anthropic-version": judge.api_version,
            },
            body={
                "model": judge.model,
                "max_tokens": judge.max_tokens,
                "temperature": judge.temperature,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        text = _content_to_text(payload.get("content"))
        if not text:
            raise PanelAdapterError("messages response has no text content", retryable=False)
        usage = payload.get("usage")
        return AdapterResponse(text=text, usage=dict(usage) if isinstance(usage, Mapping) else {})


def _default_adapters() -> dict[str, PanelAdapter]:
    return {
        "openai_compatible": OpenAICompatibleAdapter(),
        "anthropic_messages": AnthropicMessagesAdapter(),
    }


class PanelRunner:
    """Execute private blinded tasks and emit normalized response evidence."""

    def __init__(
        self,
        config: PanelRunConfig,
        *,
        adapters: Mapping[str, PanelAdapter] | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config
        self.adapters = _default_adapters()
        if adapters:
            self.adapters.update(adapters)
        self._sleeper = sleeper

    def run(
        self,
        tasks: Iterable[Mapping[str, Any]],
        *,
        run_id: str,
        responses_path: str | Path,
        errors_path: str | Path,
        manifest_path: str | Path,
        limit_per_judge: int | None = None,
        resume: bool = False,
    ) -> dict[str, Any]:
        if not run_id.strip():
            raise PanelConfigurationError("run_id must be non-empty")
        if limit_per_judge is not None and limit_per_judge <= 0:
            raise PanelConfigurationError("limit_per_judge must be positive")
        task_rows = [dict(task) for task in tasks]
        selected = self._select_tasks(task_rows, limit_per_judge=limit_per_judge)
        resolved, configuration_errors = self._resolve_judges()
        if configuration_errors:
            details = "; ".join(configuration_errors)
            raise PanelConfigurationError(f"panel configuration incomplete: {details}")
        responses_path = Path(responses_path)
        errors_path = Path(errors_path)
        manifest_path = Path(manifest_path)
        responses = _load_existing_rows(
            responses_path,
            run_id=run_id,
            resume=resume,
            kind="responses",
        )
        errors = _load_existing_rows(
            errors_path,
            run_id=run_id,
            resume=resume,
            kind="errors",
        )
        self._validate_existing_records(selected, responses, errors)
        previous_manifest = _load_existing_manifest(manifest_path, run_id=run_id, resume=resume)
        if previous_manifest and previous_manifest.get("config_sha256") != self._configuration_sha256(resolved):
            raise PanelConfigurationError("resume configuration does not match the existing run")
        self._validate_budget_configuration(resolved, responses)
        started = _parse_timestamp(previous_manifest.get("started_at")) if previous_manifest else None
        started = started or datetime.now(timezone.utc)
        started_perf = time.perf_counter()
        responses_by_key = {
            _record_key(row): row for row in responses
        }
        errors_by_key = {
            _record_key(row): row for row in errors
        }
        budget_status = "not_configured"
        stop_reason: str | None = None
        if self.config.max_total_cost_usd is not None:
            current_cost = _known_cost_total(responses_by_key.values())
            if current_cost >= self.config.max_total_cost_usd:
                budget_status = "exhausted"
                stop_reason = "cost_budget"
        for task in selected:
            key = (str(task["item_id"]), str(task["provider_id"]))
            if key in responses_by_key:
                continue
            if stop_reason is not None:
                break
            judge = resolved[str(task["provider_id"])]
            adapter = self.adapters.get(judge.adapter)
            if adapter is None:
                raise PanelConfigurationError(
                    f"no adapter registered for {judge.adapter}; add an adapter without changing the panel protocol"
                )
            record, error = self._execute_task(task, judge, adapter, run_id=run_id)
            if record is not None:
                responses_by_key[key] = record
                errors_by_key.pop(key, None)
            if error is not None:
                errors_by_key[key] = error
            responses = _sorted_records(responses_by_key.values())
            errors = _sorted_records(errors_by_key.values())
            _atomic_write_jsonl(responses_path, responses)
            _atomic_write_jsonl(errors_path, errors)
            if self.config.max_total_cost_usd is not None:
                if (record is not None and record.get("cost_usd") is None) or (
                    error is not None and error.get("cost_usd") is None
                ) or (record is not None and int(record.get("attempts", 1)) > 1):
                    budget_status = "unmeasurable"
                    stop_reason = "unmeasurable_cost"
                else:
                    current_cost = _known_cost_total(responses)
                    budget_status = "measured"
                    if current_cost >= self.config.max_total_cost_usd:
                        budget_status = "exhausted"
                        stop_reason = "cost_budget"
        responses = _sorted_records(responses_by_key.values())
        errors = _sorted_records(errors_by_key.values())
        _atomic_write_jsonl(responses_path, responses)
        _atomic_write_jsonl(errors_path, errors)
        finished = datetime.now(timezone.utc)
        wall_ms = (time.perf_counter() - started_perf) * 1000.0
        status = (
            "stopped_cost_budget"
            if stop_reason == "cost_budget"
            else "stopped_unmeasurable_cost"
            if stop_reason == "unmeasurable_cost"
            else "completed_with_smoke_limit"
            if limit_per_judge is not None
            else "completed"
        )
        manifest = self._build_manifest(
            run_id=run_id,
            all_tasks=task_rows,
            selected_tasks=selected,
            responses=responses,
            errors=errors,
            resolved=resolved,
            started=started,
            finished=finished,
            wall_ms=wall_ms,
            responses_path=responses_path,
            errors_path=errors_path,
            status=status,
            resumed=resume,
            stop_reason=stop_reason,
            budget_status=budget_status,
        )
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(_canonical_json(manifest) + "\n", encoding="utf-8")
        return manifest

    def _select_tasks(
        self,
        tasks: list[dict[str, Any]],
        *,
        limit_per_judge: int | None,
    ) -> list[dict[str, Any]]:
        configured = {judge.judge_id for judge in self.config.judges}
        grouped: dict[str, list[dict[str, Any]]] = {judge_id: [] for judge_id in configured}
        seen: set[tuple[str, str]] = set()
        for task in tasks:
            judge_id = str(task.get("provider_id", "")).strip()
            item_id = str(task.get("item_id", "")).strip()
            prompt = str(task.get("prompt", ""))
            if judge_id not in configured:
                raise PanelConfigurationError(f"task uses unconfigured judge {judge_id}")
            if not item_id or not prompt:
                raise PanelConfigurationError("each panel task requires item_id and prompt")
            prompt_hash = sha256(prompt.encode("utf-8")).hexdigest()
            if str(task.get("prompt_sha256", "")) != prompt_hash:
                raise PanelConfigurationError(f"prompt hash mismatch for task {item_id}/{judge_id}")
            key = (item_id, judge_id)
            if key in seen:
                raise PanelConfigurationError(f"duplicate panel task for {item_id}/{judge_id}")
            seen.add(key)
            grouped[judge_id].append(task)
        if self.config.require_negative_controls:
            unique_conditions: dict[str, dict[str, Any]] = {}
            condition_values: dict[str, set[str]] = {}
            condition_presence: dict[str, int] = {}
            for task in tasks:
                item_id = str(task["item_id"])
                condition = task.get("control_condition")
                if condition is None:
                    continue
                condition_presence[item_id] = condition_presence.get(item_id, 0) + 1
                condition_values.setdefault(item_id, set()).add(str(condition))
                unique_conditions[item_id] = {
                    "item_id": item_id,
                    "target_family": str(task["target_family"]),
                    "control_condition": str(condition),
                }
            inconsistent = {
                item_id: sorted(values)
                for item_id, values in condition_values.items()
                if len(values) != 1
            }
            if inconsistent:
                raise PanelConfigurationError(
                    f"control condition differs across judges: {inconsistent}"
                )
            missing_conditions = sorted(
                item_id
                for item_id, count in condition_presence.items()
                if count != len(self.config.judges)
            )
            if len(condition_presence) != len({str(task["item_id"]) for task in tasks}) or missing_conditions:
                raise PanelConfigurationError(
                    "every controlled item must declare one condition for every judge"
                )
            validate_control_matrix(unique_conditions.values())
        self._validate_expected_task_counts(grouped, limit_per_judge=limit_per_judge)
        selected: list[dict[str, Any]] = []
        for judge in self.config.judges:
            rows = sorted(grouped[judge.judge_id], key=lambda row: (str(row["item_id"]), str(row["prompt_sha256"])))
            if limit_per_judge is not None:
                rows = rows[:limit_per_judge]
            selected.extend(rows)
        if not selected:
            raise PanelConfigurationError("panel task input is empty")
        selected.sort(key=lambda row: (str(row["item_id"]), str(row["provider_id"])))
        return selected

    def _validate_expected_task_counts(
        self,
        grouped: Mapping[str, list[dict[str, Any]]],
        *,
        limit_per_judge: int | None,
    ) -> None:
        if any(not rows for rows in grouped.values()):
            missing = sorted(judge_id for judge_id, rows in grouped.items() if not rows)
            raise PanelConfigurationError(
                "each configured judge must receive tasks; missing: " + ", ".join(missing)
            )
        item_sets = {
            judge_id: {str(task["item_id"]) for task in rows}
            for judge_id, rows in grouped.items()
        }
        first_judge = next(iter(item_sets))
        if any(items != item_sets[first_judge] for items in item_sets.values()):
            raise PanelConfigurationError("configured judges must receive the same item set")
        if limit_per_judge is not None:
            return
        counts = {judge_id: len(rows) for judge_id, rows in grouped.items()}
        if self.config.expected_tasks_per_judge is not None:
            expected = self.config.expected_tasks_per_judge
            mismatched = {
                judge_id: count for judge_id, count in counts.items() if count != expected
            }
            if mismatched:
                raise PanelConfigurationError(
                    f"expected {expected} tasks per judge; observed {mismatched}"
                )
        if self.config.expected_total_tasks is not None:
            observed_total = sum(counts.values())
            if observed_total != self.config.expected_total_tasks:
                raise PanelConfigurationError(
                    f"expected {self.config.expected_total_tasks} total tasks; observed {observed_total}"
                )

    def _validate_existing_records(
        self,
        selected: Iterable[Mapping[str, Any]],
        responses: list[dict[str, Any]],
        errors: list[dict[str, Any]],
    ) -> None:
        selected_keys = {
            (str(task["item_id"]), str(task["provider_id"])) for task in selected
        }
        response_keys = _validate_existing_record_set(responses, kind="responses")
        error_keys = _validate_existing_record_set(errors, kind="errors")
        if response_keys & error_keys:
            raise PanelConfigurationError("resume outputs contain both response and error for one task")
        for key in response_keys | error_keys:
            if key not in selected_keys:
                raise PanelConfigurationError(
                    f"resume output contains a task outside the current selection: {key[0]}/{key[1]}"
                )

    def _validate_budget_configuration(
        self,
        resolved: Mapping[str, ResolvedJudgeConfig],
        responses: Iterable[Mapping[str, Any]],
    ) -> None:
        if self.config.max_total_cost_usd is None:
            return
        if any(
            judge.input_usd_per_1k is None or judge.output_usd_per_1k is None
            for judge in resolved.values()
        ):
            raise PanelConfigurationError(
                "max_total_cost_usd requires input/output pricing for every judge"
            )
        if any(row.get("cost_usd") is None for row in responses):
            raise PanelConfigurationError(
                "cannot resume a budgeted run with an unmeasured prior response cost"
            )

    def _configuration_sha256(
        self, resolved: Mapping[str, ResolvedJudgeConfig]
    ) -> str:
        return _hash_json(self._public_configuration(resolved))

    def _public_configuration(
        self, resolved: Mapping[str, ResolvedJudgeConfig]
    ) -> dict[str, Any]:
        """Return the complete non-secret configuration identity."""

        return {
            "schema_version": self.config.schema_version,
            "stage": self.config.stage,
            "expected_tasks_per_judge": self.config.expected_tasks_per_judge,
            "expected_total_tasks": self.config.expected_total_tasks,
            "require_negative_controls": self.config.require_negative_controls,
            "max_total_cost_usd": self.config.max_total_cost_usd,
            "consensus_required": self.config.consensus_required,
            "defaults": {
                "timeout_seconds": self.config.timeout_seconds,
                "max_retries": self.config.max_retries,
                "retry_backoff_seconds": self.config.retry_backoff_seconds,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "reasoning_effort": self.config.reasoning_effort,
                "input_usd_per_1k": self.config.input_usd_per_1k,
                "cached_input_usd_per_1k": self.config.cached_input_usd_per_1k,
                "output_usd_per_1k": self.config.output_usd_per_1k,
            },
            "judges": [
                {
                    "judge_id": judge.judge_id,
                    "adapter": judge.adapter,
                    "model": resolved[judge.judge_id].model,
                    "model_snapshot": resolved[judge.judge_id].model_snapshot,
                    "model_snapshot_declared": resolved[judge.judge_id].model_snapshot_declared,
                    "model_env": judge.model_env,
                    "model_snapshot_env": judge.model_snapshot_env,
                    "endpoint_env": judge.endpoint_env,
                    "api_key_env": judge.api_key_env,
                    "endpoint_sha256": _hash_text(resolved[judge.judge_id].endpoint or ""),
                    "api_version": resolved[judge.judge_id].api_version,
                    "max_tokens": resolved[judge.judge_id].max_tokens,
                    "temperature": resolved[judge.judge_id].temperature,
                    "reasoning_effort": resolved[judge.judge_id].reasoning_effort,
                    "timeout_seconds": resolved[judge.judge_id].timeout_seconds,
                    "max_retries": resolved[judge.judge_id].max_retries,
                    "input_usd_per_1k": resolved[judge.judge_id].input_usd_per_1k,
                    "cached_input_usd_per_1k": resolved[judge.judge_id].cached_input_usd_per_1k,
                    "output_usd_per_1k": resolved[judge.judge_id].output_usd_per_1k,
                }
                for judge in self.config.judges
            ],
        }

    def _resolve_judges(self) -> tuple[dict[str, ResolvedJudgeConfig], list[str]]:
        resolved: dict[str, ResolvedJudgeConfig] = {}
        errors: list[str] = []
        for judge in self.config.judges:
            try:
                resolved[judge.judge_id] = judge.resolve(self.config)
            except PanelConfigurationError as exc:
                errors.append(str(exc))
        return resolved, errors

    def _execute_task(
        self,
        task: Mapping[str, Any],
        judge: ResolvedJudgeConfig,
        adapter: PanelAdapter,
        *,
        run_id: str,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        prompt = str(task["prompt"])
        prompt_hash = str(task["prompt_sha256"])
        request_hash = _hash_json(
            {
                "adapter": judge.adapter,
                "endpoint_sha256": _hash_text(judge.endpoint or ""),
                "judge_id": judge.judge_id,
                "model": judge.model,
                "prompt_sha256": prompt_hash,
                "target_family": str(task["target_family"]),
            }
        )
        started = time.perf_counter()
        attempts = 0
        last_error: Exception | None = None
        response: AdapterResponse | None = None
        max_attempts = judge.max_retries + 1
        for attempt in range(max_attempts):
            attempts = attempt + 1
            try:
                response = adapter.complete(prompt=prompt, judge=judge)
                if not response.text.strip():
                    raise PanelAdapterError("adapter returned empty text", retryable=False)
                break
            except PanelAdapterError as exc:
                last_error = exc
                if not exc.retryable or attempts >= max_attempts:
                    break
            except (TimeoutError, OSError) as exc:
                last_error = exc
                if attempts >= max_attempts:
                    break
            if self.config.retry_backoff_seconds:
                self._sleeper(self.config.retry_backoff_seconds * (2**attempt))
        latency_ms = round((time.perf_counter() - started) * 1000.0, 3)
        if response is None:
            assert last_error is not None
            return None, {
                "schema_version": RESPONSE_SCHEMA_VERSION,
                "run_id": run_id,
                "item_id": str(task["item_id"]),
                "provider_id": judge.judge_id,
                "model_id": judge.model,
                "target_family": str(task["target_family"]),
                "prompt_sha256": prompt_hash,
                "request_sha256": request_hash,
                "status": "error",
                "error_type": type(last_error).__name__,
                "error_message": _safe_error(last_error, judge.endpoint),
                "attempts": attempts,
                "latency_ms": latency_ms,
                "usage": {},
                "cost_usd": None,
            }
        try:
            payload = _extract_json_object(response.text)
            reserved = {"item_id", "provider_id", "model_id"}
            if reserved.intersection(payload):
                raise ValueError("model response must not provide provenance identity fields")
            annotation = {
                **payload,
                "item_id": str(task["item_id"]),
                "provider_id": judge.judge_id,
                "model_id": judge.model,
            }
            validated = validate_panel_annotation(
                annotation,
                allowed_providers=(judge.judge_id,),
            )
        except (ValueError, json.JSONDecodeError) as exc:
            return None, {
                "schema_version": RESPONSE_SCHEMA_VERSION,
                "run_id": run_id,
                "item_id": str(task["item_id"]),
                "provider_id": judge.judge_id,
                "model_id": judge.model,
                "target_family": str(task["target_family"]),
                "prompt_sha256": prompt_hash,
                "request_sha256": request_hash,
                "response_sha256": _hash_text(response.text),
                "status": "error",
                "error_type": type(exc).__name__,
                "error_message": _safe_error(exc, judge.endpoint),
                "attempts": attempts,
                "latency_ms": latency_ms,
                "usage": _normalize_usage(response.usage),
                "cost_usd": _estimate_cost(
                    response.usage,
                    input_usd_per_1k=judge.input_usd_per_1k,
                    cached_input_usd_per_1k=judge.cached_input_usd_per_1k,
                    output_usd_per_1k=judge.output_usd_per_1k,
                ),
            }
        record = {
            "schema_version": RESPONSE_SCHEMA_VERSION,
            "run_id": run_id,
            "panel_version": str(task.get("panel_version", "unknown")),
            **validated,
            "adapter": judge.adapter,
            "prompt_sha256": prompt_hash,
            "request_sha256": request_hash,
            "response_sha256": _hash_text(response.text),
            "attempts": attempts,
            "latency_ms": latency_ms,
            "usage": _normalize_usage(response.usage),
            "cost_usd": _estimate_cost(
                response.usage,
                input_usd_per_1k=judge.input_usd_per_1k,
                cached_input_usd_per_1k=judge.cached_input_usd_per_1k,
                output_usd_per_1k=judge.output_usd_per_1k,
            ),
        }
        if task.get("control_condition") is not None:
            record["control_condition"] = str(task["control_condition"])
        return record, None

    def _build_manifest(
        self,
        *,
        run_id: str,
        all_tasks: list[dict[str, Any]],
        selected_tasks: list[dict[str, Any]],
        responses: list[dict[str, Any]],
        errors: list[dict[str, Any]],
        resolved: Mapping[str, ResolvedJudgeConfig],
        started: datetime,
        finished: datetime,
        wall_ms: float,
        responses_path: Path,
        errors_path: Path,
        status: str,
        resumed: bool,
        stop_reason: str | None,
        budget_status: str,
    ) -> dict[str, Any]:
        judges = [resolved[judge.judge_id] for judge in self.config.judges]
        public_configuration = self._public_configuration(resolved)
        control_counts = Counter(
            (
                str(task.get("target_family", "")),
                str(task.get("control_condition", "")),
            )
            for task in selected_tasks
            if task.get("control_condition") is not None
        )
        return {
            "schema_version": "requirements-smell-panel-run-manifest/v1",
            "run_id": run_id,
            "status": status,
            "stage": self.config.stage,
            "stage_contract_version": "requirements-smell-panel-stages/v1",
            "resumed": resumed,
            "stop_reason": stop_reason,
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
            "wall_time_ms": round(wall_ms, 3),
            "task_input_sha256": _hash_json(all_tasks),
            "selected_task_count": len(selected_tasks),
            "requested_task_count": len(all_tasks),
            "ok_count": len(responses),
            "error_count": len(errors),
            "completed_task_count": len(responses) + len(errors),
            "remaining_task_count": max(0, len(selected_tasks) - len(responses) - len(errors)),
            "expected_tasks_per_judge": self.config.expected_tasks_per_judge,
            "expected_total_tasks": self.config.expected_total_tasks,
            "units": {
                "candidate_count": len({str(task["item_id"]) for task in selected_tasks}),
                "task_count": len(selected_tasks),
                "tasks_per_judge": dict(
                    sorted(
                        Counter(str(task["provider_id"]) for task in selected_tasks).items()
                    )
                ),
                "provider_call_count": len(responses) + len(errors),
            },
            "control_strata": {
                f"{family}:{condition}": count
                for (family, condition), count in sorted(control_counts.items())
            },
            "consensus_required": self.config.consensus_required,
            "raw_prompts_in_repository": False,
            "raw_responses_in_repository": False,
            "responses_sha256": _hash_file(responses_path),
            "errors_sha256": _hash_file(errors_path),
            "config_sha256": self._configuration_sha256(resolved),
            "configuration": public_configuration,
            "judges": [
                {
                    "judge_id": judge.judge_id,
                    "adapter": judge.adapter,
                    "model_id": judge.model,
                    "model_snapshot": judge.model_snapshot,
                    "model_snapshot_declared": judge.model_snapshot_declared,
                    "endpoint_sha256": _hash_text(judge.endpoint or ""),
                }
                for judge in judges
            ],
            "latency": {
                "measured": True,
                "total_ms": round(sum(float(row["latency_ms"]) for row in responses + errors), 3),
                "successful_response_count": len(responses),
            },
            "usage": _summarize_usage(responses),
            "cost": _summarize_cost(responses + errors, judges),
            "budget": {
                "limit_usd": self.config.max_total_cost_usd,
                "status": budget_status,
                "spent_usd": _known_cost_total(responses + errors)
                if all(row.get("cost_usd") is not None for row in responses + errors)
                else None,
            },
        }


def load_panel_tasks(path: str | Path) -> list[dict[str, Any]]:
    """Load private JSONL tasks without exposing their text in summaries."""

    return load_jsonl(path)


def _load_existing_rows(
    path: Path,
    *,
    run_id: str,
    resume: bool,
    kind: str,
) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    if not resume:
        raise PanelConfigurationError(
            f"{kind} output already exists; pass resume=True to continue the run"
        )
    rows = load_jsonl(path)
    for row in rows:
        if str(row.get("run_id", "")) != run_id:
            raise PanelConfigurationError(f"{kind} output contains a different run_id")
    return rows


def _load_existing_manifest(
    path: Path,
    *,
    run_id: str,
    resume: bool,
) -> dict[str, Any] | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    if not resume:
        raise PanelConfigurationError(
            "manifest output already exists; pass resume=True to continue the run"
        )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PanelConfigurationError("existing run manifest is invalid JSON") from exc
    if not isinstance(value, dict) or str(value.get("run_id", "")) != run_id:
        raise PanelConfigurationError("existing run manifest contains a different run_id")
    return value


def _validate_existing_record_set(
    records: Iterable[Mapping[str, Any]], *, kind: str
) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for index, row in enumerate(records):
        item_id = str(row.get("item_id", "")).strip()
        judge_id = str(row.get("provider_id", "")).strip()
        if not item_id or not judge_id:
            raise PanelConfigurationError(f"{kind} row {index} lacks item_id/provider_id")
        key = (item_id, judge_id)
        if key in keys:
            raise PanelConfigurationError(f"{kind} output contains duplicate task {item_id}/{judge_id}")
        keys.add(key)
    return keys


def _record_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return str(row.get("item_id", "")), str(row.get("provider_id", ""))


def _sorted_records(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        (dict(record) for record in records),
        key=lambda row: (str(row.get("item_id", "")), str(row.get("provider_id", ""))),
    )


def _atomic_write_jsonl(path: str | Path, rows: Iterable[Mapping[str, Any]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    _write_jsonl(temporary, rows)
    os.replace(temporary, target)


def _known_cost_total(records: Iterable[Mapping[str, Any]]) -> float:
    return round(
        sum(float(row["cost_usd"]) for row in records if row.get("cost_usd") is not None),
        8,
    )


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _reject_unknown_keys(value: Mapping[str, Any], allowed: set[str], name: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise PanelConfigurationError(f"{name} contains unsupported fields: {unknown}")


def _resolve_value(value: str | None, env_name: str | None, description: str) -> str | None:
    if value and env_name:
        raise PanelConfigurationError(f"cannot set both literal and environment-backed {description}")
    resolved = value or (os.environ.get(env_name) if env_name else None)
    return resolved.strip() if isinstance(resolved, str) and resolved.strip() else None


def _validate_endpoint(endpoint: str, judge_id: str) -> None:
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        raise PanelConfigurationError(f"judge {judge_id} endpoint must be an HTTP(S) URL without embedded credentials")


def _extract_json_object(text: str) -> dict[str, Any]:
    candidate = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", candidate, re.DOTALL | re.IGNORECASE)
    if fenced:
        candidate = fenced.group(1)
    else:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("model response did not contain a JSON object")
        candidate = candidate[start : end + 1]
    value = json.loads(candidate)
    if not isinstance(value, dict):
        raise ValueError("model response JSON must be an object")
    return value


def _content_to_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        chunks: list[str] = []
        for item in value:
            if isinstance(item, str):
                chunks.append(item)
            elif isinstance(item, Mapping) and isinstance(item.get("text"), str):
                chunks.append(str(item["text"]))
        return "".join(chunks)
    return ""


def _normalize_usage(value: Mapping[str, Any]) -> dict[str, int | float]:
    result: dict[str, int | float] = {}
    for key, item in value.items():
        if isinstance(item, bool):
            continue
        if isinstance(item, (int, float)):
            result[str(key)] = item
    input_tokens = result.get("input_tokens", result.get("prompt_tokens"))
    output_tokens = result.get("output_tokens", result.get("completion_tokens"))
    if isinstance(input_tokens, (int, float)):
        result.setdefault("input_tokens", input_tokens)
    if isinstance(output_tokens, (int, float)):
        result.setdefault("output_tokens", output_tokens)
    if "cached_tokens" not in result:
        cached_tokens = _nested_usage_number(
            value,
            ("input_tokens_details", "cached_tokens"),
            ("prompt_tokens_details", "cached_tokens"),
            ("input_token_details", "cached_tokens"),
        )
        if cached_tokens is None:
            for key in (
                "input_cached_tokens",
                "cache_read_input_tokens",
                "prompt_cache_hit_tokens",
            ):
                candidate = value.get(key)
                if isinstance(candidate, (int, float)) and not isinstance(candidate, bool):
                    cached_tokens = candidate
                    break
        if cached_tokens is not None:
            result["cached_tokens"] = cached_tokens
    if "reasoning_tokens" not in result:
        reasoning_tokens = _nested_usage_number(
            value,
            ("output_tokens_details", "reasoning_tokens"),
            ("completion_tokens_details", "reasoning_tokens"),
            ("output_token_details", "reasoning_tokens"),
        )
        if reasoning_tokens is not None:
            result["reasoning_tokens"] = reasoning_tokens
    if "total_tokens" not in result:
        if isinstance(input_tokens, (int, float)) and isinstance(output_tokens, (int, float)):
            result["total_tokens"] = input_tokens + output_tokens
    return result


def _nested_usage_number(
    value: Mapping[str, Any], paths: tuple[str, str], *more_paths: tuple[str, str]
) -> int | float | None:
    """Read a numeric usage detail from common provider response shapes."""

    for container_key, field_key in (paths, *more_paths):
        container = value.get(container_key)
        if not isinstance(container, Mapping):
            continue
        candidate = container.get(field_key)
        if isinstance(candidate, (int, float)) and not isinstance(candidate, bool):
            return candidate
    return None


def _summarize_usage(records: Iterable[Mapping[str, Any]]) -> dict[str, int | float]:
    totals: dict[str, int | float] = {}
    for record in records:
        usage = record.get("usage")
        if not isinstance(usage, Mapping):
            continue
        for key, value in usage.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            totals[str(key)] = totals.get(str(key), 0) + value
    return dict(sorted(totals.items()))


def _estimate_cost(
    usage: Mapping[str, Any],
    *,
    input_usd_per_1k: float | None,
    cached_input_usd_per_1k: float | None = None,
    output_usd_per_1k: float | None,
) -> float | None:
    if input_usd_per_1k is None or output_usd_per_1k is None:
        return None
    input_tokens = usage.get("input_tokens", usage.get("prompt_tokens"))
    output_tokens = usage.get("output_tokens", usage.get("completion_tokens"))
    if not isinstance(input_tokens, (int, float)) or not isinstance(output_tokens, (int, float)):
        return None
    cached_tokens = usage.get("cached_tokens", 0)
    if not isinstance(cached_tokens, (int, float)) or isinstance(cached_tokens, bool):
        cached_tokens = 0
    cached_tokens = min(max(float(cached_tokens), 0.0), float(input_tokens))
    uncached_tokens = float(input_tokens) - cached_tokens
    if cached_input_usd_per_1k is None:
        input_cost = float(input_tokens) / 1000 * input_usd_per_1k
    else:
        input_cost = (
            uncached_tokens / 1000 * input_usd_per_1k
            + cached_tokens / 1000 * cached_input_usd_per_1k
        )
    return round(input_cost + (float(output_tokens) / 1000 * output_usd_per_1k), 8)


def _summarize_cost(
    records: Iterable[Mapping[str, Any]], judges: Iterable[ResolvedJudgeConfig]
) -> dict[str, Any]:
    resolved_judges = tuple(judges)
    values = [record.get("cost_usd") for record in records]
    if not values:
        return {"status": "no_successful_responses", "total_usd": None}
    if not any(
        judge.input_usd_per_1k is not None and judge.output_usd_per_1k is not None
        for judge in resolved_judges
    ):
        return {"status": "not_configured", "total_usd": None}
    if any(value is None for value in values):
        return {"status": "incomplete_usage", "total_usd": None}
    return {"status": "measured", "total_usd": round(sum(float(value) for value in values), 8)}


def _write_jsonl(path: str | Path, rows: Iterable[Mapping[str, Any]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "".join(_canonical_json(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _hash_json(value: Any) -> str:
    return _hash_text(_canonical_json(value))


def _hash_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _safe_error(error: Exception, endpoint: str | None) -> str:
    message = str(error).replace("\n", " ").strip()[:240]
    if endpoint:
        message = message.replace(endpoint, "<endpoint>")
    return message or type(error).__name__


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_positive_int(value: Any, name: str) -> int | None:
    if value is None:
        return None
    return _positive_int(value, name)


def _optional_nonnegative_int(value: Any, name: str) -> int | None:
    if value is None:
        return None
    return _nonnegative_int(value, name)


def _optional_positive_float(value: Any, name: str) -> float | None:
    if value is None:
        return None
    return _positive_float(value, name)


def _optional_nonnegative_float(value: Any, name: str) -> float | None:
    if value is None:
        return None
    return _nonnegative_float(value, name)


def _optional_float(value: Any, name: str) -> float | None:
    if value is None:
        return None
    return _bounded_float(value, name, 0, 2)


def _positive_int(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise PanelConfigurationError(f"{name} must be a positive integer")
    if isinstance(value, float) and not value.is_integer():
        raise PanelConfigurationError(f"{name} must be a positive integer")
    if isinstance(value, str) and not re.fullmatch(r"[+]?\d+", value.strip()):
        raise PanelConfigurationError(f"{name} must be a positive integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise PanelConfigurationError(f"{name} must be a positive integer") from exc
    if parsed <= 0:
        raise PanelConfigurationError(f"{name} must be a positive integer")
    return parsed


def _nonnegative_int(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise PanelConfigurationError(f"{name} must be a non-negative integer")
    if isinstance(value, float) and not value.is_integer():
        raise PanelConfigurationError(f"{name} must be a non-negative integer")
    if isinstance(value, str) and not re.fullmatch(r"[+]?\d+", value.strip()):
        raise PanelConfigurationError(f"{name} must be a non-negative integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise PanelConfigurationError(f"{name} must be a non-negative integer") from exc
    if parsed < 0:
        raise PanelConfigurationError(f"{name} must be a non-negative integer")
    return parsed


def _positive_float(value: Any, name: str) -> float:
    parsed = _finite_float(value, name)
    if parsed <= 0:
        raise PanelConfigurationError(f"{name} must be positive")
    return parsed


def _nonnegative_float(value: Any, name: str) -> float:
    parsed = _finite_float(value, name)
    if parsed < 0:
        raise PanelConfigurationError(f"{name} must be non-negative")
    return parsed


def _bounded_float(value: Any, name: str, lower: float, upper: float) -> float:
    parsed = _finite_float(value, name)
    if not lower <= parsed <= upper:
        raise PanelConfigurationError(f"{name} must be between {lower} and {upper}")
    return parsed


def _finite_float(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise PanelConfigurationError(f"{name} must be numeric")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise PanelConfigurationError(f"{name} must be numeric") from exc
    if parsed != parsed or parsed in {float("inf"), float("-inf")}:
        raise PanelConfigurationError(f"{name} must be finite")
    return parsed


__all__ = [
    "AdapterResponse",
    "AnthropicMessagesAdapter",
    "JudgeConfig",
    "OpenAICompatibleAdapter",
    "PanelAdapterError",
    "PanelConfigurationError",
    "PanelRunConfig",
    "PanelRunner",
    "PANEL_STAGES",
    "ResolvedJudgeConfig",
    "load_panel_tasks",
]
