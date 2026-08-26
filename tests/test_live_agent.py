from __future__ import annotations

import json
import re
import sys
from types import SimpleNamespace

import pytest

from agents.live import LiveAgent, NotConfiguredError, _build_prompt
from agents.mock_transport import MockTransport
from agents.providers import AnthropicProvider, MockProvider, ReplayProvider
from pairs.loader import load_all_pairs


def _rf09_pair() -> dict:
    return next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")


def test_live_agent_without_transport_raises_not_configured(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AGENT_LIVE_API_KEY", raising=False)
    with pytest.raises(NotConfiguredError):
        LiveAgent()


def test_mock_transport_generates_parseable_artifact():
    pair = _rf09_pair()
    oracle = pair["oracle_spec"]["codegen"]
    response = json.dumps({**oracle, "extra_field": "ignored"})
    transport = MockTransport([response])
    agent = LiveAgent(provider=MockProvider(transport), model="mock-model")

    artifact = agent.generate(pair, variant="clean", task_family="codegen")

    assert artifact["delay_threshold_minutes"] == 5
    assert artifact["comparator"] == ">"


def test_explicit_mock_provider_records_mock_metadata():
    pair = _rf09_pair()
    oracle = pair["oracle_spec"]["codegen"]
    agent = LiveAgent(provider=MockProvider(MockTransport([json.dumps(oracle)])))

    _artifact, meta = agent.generate_with_meta(pair, variant="clean", task_family="codegen")

    assert meta["provider"] == "mock"


def test_generate_with_meta_returns_expected_keys():
    pair = _rf09_pair()
    oracle = pair["oracle_spec"]["codegen"]
    transport = MockTransport([json.dumps(oracle)])
    agent = LiveAgent(transport=transport)

    artifact, meta = agent.generate_with_meta(pair, variant="clean", task_family="codegen")

    assert artifact == oracle
    assert set(meta.keys()) == {
        "latency_ms",
        "parse_retries",
        "model",
        "provider",
        "prompt_sha256",
        "prompt_template_version",
    }
    assert meta["parse_retries"] == 0
    assert meta["model"] == "gpt-4o-mini"
    assert meta["provider"] == "openai"
    assert re.fullmatch(r"[0-9a-f]{64}", meta["prompt_sha256"])
    assert meta["prompt_template_version"] == "discovery-generation/v1"
    assert "prompt" not in meta


def test_generation_prompt_does_not_disclose_variant_or_oracle_values():
    pair = _rf09_pair()

    prompt = _build_prompt(pair, variant="smelly", task_family="codegen")

    assert "Variant:" not in prompt
    assert "smelly" not in prompt.lower()
    assert str(pair["oracle_spec"]["codegen"]["delay_threshold_minutes"]) not in prompt
    for output_key in pair["generation_contract"]["codegen"]["output_keys"]:
        assert output_key in prompt


def test_retries_on_json_parse_failure():
    pair = _rf09_pair()
    oracle = pair["oracle_spec"]["codegen"]
    transport = MockTransport(["not json", "still bad", json.dumps(oracle)])
    agent = LiveAgent(transport=transport)

    artifact, meta = agent.generate_with_meta(pair, variant="clean", task_family="codegen")

    assert artifact == oracle
    assert meta["parse_retries"] == 2


def test_raises_after_max_retries_exhausted():
    pair = _rf09_pair()
    transport = MockTransport(["bad"] * 3)
    agent = LiveAgent(transport=transport)

    with pytest.raises(ValueError, match="JSON"):
        agent.generate(pair, variant="clean", task_family="codegen")


def test_works_without_openai_package(monkeypatch):
    """LiveAgent with MockTransport must not import openai."""
    pair = _rf09_pair()
    oracle = pair["oracle_spec"]["codegen"]

    def _block_openai(*_args, **_kwargs):
        raise ImportError("openai blocked for test")

    monkeypatch.setitem(__import__("sys").modules, "openai", None)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    transport = MockTransport([json.dumps(oracle)])
    agent = LiveAgent(transport=transport)
    artifact = agent.generate(pair, variant="clean", task_family="codegen")
    assert artifact["delay_threshold_minutes"] == 5


def test_replay_provider_is_used_for_live_agent_calls():
    pair = _rf09_pair()
    oracle = pair["oracle_spec"]["codegen"]
    provider = ReplayProvider([json.dumps(oracle)])
    agent = LiveAgent(provider=provider, model="replay-model")

    artifact, meta = agent.generate_with_meta(pair, variant="clean", task_family="codegen")

    assert artifact == oracle
    assert provider.calls_made == 1
    assert meta["provider"] == "replay"


def test_named_unconfigured_provider_is_rejected_without_openai_fallback():
    with pytest.raises(ValueError, match="Provider instances"):
        LiveAgent(provider="replay")


def test_real_provider_can_be_promoted_to_confirmatory_runtime():
    class FakeLiveProvider:
        name = "openai"

        def complete(self, request):
            raise AssertionError("not called while constructing runtime")

    agent = LiveAgent(provider=FakeLiveProvider(), model="provider-model")
    runtime = agent.as_runtime_checkpoint_agent()
    assert runtime.run_mode == "runtime"
    assert runtime.checkpoint_provenance == "runtime_native"
    assert runtime.model == "provider-model"


def test_replay_provider_cannot_be_promoted_to_confirmatory_runtime():
    agent = LiveAgent(provider=ReplayProvider([]), model="replay-model")
    with pytest.raises(ValueError, match="real live provider"):
        agent.as_runtime_checkpoint_agent()


def test_default_live_agent_routes_completion_to_openai(monkeypatch):
    pair = _rf09_pair()
    oracle = pair["oracle_spec"]["codegen"]
    calls = []

    class FakeOpenAI:
        def __init__(self, *, api_key):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=self.create),
            )

        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(oracle)))],
            )

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    artifact = LiveAgent(model="test-model").generate(
        pair,
        variant="clean",
        task_family="codegen",
    )

    assert artifact == oracle
    assert len(calls) == 1
    assert calls[0]["model"] == "test-model"
    assert calls[0]["messages"][0]["role"] == "user"
    assert "Task family: codegen" in calls[0]["messages"][0]["content"]


def test_anthropic_provider_routes_completion_without_openai_fallback(monkeypatch):
    pair = _rf09_pair()
    oracle = pair["oracle_spec"]["codegen"]
    calls = []

    class FakeAnthropic:
        def __init__(self, *, api_key):
            self.messages = SimpleNamespace(create=self.create)

        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                content=[SimpleNamespace(text=json.dumps(oracle))],
            )

    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=FakeAnthropic))
    provider = AnthropicProvider(api_key="test-key", model="claude-test")
    response = provider.complete(
        __import__("agents.providers", fromlist=["ProviderRequest"]).ProviderRequest(
            prompt="return json",
            pair=pair,
            variant="clean",
            task_family="codegen",
        )
    )

    assert json.loads(response) == oracle
    assert calls[0]["model"] == "claude-test"


def test_named_anthropic_provider_is_constructed_from_anthropic_credentials(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "anthropic",
        SimpleNamespace(Anthropic=lambda **_kwargs: SimpleNamespace(messages=None)),
    )
    monkeypatch.setenv("AGENT_LIVE_API_KEY", "test-key")
    agent = LiveAgent(provider="anthropic", model="claude-test")
    assert agent.provider == "anthropic"
    assert agent.run_mode == "live"
