"""Provider boundary for live and offline agent completions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from agents.stub import StubAgent


@dataclass(frozen=True)
class ProviderRequest:
    prompt: str
    pair: dict[str, Any]
    variant: str
    task_family: str


class Provider(Protocol):
    name: str

    def complete(self, request: ProviderRequest) -> str: ...


class OpenAIProvider:
    """OpenAI Chat Completions adapter, imported only for live runs."""

    name = "openai"

    def __init__(self, *, api_key: str, model: str) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def complete(self, request: ProviderRequest) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": request.prompt}],
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI response did not contain message content")
        return content


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
