"""Provider boundary for live and offline agent completions.

The live adapters expose only bounded response metadata.  They never export
credentials, prompts, responses, or hidden reasoning.  OpenAI-compatible
providers are intentionally configured with explicit model and model-version
values so a qualification report can be reproduced after a vendor alias
moves.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from agents.stub import StubAgent


@dataclass(frozen=True)
class ProviderRequest:
    prompt: str
    pair: dict[str, Any]
    variant: str
    task_family: str


def provider_visible_pair(
    pair: dict[str, Any],
    *,
    variant: str,
    task_family: str,
) -> dict[str, Any]:
    """Build the minimum context a provider may inspect.

    The full pair remains local to the harness for contract checks and labels.
    Providers receive neither variants nor source annotations, oracle data,
    smell metadata, project metadata, nor the paired alternative requirement.
    """

    requirement_key = "clean_requirement" if variant == "clean" else "smelly_requirement"
    requirement = pair.get(requirement_key)
    contract = pair.get("generation_contract", {})
    task_contract = contract.get(task_family, {}) if isinstance(contract, dict) else {}
    output_keys = task_contract.get("output_keys", []) if isinstance(task_contract, dict) else []
    return {
        "requirement": requirement,
        "task_family": task_family,
        "output_keys": list(output_keys) if isinstance(output_keys, list) else [],
    }


class Provider(Protocol):
    name: str

    def complete(self, request: ProviderRequest) -> str: ...


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    for method_name in ("model_dump", "to_dict"):
        method = getattr(value, method_name, None)
        if callable(method):
            try:
                candidate = method()
            except TypeError:
                candidate = method(mode="json")
            if isinstance(candidate, Mapping):
                return dict(candidate)
    raw = getattr(value, "__dict__", None)
    return dict(raw) if isinstance(raw, Mapping) else {}


def _number(value: Any) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


def _first_number(mapping: Mapping[str, Any], *keys: str) -> int | float | None:
    for key in keys:
        value = _number(mapping.get(key))
        if value is not None:
            return value
    return None


def _nested_number(mapping: Mapping[str, Any], *paths: tuple[str, str]) -> int | float | None:
    for container_key, field_key in paths:
        container = _as_mapping(mapping.get(container_key))
        value = _number(container.get(field_key))
        if value is not None:
            return value
    return None


def normalize_provider_usage(raw_usage: Any) -> dict[str, int | float]:
    """Normalize common OpenAI/Anthropic usage shapes without raw payloads."""

    usage = _as_mapping(raw_usage)
    normalized: dict[str, int | float] = {}
    input_tokens = _first_number(usage, "input_tokens", "prompt_tokens")
    output_tokens = _first_number(usage, "output_tokens", "completion_tokens")
    total_tokens = _first_number(usage, "total_tokens")
    cached_tokens = _first_number(usage, "cached_tokens")
    if cached_tokens is None:
        cached_tokens = _nested_number(
            usage,
            ("prompt_tokens_details", "cached_tokens"),
            ("input_tokens_details", "cached_tokens"),
            ("prompt_token_details", "cached_tokens"),
            ("input_token_details", "cached_tokens"),
        )
    reasoning_tokens = _first_number(usage, "reasoning_tokens")
    if reasoning_tokens is None:
        reasoning_tokens = _nested_number(
            usage,
            ("completion_tokens_details", "reasoning_tokens"),
            ("output_tokens_details", "reasoning_tokens"),
            ("completion_token_details", "reasoning_tokens"),
            ("output_token_details", "reasoning_tokens"),
        )
    if input_tokens is not None:
        normalized["input_tokens"] = input_tokens
    if output_tokens is not None:
        normalized["output_tokens"] = output_tokens
    if total_tokens is not None:
        normalized["total_tokens"] = total_tokens
    elif input_tokens is not None and output_tokens is not None:
        normalized["total_tokens"] = input_tokens + output_tokens
    if cached_tokens is not None:
        normalized["cached_tokens"] = cached_tokens
    if reasoning_tokens is not None:
        normalized["reasoning_tokens"] = reasoning_tokens
    return dict(sorted(normalized.items()))


def estimate_provider_cost(
    usage: Mapping[str, Any],
    *,
    input_usd_per_1k: float | None,
    output_usd_per_1k: float | None,
    cached_input_usd_per_1k: float | None = None,
) -> float | None:
    """Estimate one call's USD cost from observed usage and frozen prices."""

    if input_usd_per_1k is None or output_usd_per_1k is None:
        return None
    input_tokens = _first_number(usage, "input_tokens", "prompt_tokens")
    output_tokens = _first_number(usage, "output_tokens", "completion_tokens")
    if input_tokens is None or output_tokens is None:
        return None
    if min(input_usd_per_1k, output_usd_per_1k) < 0:
        raise ValueError("provider prices must be non-negative")
    if cached_input_usd_per_1k is not None and cached_input_usd_per_1k < 0:
        raise ValueError("cached input price must be non-negative")
    cached_tokens = _first_number(usage, "cached_tokens") or 0
    cached_tokens = min(max(float(cached_tokens), 0.0), float(input_tokens))
    if cached_input_usd_per_1k is None:
        input_cost = float(input_tokens) / 1000.0 * input_usd_per_1k
    else:
        input_cost = (
            (float(input_tokens) - cached_tokens) / 1000.0 * input_usd_per_1k
            + cached_tokens / 1000.0 * cached_input_usd_per_1k
        )
    return round(
        input_cost + float(output_tokens) / 1000.0 * output_usd_per_1k,
        8,
    )


