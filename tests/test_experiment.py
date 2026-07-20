from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from eval.experiment import run_experiment


def _load_episodes(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_experiment_refuses_live_without_env(tmp_path, capsys):
    repo = tmp_path / "repo"
    (repo / "eval").mkdir(parents=True)
    (repo / "pairs").mkdir()

    result = subprocess.run(
        [sys.executable, "-m", "eval.experiment"],
        cwd=repo,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1])},
    )

    assert result.returncode == 0
    assert "stub-as-live" in result.stderr.lower() or "stub-as-live" in result.stdout.lower()


def test_stub_as_live_writes_experiment_artifacts(tmp_path):
    repo = tmp_path / "repo"
    eval_dir = repo / "eval"
    eval_dir.mkdir(parents=True)

    report = run_experiment(stub_as_live=True, repo_root=repo)

    experiment_run = eval_dir / "experiment_run.json"
    experiment_episodes = eval_dir / "experiment_run_episodes.jsonl"

    assert experiment_run.exists()
    assert experiment_episodes.exists()

    written = json.loads(experiment_run.read_text())
    assert written == report
    assert written["mode"] == "stub-as-live"
    assert written["replications"] == 1
    assert len(written["runs"]) == 1

    episodes = _load_episodes(experiment_episodes)
    assert episodes
    assert all(ep["replication_id"] == 0 for ep in episodes)
    assert all("degradation_mode" in ep for ep in episodes)


def test_experiment_does_not_touch_last_run_by_default(tmp_path):
    repo = tmp_path / "repo"
    eval_dir = repo / "eval"
    eval_dir.mkdir(parents=True)
    last_run = eval_dir / "last_run.json"
    sentinel = {"sentinel": "keep-me", "episode_count": 99}
    last_run.write_text(json.dumps(sentinel), encoding="utf-8")

    run_experiment(stub_as_live=True, repo_root=repo)

    assert json.loads(last_run.read_text()) == sentinel


def test_experiment_also_last_run_overwrites_when_requested(tmp_path):
    repo = tmp_path / "repo"
    eval_dir = repo / "eval"
    eval_dir.mkdir(parents=True)
    last_run = eval_dir / "last_run.json"
    last_run.write_text(json.dumps({"sentinel": "old"}), encoding="utf-8")

    run_experiment(stub_as_live=True, also_last_run=True, repo_root=repo)

    written = json.loads(last_run.read_text())
    assert "sentinel" not in written
    assert written["paired_degradation_rate"] == 0.0


def test_experiment_replications_add_replication_id(tmp_path):
    repo = tmp_path / "repo"
    eval_dir = repo / "eval"
    eval_dir.mkdir(parents=True)

    report = run_experiment(stub_as_live=True, replications=2, repo_root=repo)

    assert report["replications"] == 2
    assert len(report["runs"]) == 2

    episodes = _load_episodes(eval_dir / "experiment_run_episodes.jsonl")
    replication_ids = {ep["replication_id"] for ep in episodes}
    assert replication_ids == {0, 1}
