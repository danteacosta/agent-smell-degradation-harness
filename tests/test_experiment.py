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
    experiment_episode = _load_episodes(eval_dir / "experiment_run_episodes.jsonl")[0]
    last_run_episode = _load_episodes(eval_dir / "last_run_episodes.jsonl")[0]
    assert experiment_episode["episode_id"] != last_run_episode["episode_id"]


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


def test_mock_live_executes_each_requested_replication_with_distinct_identity(tmp_path):
    repo = tmp_path / "repo"
    (repo / "eval").mkdir(parents=True)

    report = run_experiment(
        mock_live=True,
        replications=2,
        repo_root=repo,
        run_id="mock-identity",
    )

    episodes = _load_episodes(repo / "runs" / "mock-identity" / "episodes.jsonl")
    assert report["episode_count"] == len(episodes)
    assert {episode["replication_id"] for episode in episodes} == {0, 1}
    assert len({episode["episode_id"] for episode in episodes}) == len(episodes)


def test_live_experiment_routes_evaluation_through_live_agent(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "eval").mkdir(parents=True)
    captured = {}

    class FakeLiveAgent:
        def __init__(self, *, model):
            captured["model"] = model

    def fake_run_eval_with_agent(agent, **kwargs):
        captured["agent"] = agent
        captured["kwargs"] = kwargs
        return {"paired_degradation_rate": 0.0}, []

    monkeypatch.setattr("eval.experiment.LiveAgent", FakeLiveAgent)
    monkeypatch.setattr("eval.experiment.run_eval_with_agent", fake_run_eval_with_agent)
    monkeypatch.setattr(
        "eval.experiment.run_eval",
        lambda **_kwargs: pytest.fail("live experiment must not use StubAgent runner"),
    )

    report = run_experiment(repo_root=repo, model="provider-model")

    assert report["mode"] == "live"
    assert captured["model"] == "provider-model"
    assert isinstance(captured["agent"], FakeLiveAgent)
