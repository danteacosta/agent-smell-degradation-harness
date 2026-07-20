import json
from pathlib import Path

from eval.analysis_report import build_analysis_report, write_analysis_report


def test_build_analysis_report_shape(tmp_path):
    report = build_analysis_report(tmp_path / "work")

    assert set(report) == {
        "happy",
        "smell_blind",
        "effect_detected",
        "baselines",
        "observability_gate_passed",
        "paired_stats",
    }

    assert report["happy"]["paired_degradation_rate"] == 0.0
    assert report["smell_blind"]["paired_degradation_rate"] > 0.0
    assert report["effect_detected"] is True

    for family in ("static_smell", "output_only", "operational", "provenance_semantic"):
        assert "auroc" in report["baselines"][family]

    assert report["observability_gate_passed"] is True
    assert report["paired_stats"]["proportion_diff"] > 0.0
    assert "proportion_diff_ci" in report["paired_stats"]


def test_write_analysis_report_creates_json(tmp_path):
    output_path = tmp_path / "analysis_report.json"
    report = write_analysis_report(tmp_path / "work", output_path)

    assert output_path.exists()
    written = json.loads(output_path.read_text())
    assert written == report
    assert written["effect_detected"] is True


def test_analysis_report_does_not_touch_last_run(tmp_path):
    repo_eval = tmp_path / "eval"
    repo_eval.mkdir()
    last_run = repo_eval / "last_run.json"
    sentinel = {"sentinel": "keep-me", "episode_count": 42}
    last_run.write_text(json.dumps(sentinel), encoding="utf-8")

    write_analysis_report(tmp_path / "work", repo_eval / "analysis_report.json")

    assert json.loads(last_run.read_text()) == sentinel
