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
