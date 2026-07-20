from __future__ import annotations

import json

import pytest

from agents.live import LiveAgent, NotConfiguredError
from agents.mock_transport import MockTransport
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
    agent = LiveAgent(transport=transport, model="mock-model", provider="mock")

    artifact = agent.generate(pair, variant="clean", task_family="codegen")

    assert artifact["delay_threshold_minutes"] == 5
    assert artifact["comparator"] == ">"


def test_generate_with_meta_returns_expected_keys():
    pair = _rf09_pair()
    oracle = pair["oracle_spec"]["codegen"]
    transport = MockTransport([json.dumps(oracle)])
    agent = LiveAgent(transport=transport)

    artifact, meta = agent.generate_with_meta(pair, variant="clean", task_family="codegen")

    assert artifact == oracle
    assert set(meta.keys()) == {"latency_ms", "parse_retries", "model", "provider"}
    assert meta["parse_retries"] == 0
    assert meta["model"] == "gpt-4o-mini"
    assert meta["provider"] == "openai"


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
