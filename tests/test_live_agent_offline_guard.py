from __future__ import annotations

import json

import pytest

from agents.live import LiveAgent, NotConfiguredError
from agents.providers import ProviderRequest, StubProvider
from pairs.loader import load_all_pairs


def test_live_agent_raises_not_configured_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AGENT_LIVE_API_KEY", raising=False)

    with pytest.raises(NotConfiguredError) as exc_info:
        LiveAgent()

    message = str(exc_info.value).lower()
    assert "api key" in message or "openai" in message


def test_stub_provider_generates_without_openai_or_credentials(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AGENT_LIVE_API_KEY", raising=False)
    pair = next(pair for pair in load_all_pairs() if pair["intent_id"] == "RF-09")

    response = StubProvider().complete(
        ProviderRequest(
            prompt="offline fixture",
            pair=pair,
            variant="clean",
            task_family="codegen",
        )
    )

    assert json.loads(response) == pair["oracle_spec"]["codegen"]
