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
