import sys
import types
import pytest
from agents.providers import OpenAIProvider, AnthropicProvider


@pytest.mark.parametrize("vendor", ["openai", "anthropic"])
def test_sdk_retries_are_disabled_and_transport_timeout_is_explicit(monkeypatch, vendor):
    captured = {}
    def constructor(**kwargs):
        captured.update(kwargs)
        return object()
    monkeypatch.setitem(sys.modules, vendor, types.SimpleNamespace(**{
        "OpenAI" if vendor == "openai" else "Anthropic": constructor}))
    cls = OpenAIProvider if vendor == "openai" else AnthropicProvider
    cls(api_key="test-only", model="test-model")
    assert captured["max_retries"] == 0
    assert captured["timeout"] == 60.0


@pytest.mark.parametrize("vendor", ["openai", "anthropic"])
def test_locked_real_sdk_constructor_accepts_production_limits(vendor, monkeypatch):
    import os
    import socket
    # Constructor-only direct-HTTPS profile; no network operation is permitted.
    for key in list(os.environ):
        if key.lower() in {"all_proxy", "http_proxy", "https_proxy"}:
            monkeypatch.delenv(key)
    def reject_network(*args, **kwargs):
        pytest.fail("constructor smoke must not connect to a network")
    monkeypatch.setattr(socket.socket, "connect", reject_network)
    pytest.importorskip(vendor)
    cls = OpenAIProvider if vendor == "openai" else AnthropicProvider
    provider = cls(api_key="offline-constructor-only", model="test-model")
    try:
        assert provider._client.max_retries == 0
        timeout = provider._client.timeout
        assert getattr(timeout, "read", timeout) == 60.0
    finally:
        provider._client.close()
