import json
from pathlib import Path

from eval.runner import run_eval
from gates.run import check_gate

THRESHOLDS = {
    "floors": {
        "oracle_pass_rate_clean": 1.0,
        "semantic_provenance_coverage": 1.0,
    },
    "ceilings": {
        "paired_degradation_rate": 0.0,
    },
    "require_degradation_detector": True,
}

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


def test_happy_path_clean_episodes_have_none_mode(tmp_path):
    output_path = tmp_path / "metrics.json"
    episodes_path = tmp_path / "episodes.jsonl"
    traces_dir = tmp_path / "traces"

    metrics, _ = run_eval(
        failure_mode=None,
        output_path=output_path,
        traces_dir=traces_dir,
        episodes_path=episodes_path,
    )

    episodes = _load_episodes(episodes_path)
    assert len(episodes) > 0

    clean_episodes = [ep for ep in episodes if ep["variant"] == "clean"]
    assert clean_episodes
    assert all(ep["degradation_mode"] == "none" for ep in clean_episodes)
    assert all(ep["smell"] is None for ep in clean_episodes)
    assert all(ep["requirement_text"] for ep in clean_episodes)
    assert all(ep["artifact"] for ep in clean_episodes)

    assert "taxonomy_modes" in metrics
    assert metrics["taxonomy_modes"]["none"] == len(episodes)


def test_smell_blind_episodes_have_taxonomy_modes(tmp_path):
    output_path = tmp_path / "metrics.json"
    episodes_path = tmp_path / "episodes.jsonl"
    traces_dir = tmp_path / "traces"

    metrics, _ = run_eval(
        failure_mode="smell-blind",
        output_path=output_path,
        traces_dir=traces_dir,
        episodes_path=episodes_path,
    )

    episodes = _load_episodes(episodes_path)
    smelly_failed = [
        ep for ep in episodes if ep["variant"] == "smelly" and not ep["oracle_passed"]
    ]
    assert smelly_failed

    modes = {ep["degradation_mode"] for ep in smelly_failed}
    assert "wrong_numeric_threshold" in modes
    assert "none" not in modes

    assert metrics["taxonomy_modes"]["none"] == len(
        [ep for ep in episodes if ep["variant"] == "clean"]
    )
    assert metrics["paired_degradation_rate"] > 0
    assert metrics["degradation_detected"] is True


def test_last_run_json_remains_gate_compatible(tmp_path):
    output_path = tmp_path / "last_run.json"
    traces_dir = tmp_path / "traces"

    metrics, _ = run_eval(
        failure_mode=None,
        output_path=output_path,
        traces_dir=traces_dir,
    )

    assert TIER1_KEYS.issubset(metrics.keys())

    written = json.loads(output_path.read_text())
    assert TIER1_KEYS.issubset(written.keys())

    passed, failures = check_gate(written, THRESHOLDS)
    assert passed is True
    assert failures == []
