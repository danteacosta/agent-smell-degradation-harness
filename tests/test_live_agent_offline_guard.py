from __future__ import annotations

import pytest

from agents.live import LiveAgent, NotConfiguredError


def test_live_agent_raises_not_configured_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AGENT_LIVE_API_KEY", raising=False)

    with pytest.raises(NotConfiguredError) as exc_info:
        LiveAgent()

    message = str(exc_info.value).lower()
    assert "api key" in message or "openai" in message
