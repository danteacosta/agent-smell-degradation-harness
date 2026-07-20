"""Tier 2 offline acceptance criteria (C1, C4, analysis, live guard, Tier 1 regression)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from agents.live import LiveAgent, NotConfiguredError
from baselines.compare import compare_baselines
from eval.analysis_report import build_analysis_report
from eval.runner import run_eval
from gates.run import check_gate, load_thresholds

ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = load_thresholds(ROOT / "eval" / "thresholds.yaml")

TIER1_KEYS = {
    "paired_degradation_rate",
    "oracle_pass_rate_clean",
    "oracle_pass_rate_smelly",
    "semantic_provenance_coverage",
    "degradation_detected",
    "episode_count",
    "task_families_exercised",
}


def _load_episodes(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_tier2_taxonomy_labels_on_episodes(tmp_path):
    episodes_path = tmp_path / "episodes.jsonl"
    run_eval(
        failure_mode="smell-blind",
        output_path=tmp_path / "metrics.json",
        traces_dir=tmp_path / "traces",
        episodes_path=episodes_path,
    )

    episodes = _load_episodes(episodes_path)
    assert episodes
    for episode in episodes:
        assert "degradation_mode" in episode
        assert "degradation_severity" in episode
        assert "smell" in episode
        assert "requirement_text" in episode

    smelly_failed = [
        ep for ep in episodes if ep["variant"] == "smelly" and not ep["oracle_passed"]
    ]
    assert smelly_failed
    assert all(ep["degradation_mode"] != "none" for ep in smelly_failed)


def test_tier2_compare_baselines_on_smell_blind(tmp_path):
    episodes_path = tmp_path / "episodes.jsonl"
    run_eval(
        failure_mode="smell-blind",
        output_path=tmp_path / "metrics.json",
        traces_dir=tmp_path / "traces",
        episodes_path=episodes_path,
    )

    report = compare_baselines(_load_episodes(episodes_path))
    for family in ("static_smell", "output_only", "operational", "provenance_semantic"):
        assert "auroc" in report[family]
    assert report["provenance_semantic"]["auroc"] >= report["operational"]["auroc"] - 1e-9


def test_tier2_analysis_report_effect_and_observability(tmp_path):
    report = build_analysis_report(tmp_path / "work")

    assert report["effect_detected"] is True
    assert report["smell_blind"]["paired_degradation_rate"] > 0.0
    assert report["happy"]["paired_degradation_rate"] == 0.0
    assert report["observability_gate_passed"] is True
    assert report["paired_stats"]["proportion_diff"] > 0.0


def test_tier2_live_agent_not_configured_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AGENT_LIVE_API_KEY", raising=False)

    with pytest.raises(NotConfiguredError):
        LiveAgent()


def test_tier2_make_all_still_passes_and_gate_keys_intact():
    python = ROOT / ".venv" / "bin" / "python"

    for module in ("eval", "eval.simulate_regressions", "gates"):
        result = subprocess.run(
            [str(python), "-m", module],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"{module}: {result.stdout}{result.stderr}"

    last_run = json.loads((ROOT / "eval" / "last_run.json").read_text(encoding="utf-8"))
    assert TIER1_KEYS.issubset(last_run.keys())

    ok, failures = check_gate(last_run, THRESHOLDS)
    assert ok is True, failures
