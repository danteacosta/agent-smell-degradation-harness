import json
from pathlib import Path

from baselines.compare import compare_baselines
from baselines.features import extract_features
from baselines.score import mann_whitney_auroc
from eval.runner import run_eval


def _load_episodes(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_mann_whitney_auroc_handles_ties_and_uniform_labels():
    assert mann_whitney_auroc([1.0, 2.0, 3.0], [0, 0, 0]) == 0.5
    assert mann_whitney_auroc([2.0, 1.0, 1.0, 0.0], [1, 1, 0, 0]) == 0.875


def test_extract_features_shape(tmp_path):
    episodes_path = tmp_path / "episodes.jsonl"
    traces_dir = tmp_path / "traces"
    run_eval(
        failure_mode="smell-blind",
        output_path=tmp_path / "metrics.json",
        traces_dir=traces_dir,
        episodes_path=episodes_path,
    )

    episode = _load_episodes(episodes_path)[0]
    feats = extract_features(episode, episode["provenance_path"])

    assert set(feats) == {
        "static_smell",
        "output_only",
        "operational",
        "provenance_semantic",
    }
    assert "smell_present" in feats["static_smell"]
    assert "oracle_passed" in feats["output_only"]
    assert feats["operational"]["event_count"] >= 1
    assert "constraint_match" in feats["provenance_semantic"]


def test_compare_baselines_ranks_provenance_on_smell_blind(tmp_path):
    episodes_path = tmp_path / "episodes.jsonl"
    traces_dir = tmp_path / "traces"
    run_eval(
        failure_mode="smell-blind",
        output_path=tmp_path / "metrics.json",
        traces_dir=traces_dir,
        episodes_path=episodes_path,
    )

    episodes = _load_episodes(episodes_path)
    report = compare_baselines(episodes)

    assert "auroc" in report["provenance_semantic"]
    assert "auroc" in report["operational"]
    assert (
        report["provenance_semantic"]["auroc"]
        >= report["operational"]["auroc"] - 1e-9
    )
