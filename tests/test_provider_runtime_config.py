from __future__ import annotations

import json
from pathlib import Path

import pytest

import eval.provider_runtime_config as runtime_config
from eval.protocol_hashes import (
    build_protocol_hashes,
    sha256_text,
    verify_protocol_hashes,
)
from eval.provider_runtime_config import (
    ProviderRuntimeConfigError,
    load_exploratory_runtime_config,
    parse_provider_slot,
    resolve_provider_spec,
    validate_measured_token_fit,
)


ROOT = Path(__file__).resolve().parents[1]


def _slot(kind: str, model: str, version: str, key_env: str) -> dict[str, object]:
    return {
        "id": kind,
        "kind": kind,
        "api_key_env": key_env,
        "model": model,
        "model_version": version,
        "pricing_snapshot_date": "2026-09-02",
        "pricing_source_ref": "docs/research/2026-09-02-native-provider-smoke-model-selection.md",
        "pricing": {
            "input_usd_per_1k": "0.001",
            "cached_input_usd_per_1k": "0.0001",
            "output_usd_per_1k": "0.002",
        },
    }


def test_explicit_model_versions_and_pricing_are_secret_free() -> None:
    openai = parse_provider_slot(
        {
            **_slot("openai", "gpt-5.6-luna", "gpt-5.6-luna", "PANEL_OPENAI_API_KEY"),
            "temperature": None,
        }
    )
    deepseek = parse_provider_slot(
        {
            **_slot(
                "deepseek",
                "deepseek-v4-pro",
                "DeepSeek-V4-Pro-0813",
                "PANEL_DEEPSEEK_API_KEY",
            ),
            "base_url": "https://api.deepseek.com",
            "temperature": 0.0,
        }
    )

    assert openai.model == "gpt-5.6-luna"
    assert openai.model_version == "gpt-5.6-luna"
    assert deepseek.model == "deepseek-v4-pro"
    assert deepseek.model_version == "DeepSeek-V4-Pro-0813"
    assert openai.public_metadata()["api_key_env"] == "PANEL_OPENAI_API_KEY"
    assert deepseek.public_metadata()["api_key_env"] == "PANEL_DEEPSEEK_API_KEY"
    metadata = openai.public_metadata()
    assert "api_key" not in metadata
    assert metadata["api_key_env"] == "PANEL_OPENAI_API_KEY"


def test_missing_key_is_rejected_before_provider_constructor(monkeypatch) -> None:
    constructed = []

    class UnexpectedProviderConstruction:
        def __init__(self, **_kwargs):
            constructed.append(True)

    monkeypatch.setattr(runtime_config, "OpenAIProvider", UnexpectedProviderConstruction)
    spec = _slot("openai", "gpt-5.6-luna", "gpt-5.6-luna", "PANEL_OPENAI_API_KEY")
    with pytest.raises(ProviderRuntimeConfigError, match="PANEL_OPENAI_API_KEY") as error:
        resolve_provider_spec(spec, environ={}, client=object())
    assert constructed == []
    assert "secret-value" not in str(error.value)


def test_provider_construction_uses_explicit_identity_and_never_exports_key() -> None:
    secret = "secret-value-never-in-metadata"
    provider, metadata = resolve_provider_spec(
        {
            **_slot("openai", "gpt-5.6-luna", "gpt-5.6-luna", "PANEL_OPENAI_API_KEY"),
            "temperature": None,
        },
        environ={"PANEL_OPENAI_API_KEY": secret},
        client=object(),
    )
    serialized = json.dumps(metadata, sort_keys=True)
    assert provider.model == "gpt-5.6-luna"
    assert provider.configuration_metadata()["temperature"] is None
    assert secret not in serialized
    assert secret not in repr(provider)


def test_example_config_has_frozen_budget_and_two_distinct_snapshots(tmp_path) -> None:
    payload = json.loads(
        (ROOT / "tasks/exploratory_llm_judged_prepilot.example.json").read_text(
            encoding="utf-8"
        )
    )
    payload["source_revision"] = "a" * 40
    payload["protocol_hashes"] = build_protocol_hashes(ROOT)
    path = tmp_path / "runtime.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    configuration = load_exploratory_runtime_config(path)
    preflight = configuration.cost_configuration().preflight()

    assert {slot.kind for slot in configuration.providers} == {"openai", "deepseek"}
    assert preflight.passed is True
    assert preflight.direct_expected_cost_microusd == 439200
    assert preflight.retry_inclusive_worst_case_microusd == 878400
    assert preflight.contingency_reserve_microusd == 109800
    assert preflight.worst_case_reserved_microusd == 988200
    assert preflight.unused_headroom_microusd == 11800


def test_protocol_hashes_normalize_newlines_and_reject_drift(tmp_path) -> None:
    assert sha256_text("alpha\r\nbeta\r") == sha256_text("alpha\nbeta\n")
    expected = build_protocol_hashes(ROOT)
    assert verify_protocol_hashes(expected, repository_root=ROOT) == expected
    drifted = dict(expected)
    drifted["rubric_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="rubric_sha256"):
        verify_protocol_hashes(drifted, repository_root=ROOT)


def test_measured_prompt_and_schema_tokens_must_fit_each_phase() -> None:
    from eval.exploratory_cost import TokenBounds

    token_bounds = {
        "generation.T1": TokenBounds(192, 128),
        "generation.T2": TokenBounds(192, 64),
        "generation.artifact": TokenBounds(192, 48),
        "judge": TokenBounds(128, 64),
    }
    measurements = {
        phase: {"input_tokens": bound.input_tokens, "output_tokens": bound.output_tokens}
        for phase, bound in token_bounds.items()
    }
    validate_measured_token_fit(measurements, token_bounds)
    measurements["judge"]["output_tokens"] = 65
    with pytest.raises(ProviderRuntimeConfigError, match="judge"):
        validate_measured_token_fit(measurements, token_bounds)
