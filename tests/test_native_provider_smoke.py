from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from agents.providers import ReplayProvider
from agents.runtime import RuntimeCheckpointAgent
from eval.native_provider_smoke import (
    NativeSmokeConfigurationError,
    load_smoke_config,
    run_native_provider_smoke,
    summarize_execution,
)
import eval.native_provider_smoke as native_smoke


def _pair() -> dict:
    return {
        "intent_id": "smoke-1",
        "clean_requirement": "Reject requests after 5 minutes.",
        "smelly_requirement": "Reject late requests.",
        "generation_contract": {
            "test_gen": {"output_keys": ["criterion"]},
        },
    }


def _responses() -> list[str]:
    return [
        json.dumps(
            {
                "constraints": ["reject requests after five minutes"],
                "quantities": ["five minutes"],
                "unresolved_references": [],
                "assumptions": [],
                "contradictions": [],
                "conditional_semantics": [
                    {
                        "antecedent": "a request exceeds five minutes",
                        "consequent": "the request is rejected",
                        "necessity_status": "sufficient_only",
                        "temporal_relation": "next_state",
                        "negative_case": {
                            "status": "specified",
                            "description": "the request is at or below five minutes",
                        },
                    }
                ],
                "atomic_obligations": [
                    {
                        "constraint_index": 1,
                        "atom_type": "condition",
                        "status": "present",
                    }
                ],
            }
        ),
        json.dumps(
            {
                "validation_checks": ["check boundary"],
                "planned_tools": ["contract validator"],
                "coverage_targets": ["reject requests after five minutes"],
            }
        ),
        json.dumps({"criterion": "reject after five minutes"}),
    ]


def test_native_smoke_summary_checks_no_compaction_and_timestamps() -> None:
    values = iter(
        datetime(2026, 9, 1, tzinfo=timezone.utc)
        + timedelta(milliseconds=index)
        for index in range(20)
    )
    execution = RuntimeCheckpointAgent.from_provider(
        ReplayProvider(_responses()),
        model="replay-model",
        model_version="fixture-v1",
        clock=lambda: next(values),
    ).execute_with_checkpoints(
        _pair(),
        variant="clean",
        task_family="test_gen",
    )

    summary = summarize_execution(
        execution,
        _pair(),
        task_family="test_gen",
        variant="clean",
    )

    assert summary["checkpoint_provenance"] == "runtime_native"
    assert summary["context_condition"] == "no_compaction"
    assert summary["compaction_count"] == 0
    assert summary["context_event_count"] == 3
    assert summary["artifact_shape_matches_contract"] is True
    assert summary["cost_status"] == "not_configured"


def test_smoke_config_requires_two_secret_free_provider_slots(tmp_path) -> None:
    config = tmp_path / "smoke.json"
    config.write_text(
        json.dumps(
            {
                "schema_version": "native-provider-smoke/v1",
                "providers": [
                    {
                        "id": "only",
                        "kind": "openai",
                        "api_key_env": "OPENAI_API_KEY",
                        "model_env": "MODEL",
                        "model_version_env": "MODEL_VERSION",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(NativeSmokeConfigurationError, match="at least two"):
        load_smoke_config(config)


def test_missing_private_keys_are_reported_without_writing_them(tmp_path) -> None:
    config = tmp_path / "smoke.json"
    output = tmp_path / "report.json"
    config.write_text(
        json.dumps(
            {
                "schema_version": "native-provider-smoke/v1",
                "task_family": "test_gen",
                "context_condition": "no_compaction",
                "providers": [
                    {
                        "id": "openai",
                        "kind": "openai",
                        "api_key_env": "OPENAI_API_KEY",
                        "model_env": "OPENAI_MODEL",
                        "model_version_env": "OPENAI_VERSION",
                    },
                    {
                        "id": "deepseek",
                        "kind": "deepseek",
                        "api_key_env": "DEEPSEEK_API_KEY",
                        "model_env": "DEEPSEEK_MODEL",
                        "model_version_env": "DEEPSEEK_VERSION",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    report = run_native_provider_smoke(
        config,
        output,
        environ={
            "OPENAI_MODEL": "gpt-test",
            "OPENAI_VERSION": "snapshot-a",
            "DEEPSEEK_MODEL": "deepseek-test",
            "DEEPSEEK_VERSION": "snapshot-b",
        },
    )

    serialized = output.read_text(encoding="utf-8")
    assert report["status"] == "fail"
    assert "api key" not in serialized.lower()
    assert "OPENAI_API_KEY" in serialized
    assert "DEEPSEEK_API_KEY" in serialized


def test_failed_provider_episode_preserves_observed_usage_and_cost(tmp_path, monkeypatch) -> None:
    config = tmp_path / "smoke.json"
    output = tmp_path / "report.json"
    config.write_text(
        json.dumps(
            {
                "schema_version": "native-provider-smoke/v1",
                "task_family": "test_gen",
                "context_condition": "no_compaction",
                "providers": [
                    {
                        "id": "openai",
                        "kind": "openai",
                        "api_key_env": "OPENAI_API_KEY",
                        "model_env": "OPENAI_MODEL",
                        "model_version_env": "OPENAI_VERSION",
                    },
                    {
                        "id": "deepseek",
                        "kind": "deepseek",
                        "api_key_env": "DEEPSEEK_API_KEY",
                        "model_env": "DEEPSEEK_MODEL",
                        "model_version_env": "DEEPSEEK_VERSION",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(native_smoke, "_selected_pairs", lambda **_: [_pair()])

    def fake_provider_from_spec(spec, *, environ):
        provider = SimpleNamespace(
            name=str(spec["kind"]),
            last_call_metadata={
                "usage": {"input_tokens": 7, "output_tokens": 3, "total_tokens": 10},
                "cost_usd": 0.0042,
            },
        )

        def complete(_request):
            raise ValueError("simulated provider response failure")

        provider.complete = complete
        return provider, {
            "id": str(spec["id"]),
            "kind": str(spec["kind"]),
            "model": "test-model",
            "model_version": "test-version",
            "base_url": None,
            "max_tokens": 4096,
            "temperature": 0.0,
            "reasoning_effort": None,
            "api_key_env": str(spec["api_key_env"]),
            "model_env": str(spec["model_env"]),
            "model_version_env": str(spec["model_version_env"]),
            "pricing_envs": {},
        }

    monkeypatch.setattr(native_smoke, "_provider_from_spec", fake_provider_from_spec)
    report = run_native_provider_smoke(
        config,
        output,
        environ={
            "OPENAI_API_KEY": "private-openai",
            "OPENAI_MODEL": "test-model",
            "OPENAI_VERSION": "test-version",
            "DEEPSEEK_API_KEY": "private-deepseek",
            "DEEPSEEK_MODEL": "test-model",
            "DEEPSEEK_VERSION": "test-version",
        },
    )

    assert report["status"] == "fail"
    for provider in report["providers"]:
        assert provider["total_usage"] == {
            "input_tokens": 14,
            "output_tokens": 6,
            "total_tokens": 20,
        }
        assert provider["total_cost_usd"] == pytest.approx(0.0084)
        assert provider["cost_status"] == "measured"
        assert provider["episodes"][0]["usage"] == {
            "input_tokens": 7,
            "output_tokens": 3,
            "total_tokens": 10,
        }
        assert provider["episodes"][0]["cost_usd"] == pytest.approx(0.0042)
