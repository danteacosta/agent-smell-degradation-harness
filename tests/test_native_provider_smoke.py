from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from agents.providers import ReplayProvider
from agents.runtime import RuntimeCheckpointAgent
from eval.native_provider_smoke import (
    NativeSmokeConfigurationError,
    load_smoke_config,
    run_native_provider_smoke,
    summarize_execution,
)


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
