from __future__ import annotations

import pytest

from eval.provider_manifest import ProviderRunMetadata, summarize_provider_runs
from eval.runner import run_eval_with_agent


def test_provider_metadata_distinguishes_stub_and_real_runs() -> None:
    stub = ProviderRunMetadata(
        run_id="run-stub",
        mode="stub",
        provider="deterministic-stub",
        model="stub-v1",
        model_version="1",
        seed=0,
        configuration_hash="cfg",
        episode_count=10,
        total_latency_ms=0.0,
        total_cost_usd=0.0,
    )
    live = ProviderRunMetadata(
        run_id="run-live",
        mode="live",
        provider="openai",
        model="gpt-test",
        model_version="2026-01",
        seed=7,
        configuration_hash="cfg-live",
        episode_count=10,
        total_latency_ms=123.4,
        total_cost_usd=0.12,
    )

    summary = summarize_provider_runs([stub, live])

    assert summary["runs"] == 2
    assert {item["mode"] for item in summary["metadata"]} == {"stub", "live"}
    assert summary["total_cost_usd"] == pytest.approx(0.12)


def test_provider_metadata_rejects_secret_like_fields() -> None:
    with pytest.raises(ValueError, match="secret"):
        ProviderRunMetadata(
            run_id="run",
            mode="live",
            provider="openai",
            model="gpt-test",
            model_version="1",
            seed=0,
            configuration_hash="cfg",
            episode_count=1,
            total_latency_ms=1.0,
            total_cost_usd=0.01,
            extra={"api_key": "must-not-export"},
        )


def test_runner_exports_provider_metadata_without_prompt_or_artifact(tmp_path) -> None:
    class FakeLiveAgent:
        provider = "replay"
        model = "recorded-model"

        def generate_with_meta(self, pair, variant, task_family):
            return pair["oracle_spec"][task_family], {
                "provider": self.provider,
                "model": self.model,
                "latency_ms": 12.5,
                "cost_usd": 0.01,
            }

    pair = {
        "intent_id": "I-1",
        "workload_id": "w-1",
        "clean_requirement": "Do the thing.",
        "smelly_requirement": "Do the thing.",
        "smell": {"type": "vague", "category": "ambiguity"},
        "oracle_spec": {"codegen": {"ok": True}, "test_gen": {"ok": True}},
    }
    metrics, episodes = run_eval_with_agent(
        FakeLiveAgent(),
        pairs=[pair],
        output_path=tmp_path / "metrics.json",
        traces_dir=tmp_path / "traces",
    )

    assert metrics["provider_run"]["metadata"][0]["mode"] == "live"
    assert episodes[0]["provider_meta"]["latency_ms"] == 12.5
    assert "prompt" not in metrics["provider_run"]
    assert "artifact" not in metrics["provider_run"]


def test_runner_propagates_non_secret_prompt_identity(tmp_path) -> None:
    class PromptAwareAgent:
        provider = "replay"
        model = "recorded-model"

        def generate_with_meta(self, pair, variant, task_family):
            return pair["oracle_spec"][task_family], {
                "provider": self.provider,
                "model": self.model,
                "latency_ms": 12.5,
                "cost_usd": 0.01,
                "prompt_sha256": "a" * 64,
                "prompt_template_version": "discovery-generation/v1",
            }

    pair = {
        "intent_id": "I-1",
        "workload_id": "w-1",
        "clean_requirement": "Do the thing.",
        "smelly_requirement": "Do the thing.",
        "smell": {"type": "vague", "category": "ambiguity"},
        "oracle_spec": {"codegen": {"ok": True}, "test_gen": {"ok": True}},
    }
    metrics, episodes = run_eval_with_agent(
        PromptAwareAgent(),
        pairs=[pair],
        output_path=tmp_path / "metrics.json",
        traces_dir=tmp_path / "traces",
    )

    assert episodes[0]["provider_meta"]["prompt_sha256"] == "a" * 64
    extra = metrics["provider_run"]["metadata"][0]["extra"]
    assert extra["prompt_template_versions"] == ["discovery-generation/v1"]
    assert extra["prompt_sha256s"] == ["a" * 64]


def _live(**overrides):
    base = dict(
        run_id="r", mode="live", provider="p", model="m", model_version="m-2026-10-01",
        seed=1, configuration_hash="a" * 64, episode_count=1, total_latency_ms=1.0,
        total_cost_usd=0.0, extra={"prompt_sha256s": ["b" * 64]},
    )
    base.update(overrides)
    return ProviderRunMetadata(**base)


def test_configuration_digest_changes_with_each_bound_component() -> None:
    from eval.provider_manifest import configuration_identity_digest

    args = dict(
        provider="p", model="m", model_version="v1", instructions_sha256="c" * 64,
        tool_definitions=[{"name": "a"}, {"name": "b"}], runtime_config={"temperature": 0.0},
    )
    base = configuration_identity_digest(**args)
    assert base == configuration_identity_digest(**{**args, "tool_definitions": [{"name": "b"}, {"name": "a"}]})
    for change in (
        {"model_version": "v2"},
        {"instructions_sha256": "d" * 64},
        {"tool_definitions": [{"name": "a"}]},
        {"runtime_config": {"temperature": 0.7}},
    ):
        assert configuration_identity_digest(**{**args, **change}) != base
    with pytest.raises(ValueError, match="SHA-256"):
        configuration_identity_digest(**{**args, "instructions_sha256": "short"})
    with pytest.raises(ValueError, match="secret"):
        configuration_identity_digest(**{**args, "runtime_config": {"api_key": "x"}})


def test_identity_binding_gaps_flag_unpinned_live_runs_only() -> None:
    from eval.provider_manifest import identity_binding_gaps

    assert identity_binding_gaps(_live()) == []
    gaps = identity_binding_gaps(_live(configuration_hash="cfg", model_version="m", extra={}))
    assert len(gaps) == 3
    assert identity_binding_gaps(_live(mode="stub", configuration_hash="cfg", model_version="m", extra={})) == []