class OpenAICompatibleProvider:
    """Chat Completions adapter for OpenAI and compatible endpoints.

    The base_url argument is optional for OpenAI and should be set to the
    official compatible endpoint for another provider such as DeepSeek. Pricing
    is optional because the provider's published prices must be frozen in the
    run configuration before a budget gate can pass.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        name: str,
        base_url: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        reasoning_effort: str | None = None,
        input_usd_per_1k: float | None = None,
        cached_input_usd_per_1k: float | None = None,
        output_usd_per_1k: float | None = None,
        client: Any | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("provider API key is required")
        if not model.strip():
            raise ValueError("provider model is required")
        if not name.strip():
            raise ValueError("provider name is required")
        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if temperature < 0:
            raise ValueError("temperature must be non-negative")
        self.name = name.strip()
        self.model = model.strip()
        self.base_url = base_url.strip().rstrip("/") if base_url and base_url.strip() else None
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.reasoning_effort = reasoning_effort.strip() if reasoning_effort else None
        self._input_usd_per_1k = input_usd_per_1k
        self._cached_input_usd_per_1k = cached_input_usd_per_1k
        self._output_usd_per_1k = output_usd_per_1k
        self.last_call_metadata: dict[str, Any] = {}
        if client is None:
            from openai import OpenAI

            client_kwargs: dict[str, Any] = {"api_key": api_key}
            if self.base_url is not None:
                client_kwargs["base_url"] = self.base_url
            client = OpenAI(**client_kwargs)
        self._client = client

    def _response_metadata(self, response: Any) -> dict[str, Any]:
        usage = normalize_provider_usage(getattr(response, "usage", None))
        if not usage and isinstance(response, Mapping):
            usage = normalize_provider_usage(response.get("usage"))
        metadata: dict[str, Any] = {"usage": usage}
        response_model = getattr(response, "model", None)
        response_id = getattr(response, "id", None)
        if isinstance(response, Mapping):
            response_model = response.get("model", response_model)
            response_id = response.get("id", response_id)
        if response_model:
            metadata["response_model"] = str(response_model)
        if response_id:
            metadata["response_id"] = str(response_id)
        cost = estimate_provider_cost(
            usage,
            input_usd_per_1k=self._input_usd_per_1k,
            cached_input_usd_per_1k=self._cached_input_usd_per_1k,
            output_usd_per_1k=self._output_usd_per_1k,
        )
        if cost is not None:
            metadata["cost_usd"] = cost
        return metadata

    @staticmethod
    def _content(response: Any) -> str | None:
        choices = getattr(response, "choices", None)
        if choices is None and isinstance(response, Mapping):
            choices = response.get("choices")
        if not choices:
            return None
        choice = choices[0]
        message = getattr(choice, "message", None)
        if message is None and isinstance(choice, Mapping):
            message = choice.get("message")
        content = getattr(message, "content", None)
        if content is None and isinstance(message, Mapping):
            content = message.get("content")
        return str(content) if content is not None else None

    def complete(self, request: ProviderRequest) -> str:
        request_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if self.reasoning_effort is not None:
            request_kwargs["reasoning_effort"] = self.reasoning_effort
        response = self._client.chat.completions.create(**request_kwargs)
        self.last_call_metadata = self._response_metadata(response)
        content = self._content(response)
        if not content or not content.strip():
            raise ValueError(f"{self.name} response did not contain message content")
        return content

    def configuration_metadata(self) -> dict[str, Any]:
        """Return non-secret configuration facts suitable for a run manifest."""

        return {
            "adapter": "openai-chat-completions",
            "provider": self.name,
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "reasoning_effort": self.reasoning_effort,
            "input_pricing_configured": self._input_usd_per_1k is not None,
            "cached_input_pricing_configured": self._cached_input_usd_per_1k is not None,
            "output_pricing_configured": self._output_usd_per_1k is not None,
        }


class OpenAIProvider(OpenAICompatibleProvider):
    """OpenAI Chat Completions adapter, imported only for live runs."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        reasoning_effort: str | None = None,
        input_usd_per_1k: float | None = None,
        cached_input_usd_per_1k: float | None = None,
        output_usd_per_1k: float | None = None,
        client: Any | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            name="openai",
            base_url=base_url,
            max_tokens=max_tokens,
            temperature=temperature,
            reasoning_effort=reasoning_effort,
            input_usd_per_1k=input_usd_per_1k,
            cached_input_usd_per_1k=cached_input_usd_per_1k,
            output_usd_per_1k=output_usd_per_1k,
            client=client,
        )


