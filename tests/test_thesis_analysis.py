from __future__ import annotations

import json
from pathlib import Path

from eval.runner import run_eval
from eval.thesis_analysis import analyze_episodes, write_thesis_analysis


def test_analyze_stub_episodes_detects_smell_blind_effect(tmp_path):
    episodes_path = tmp_path / "episodes.jsonl"
    run_eval(
        failure_mode="smell-blind",
        output_path=tmp_path / "metrics.json",
        traces_dir=tmp_path / "traces",
        episodes_path=episodes_path,
    )

    report = analyze_episodes(
        [json.loads(line) for line in episodes_path.read_text().splitlines() if line.strip()]
    )

    assert report["H1_paired_degradation"]["effect_detected"] is True
    assert report["H1_paired_degradation"]["paired_degradation_rate"] > 0
    assert report["per_intent_table"]
    assert report["negative_boundary"] is False


def test_happy_path_negative_boundary(tmp_path):
    episodes_path = tmp_path / "episodes.jsonl"
    run_eval(
        output_path=tmp_path / "metrics.json",
        traces_dir=tmp_path / "traces",
        episodes_path=episodes_path,
    )

    report = write_thesis_analysis(episodes_path, tmp_path / "thesis_tables.json")

    assert report["H1_paired_degradation"]["paired_degradation_rate"] == 0.0
    assert report["negative_boundary"] is True
    assert (tmp_path / "thesis_tables.json").is_file()


def test_per_intent_table_has_rates():
    episodes = [
        {
            "intent_id": "RF-09",
            "task_family": "codegen",
            "variant": "clean",
            "oracle_passed": True,
        },
        {
            "intent_id": "RF-09",
            "task_family": "codegen",
            "variant": "smelly",
            "oracle_passed": False,
            "smell": {"type": "vague_threshold"},
        },
    ]
    report = analyze_episodes(episodes)
    row = report["per_intent_table"][0]
    assert row["intent_id"] == "RF-09"
    assert row["paired_delta"] == 1.0
