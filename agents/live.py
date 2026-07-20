from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Protocol


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


class LiveAgent:
    """Optional live LLM adapter; requires `[live]` extra and an API key unless transport is injected."""

    MAX_PARSE_RETRIES = 2

    def __init__(
        self,
        *,
        transport: Transport | None = None,
        model: str = "gpt-4o-mini",
        provider: str = "openai",
        require_creds: bool = True,
    ) -> None:
        self.model = model
        self.provider = provider
        self._transport = transport

        if transport is not None:
            return

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
            self._api_key = api_key

    def _complete(self, prompt: str) -> tuple[str, float]:
        start = time.perf_counter()
        if self._transport is not None:
            response = self._transport.complete(prompt)
        else:
            raise NotConfiguredError(
                "LiveAgent.generate requires an injected transport or live API wiring"
            )
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
            response, latency_ms = self._complete(prompt)
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

    def generate(self, pair: dict[str, Any], variant: str, task_family: str) -> dict[str, Any]:
        artifact, _meta = self.generate_with_meta(pair, variant, task_family)
        return artifact