class DeepSeekProvider(OpenAICompatibleProvider):
    """DeepSeek adapter using its documented OpenAI-compatible endpoint."""

    DEFAULT_BASE_URL = "https://api.deepseek.com"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        reasoning_effort: str | None = None,
        input_usd_per_1k: float | None = None,
        cached_input_usd_per_1k: float | None = None,
        output_usd_per_1k: float | None = None,
        client: Any | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            name="deepseek",
            base_url=base_url or self.DEFAULT_BASE_URL,
            max_tokens=max_tokens,
            temperature=temperature,
            reasoning_effort=reasoning_effort,
            input_usd_per_1k=input_usd_per_1k,
            cached_input_usd_per_1k=cached_input_usd_per_1k,
            output_usd_per_1k=output_usd_per_1k,
            client=client,
        )


class AnthropicProvider:
    """Anthropic Messages adapter, imported only for live runs."""

    name = "anthropic"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        max_tokens: int = 4096,
        input_usd_per_1k: float | None = None,
        output_usd_per_1k: float | None = None,
        client: Any | None = None,
    ) -> None:
        from anthropic import Anthropic

        if client is None:
            client = Anthropic(api_key=api_key)
        self._client = client
        self._model = model
        self._max_tokens = max_tokens
        self._input_usd_per_1k = input_usd_per_1k
        self._output_usd_per_1k = output_usd_per_1k
        self.last_call_metadata: dict[str, Any] = {}

    def complete(self, request: ProviderRequest) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[{"role": "user", "content": request.prompt}],
        )
        usage = normalize_provider_usage(getattr(response, "usage", None))
        metadata: dict[str, Any] = {"usage": usage}
        response_model = getattr(response, "model", None)
        if response_model:
            metadata["response_model"] = str(response_model)
        cost = estimate_provider_cost(
            usage,
            input_usd_per_1k=self._input_usd_per_1k,
            output_usd_per_1k=self._output_usd_per_1k,
        )
        if cost is not None:
            metadata["cost_usd"] = cost
        self.last_call_metadata = metadata
        content = getattr(response, "content", None)
        if not content:
            raise ValueError("Anthropic response did not contain message content")
        text = getattr(content[0], "text", None)
        if not text:
            raise ValueError("Anthropic response did not contain text content")
        return str(text)


class ReplayProvider:
    """Deterministic response queue for recorded or test completions."""

    name = "replay"

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.calls_made = 0

    def complete(self, request: ProviderRequest) -> str:
        if not self._responses:
            raise RuntimeError("ReplayProvider exhausted queued responses")
        self.calls_made += 1
        return self._responses.pop(0)


class MockProvider:
    """Adapter for the existing prompt-only offline transport seam."""

    name = "mock"

    def __init__(self, transport: Any) -> None:
        self._transport = transport

    def complete(self, request: ProviderRequest) -> str:
        return self._transport.complete(request.prompt)


class StubProvider:
    """Offline provider that serializes artifacts from the deterministic stub agent."""

    name = "stub"

    def __init__(self, stub_agent: StubAgent | None = None) -> None:
        self._agent = stub_agent or StubAgent()

    def complete(self, request: ProviderRequest) -> str:
        artifact = self._agent.generate(
            request.pair,
            variant=request.variant,
            task_family=request.task_family,
        )
        return json.dumps(artifact)
