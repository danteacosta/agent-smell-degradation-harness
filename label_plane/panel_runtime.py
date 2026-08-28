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
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Protocol
from urllib.parse import urlparse

from label_plane.llm_panel import load_jsonl, validate_panel_annotation

RUNTIME_SCHEMA_VERSION = "requirements-smell-panel-runtime/v1"
RESPONSE_SCHEMA_VERSION = "requirements-smell-panel-response/v1"
_HTTP_ADAPTERS = frozenset({"openai_compatible", "anthropic_messages"})
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
    endpoint: str | None = None
    endpoint_env: str | None = None
    api_key_env: str | None = None
    api_version: str = "2023-06-01"
    max_tokens: int | None = None
    temperature: float | None = None
    timeout_seconds: float | None = None
    max_retries: int | None = None
    input_usd_per_1k: float | None = None
    output_usd_per_1k: float | None = None

    def resolve(self, defaults: "PanelRunConfig") -> "ResolvedJudgeConfig":
        model = _resolve_value(self.model, self.model_env, f"model for {self.judge_id}")
        endpoint = _resolve_value(self.endpoint, self.endpoint_env, f"endpoint for {self.judge_id}")
        configuration_errors: list[str] = []
        if not model:
            configuration_errors.append(
                f"missing model for judge {self.judge_id}; set {self.model_env or 'model'}"
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
    endpoint: str | None
    api_key: str | None = field(default=None, repr=False)
    api_version: str = "2023-06-01"
    max_tokens: int = 512
    temperature: float = 0.0
    timeout_seconds: float = 60.0
    max_retries: int = 2
    input_usd_per_1k: float | None = None
    output_usd_per_1k: float | None = None


@dataclass(frozen=True)
class PanelRunConfig:
    """Validated, vendor-neutral configuration for one panel run."""

    judges: tuple[JudgeConfig, ...]
    consensus_required: int = 2
    timeout_seconds: float = 60.0
    max_retries: int = 2
    retry_backoff_seconds: float = 1.0
    max_tokens: int = 512
    temperature: float = 0.0
    input_usd_per_1k: float | None = None
    output_usd_per_1k: float | None = None
    max_total_cost_usd: float | None = None
    max_total_attempts: int | None = None
    min_request_interval_seconds: float = 0.0
    schema_version: str = RUNTIME_SCHEMA_VERSION

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "PanelRunConfig":
        if raw.get("schema_version") != RUNTIME_SCHEMA_VERSION:
            raise PanelConfigurationError(
                f"schema_version must be {RUNTIME_SCHEMA_VERSION}"
            )
        raw_judges = raw.get("judges")
        if not isinstance(raw_judges, list) or len(raw_judges) < 2:
            raise PanelConfigurationError("panel config requires at least two judges")
        judges: list[JudgeConfig] = []
        for index, value in enumerate(raw_judges):
            if not isinstance(value, Mapping):
                raise PanelConfigurationError(f"judge {index} must be an object")
            judge_id = str(value.get("judge_id", "")).strip()
            adapter = str(value.get("adapter", "")).strip()
            if not judge_id or not adapter:
                raise PanelConfigurationError(f"judge {index} requires judge_id and adapter")
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", judge_id):
                raise PanelConfigurationError(f"invalid judge_id: {judge_id}")
            for key in ("api_key_env", "model_env", "endpoint_env"):
                configured = value.get(key)
                if configured is not None and not _ENV_NAME.fullmatch(str(configured)):
                    raise PanelConfigurationError(f"{key} must be an environment variable name")
            if value.get("model") is not None and value.get("model_env") is not None:
                raise PanelConfigurationError(f"judge {judge_id} cannot set model and model_env together")
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
        pricing = raw.get("pricing", {})
        if not isinstance(pricing, Mapping):
            raise PanelConfigurationError("pricing must be an object")
        input_usd_per_1k = _optional_nonnegative_float(
            pricing.get("input_usd_per_1k"), "pricing.input_usd_per_1k"
        )
        output_usd_per_1k = _optional_nonnegative_float(
            pricing.get("output_usd_per_1k"), "pricing.output_usd_per_1k"
        )
        max_total_cost_usd = _optional_positive_float(
            raw.get("max_total_cost_usd"), "max_total_cost_usd"
        )
        max_total_attempts = _optional_positive_int(
            raw.get("max_total_attempts"), "max_total_attempts"
        )
        min_request_interval_seconds = _nonnegative_float(
            raw.get("min_request_interval_seconds", 0), "min_request_interval_seconds"
        )
        return cls(
            judges=tuple(judges),
            consensus_required=consensus_required,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            retry_backoff_seconds=retry_backoff_seconds,
            max_tokens=max_tokens,
            temperature=temperature,
            input_usd_per_1k=input_usd_per_1k,
            output_usd_per_1k=output_usd_per_1k,
            max_total_cost_usd=max_total_cost_usd,
            max_total_attempts=max_total_attempts,
            min_request_interval_seconds=min_request_interval_seconds,
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
        payload = self._post(
            judge=judge,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {judge.api_key}",
            },
            body={
                "model": judge.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": judge.temperature,
                "max_tokens": judge.max_tokens,
            },
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
        require_budget_cap: bool = False,
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
        budget = self._preflight_budget(selected, resolved, require_budget_cap=require_budget_cap)
        started = datetime.now(timezone.utc)
        started_perf = time.perf_counter()
        responses: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        last_request_at: dict[str, float] = {}
        for task in selected:
            judge = resolved[str(task["provider_id"])]
            adapter = self.adapters.get(judge.adapter)
            if adapter is None:
                raise PanelConfigurationError(
                    f"no adapter registered for {judge.adapter}; add an adapter without changing the panel protocol"
                )
            previous = last_request_at.get(judge.judge_id)
            if previous is not None and self.config.min_request_interval_seconds:
                delay = self.config.min_request_interval_seconds - (time.monotonic() - previous)
                if delay > 0:
                    self._sleeper(delay)
            record, error = self._execute_task(task, judge, adapter, run_id=run_id)
            last_request_at[judge.judge_id] = time.monotonic()
            if record is not None:
                responses.append(record)
            if error is not None:
                errors.append(error)
        _write_jsonl(responses_path, responses)
        _write_jsonl(errors_path, errors)
        finished = datetime.now(timezone.utc)
        wall_ms = (time.perf_counter() - started_perf) * 1000.0
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
            responses_path=Path(responses_path),
            errors_path=Path(errors_path),
            limited=limit_per_judge is not None,
            budget=budget,
        )
        manifest_path = Path(manifest_path)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(_canonical_json(manifest) + "\n", encoding="utf-8")
        return manifest

    def _preflight_budget(
        self,
        selected: list[dict[str, Any]],
        resolved: Mapping[str, ResolvedJudgeConfig],
        *,
        require_budget_cap: bool,
    ) -> dict[str, Any]:
        max_attempts = sum(resolved[str(task["provider_id"])].max_retries + 1 for task in selected)
        if self.config.max_total_attempts is not None and max_attempts > self.config.max_total_attempts:
            raise PanelConfigurationError(
                f"selected panel tasks require up to {max_attempts} attempts, exceeding max_total_attempts={self.config.max_total_attempts}"
            )
        estimate: float | None = 0.0
        for task in selected:
            judge = resolved[str(task["provider_id"])]
            item_cost = _worst_case_task_cost(str(task["prompt"]), judge)
            if item_cost is None:
                estimate = None
                break
            estimate += item_cost * (judge.max_retries + 1)
        if estimate is not None:
            estimate = round(estimate, 8)
        if require_budget_cap:
            if self.config.max_total_cost_usd is None:
                raise PanelConfigurationError("full panel run requires max_total_cost_usd in the runtime config")
            if estimate is None:
                raise PanelConfigurationError(
                    "full panel run requires input/output pricing for every judge so its cost cap can be enforced"
                )
        if self.config.max_total_cost_usd is not None and estimate is not None and estimate > self.config.max_total_cost_usd:
            raise PanelConfigurationError(
                f"conservative panel cost estimate ${estimate:.8f} exceeds max_total_cost_usd=${self.config.max_total_cost_usd:.8f}"
            )
        return {
            "max_total_cost_usd": self.config.max_total_cost_usd,
            "max_total_attempts": self.config.max_total_attempts,
            "conservative_max_cost_usd": estimate,
            "conservative_max_attempts": max_attempts,
            "min_request_interval_seconds": self.config.min_request_interval_seconds,
            "full_run_budget_gate": require_budget_cap,
        }

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
            }
        return {
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
                output_usd_per_1k=judge.output_usd_per_1k,
            ),
        }, None

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
        limited: bool,
        budget: Mapping[str, Any],
    ) -> dict[str, Any]:
        judges = [resolved[judge.judge_id] for judge in self.config.judges]
        return {
            "schema_version": "requirements-smell-panel-run-manifest/v1",
            "run_id": run_id,
            "status": "completed_with_smoke_limit" if limited else "completed",
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
            "wall_time_ms": round(wall_ms, 3),
            "task_input_sha256": _hash_json(all_tasks),
            "selected_task_count": len(selected_tasks),
            "requested_task_count": len(all_tasks),
            "ok_count": len(responses),
            "error_count": len(errors),
            "consensus_required": self.config.consensus_required,
            "raw_prompts_in_repository": False,
            "raw_responses_in_repository": False,
            "responses_sha256": _hash_file(responses_path),
            "errors_sha256": _hash_file(errors_path),
            "config_sha256": _hash_json(
                {
                    "schema_version": self.config.schema_version,
                    "consensus_required": self.config.consensus_required,
                    "defaults": {
                        "timeout_seconds": self.config.timeout_seconds,
                        "max_retries": self.config.max_retries,
                        "retry_backoff_seconds": self.config.retry_backoff_seconds,
                        "max_tokens": self.config.max_tokens,
                        "temperature": self.config.temperature,
                        "input_usd_per_1k": self.config.input_usd_per_1k,
                        "output_usd_per_1k": self.config.output_usd_per_1k,
                    },
                    "judges": [
                        {
                            "judge_id": judge.judge_id,
                            "adapter": judge.adapter,
                            "model": judge.model,
                            "endpoint_sha256": _hash_text(judge.endpoint or ""),
                            "api_version": judge.api_version,
                            "max_tokens": judge.max_tokens,
                            "temperature": judge.temperature,
                            "timeout_seconds": judge.timeout_seconds,
                            "max_retries": judge.max_retries,
                            "input_usd_per_1k": judge.input_usd_per_1k,
                            "output_usd_per_1k": judge.output_usd_per_1k,
                        }
                        for judge in judges
                    ],
                }
            ),
            "judges": [
                {
                    "judge_id": judge.judge_id,
                    "adapter": judge.adapter,
                    "model_id": judge.model,
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
            "cost": _summarize_cost(responses, judges),
            "budget": dict(budget),
        }


def load_panel_tasks(path: str | Path) -> list[dict[str, Any]]:
    """Load private JSONL tasks without exposing their text in summaries."""

    return load_jsonl(path)


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
    if "total_tokens" not in result:
        input_tokens = result.get("input_tokens", result.get("prompt_tokens"))
        output_tokens = result.get("output_tokens", result.get("completion_tokens"))
        if isinstance(input_tokens, (int, float)) and isinstance(output_tokens, (int, float)):
            result["total_tokens"] = input_tokens + output_tokens
    return result


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
    output_usd_per_1k: float | None,
) -> float | None:
    if input_usd_per_1k is None or output_usd_per_1k is None:
        return None
    input_tokens = usage.get("input_tokens", usage.get("prompt_tokens"))
    output_tokens = usage.get("output_tokens", usage.get("completion_tokens"))
    if not isinstance(input_tokens, (int, float)) or not isinstance(output_tokens, (int, float)):
        return None
    return round(
        (float(input_tokens) / 1000 * input_usd_per_1k)
        + (float(output_tokens) / 1000 * output_usd_per_1k),
        8,
    )


def _worst_case_task_cost(prompt: str, judge: ResolvedJudgeConfig) -> float | None:
    """Conservative preflight estimate used only to prevent accidental overspend.

    Input tokens are conservatively bounded by UTF-8 bytes and output is bounded by
    the configured provider maximum.  This is intentionally a ceiling rather
    than a billing report; measured usage remains the cost record.
    """

    if judge.input_usd_per_1k is None or judge.output_usd_per_1k is None:
        return None
    input_tokens = max(1, len(prompt.encode("utf-8")))
    return (
        input_tokens / 1000 * judge.input_usd_per_1k
        + judge.max_tokens / 1000 * judge.output_usd_per_1k
    )


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
    "ResolvedJudgeConfig",
    "load_panel_tasks",
]
