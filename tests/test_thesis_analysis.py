from __future__ import annotations

import json
import pytest
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


def test_legacy_report_preserves_repetitions_and_marks_descriptive_scope():
    rows = [{"intent_id": "same", "task_family": "codegen", "run_id": "run",
             "replication_id": replication, "variant": variant,
             "oracle_passed": variant == "clean" or replication == 1}
            for replication in (0, 1) for variant in ("clean", "smelly")]
    report = analyze_episodes(rows)
    assert report["H1_paired_degradation"]["pair_count"] == 2
    assert report["H1_paired_degradation"]["paired_degradation_rate"] == 0.5
    assert report["confirmatory_eligible"] is False
    assert report["analysis_scope"] == "legacy_binary_descriptive_only"


def test_empty_or_incomplete_legacy_input_does_not_create_a_report(tmp_path):
    source, output = tmp_path / "episodes.jsonl", tmp_path / "report.json"
    for rows in ([], [{"intent_id": "x", "task_family": "codegen", "variant": "clean", "oracle_passed": True}]):
        source.write_text("\n".join(json.dumps(r) for r in rows))
        with pytest.raises(ValueError):
            write_thesis_analysis(source, output)
        assert not output.exists()
