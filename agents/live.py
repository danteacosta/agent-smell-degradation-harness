from __future__ import annotations

import json
import hashlib
import os
import re
import time
from typing import Any, Protocol

from agents.providers import MockProvider, OpenAIProvider, Provider, ProviderRequest


class NotConfiguredError(Exception):
    """Raised when live LLM adapter dependencies or credentials are missing."""


class Transport(Protocol):
    def complete(self, prompt: str) -> str: ...


def _resolve_api_key() -> str | None:
    return os.environ.get("AGENT_LIVE_API_KEY") or os.environ.get("OPENAI_API_KEY")


def _openai_available() -> bool:
    try:
        import openai  # noqa: F401

        return True
    except ImportError:
        return False


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("Response JSON must be an object")
    return parsed


def _build_prompt(pair: dict[str, Any], variant: str, task_family: str) -> str:
    requirement = (
        pair["clean_requirement"] if variant == "clean" else pair["smelly_requirement"]
    )
    oracle_keys = list(pair["oracle_spec"][task_family].keys())
    return (
        f"Task family: {task_family}\n"
        f"Variant: {variant}\n"
        f"Requirement:\n{requirement}\n\n"
        f"Respond with a single JSON object containing exactly these keys: {oracle_keys}\n"
        "Do not include markdown or commentary."
    )


def _build_checkpoint_prompt(pair: dict[str, Any], variant: str, task_family: str) -> str:
    requirement = (
        pair["clean_requirement"] if variant == "clean" else pair["smelly_requirement"]
    )
    return (
        "You are producing pre-final observability only. Do not produce an artifact, "
        "oracle verdict, label, smell name, or variant classification.\n"
        f"Task family: {task_family}\nRequirement:\n{requirement}\n\n"
        "Return one JSON object with exactly these sections and fields: "
        "interpretation={constraints:list, quantities:list, unresolved_references:list, "
        "assumptions:list, contradictions:list}; "
        "plan={validation_checks:list, planned_tools:list, coverage_targets:list}; "
        "execution={revisions:integer, validation_attempts:integer, errors:list, retrieval_events:integer}."
    )
class LiveAgent:
    """Optional live LLM adapter; requires `[live]` extra and an API key unless transport is injected."""

    MAX_PARSE_RETRIES = 2

    def __init__(
        self,
        *,
        transport: Transport | None = None,
        model: str = "gpt-4o-mini",
        provider: Provider | str | None = "openai",
        require_creds: bool = True,
    ) -> None:
        self.model = model
        if isinstance(provider, str) and provider != "openai":
            raise ValueError(
                "Provider instances are required for non-OpenAI providers; "
                "pass ReplayProvider, MockProvider, or StubProvider instead"
            )

        provider_label = provider if isinstance(provider, str) else None
        selected_provider = provider if not isinstance(provider, str) else None

        if selected_provider is not None and transport is not None:
            raise ValueError("Provide either a provider or a transport, not both")
        if selected_provider is None and transport is not None:
            selected_provider = MockProvider(transport)
            # The prompt-only transport is the legacy OpenAI injection seam.
            # Preserve its historical metadata unless a provider object is explicit.
            provider_label = "openai"
        if selected_provider is None:
            if require_creds:
                if not _openai_available():
                    raise NotConfiguredError(
                        "openai package not installed; install with pip install -e '.[live]'"
                    )
                api_key = _resolve_api_key()
                if not api_key:
                    raise NotConfiguredError(
                        "Missing API key; set OPENAI_API_KEY or AGENT_LIVE_API_KEY"
                    )
            else:
                api_key = _resolve_api_key()
                if not api_key:
                    raise NotConfiguredError("OpenAIProvider requires an API key")
            selected_provider = OpenAIProvider(api_key=api_key, model=model)

        self._provider = selected_provider
        self.provider = provider_label or selected_provider.name
        provider_name = str(selected_provider.name)
        # Keep offline replay/mock transports distinguishable from a network
        # provider in the exported run manifest, even when the legacy
        # prompt-only transport retains the ``openai`` provider label.
        if transport is not None:
            self.run_mode = "mock"
        elif provider_name in {"replay", "mock"}:
            self.run_mode = provider_name
        else:
            self.run_mode = "live"
        self.model_version = self.model

    def _complete(self, request: ProviderRequest) -> tuple[str, float]:
        start = time.perf_counter()
        response = self._provider.complete(request)
        latency_ms = (time.perf_counter() - start) * 1000.0
        return response, latency_ms

    def generate_with_meta(
        self,
        pair: dict[str, Any],
        variant: str,
        task_family: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        prompt = _build_prompt(pair, variant, task_family)
        parse_retries = 0
        last_error: Exception | None = None
        total_latency_ms = 0.0

        for attempt in range(self.MAX_PARSE_RETRIES + 1):
            response, latency_ms = self._complete(
                ProviderRequest(
                    prompt=prompt,
                    pair=pair,
                    variant=variant,
                    task_family=task_family,
                )
            )
            total_latency_ms += latency_ms
            try:
                artifact = _extract_json(response)
                meta = {
                    "latency_ms": round(total_latency_ms, 3),
                    "parse_retries": parse_retries,
                    "model": self.model,
                    "provider": self.provider,
                }
                return artifact, meta
            except (json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                if attempt < self.MAX_PARSE_RETRIES:
                    parse_retries += 1
                    continue
                break

        raise ValueError(
            f"Failed to parse JSON from transport after {self.MAX_PARSE_RETRIES} retries: {last_error}"
        )

    def observe_checkpoints(
        self,
        pair: dict[str, Any],
        *,
        variant: str,
        task_family: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Ask the provider for a pre-final checkpoint summary before generation."""

        prompt = _build_checkpoint_prompt(pair, variant, task_family)
        response, latency_ms = self._complete(
            ProviderRequest(
                prompt=prompt,
                pair=pair,
                variant=variant,
                task_family=task_family,
            )
        )
        payload = _extract_json(response)
        from agents.checkpoints import validate_checkpoint_payload

        normalized = validate_checkpoint_payload(payload)
        return normalized, {
            "checkpoint_schema": "pre-final/v1",
            "checkpoint_request_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "checkpoint_response_sha256": hashlib.sha256(response.encode("utf-8")).hexdigest(),
            "checkpoint_latency_ms": round(latency_ms, 3),
        }

    def generate(self, pair: dict[str, Any], variant: str, task_family: str) -> dict[str, Any]:
        artifact, _meta = self.generate_with_meta(pair, variant, task_family)
        return artifact
