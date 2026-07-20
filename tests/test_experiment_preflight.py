from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from eval.experiment import run_experiment


def _repo_with_pairs(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    eval_dir = repo / "eval"
    eval_dir.mkdir(parents=True)
    pairs_src = Path(__file__).resolve().parents[1] / "data" / "pairs"
    pairs_dst = repo / "data" / "pairs"
    pairs_dst.mkdir(parents=True)
    for path in pairs_src.glob("*.json"):
        (pairs_dst / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return repo


def test_dry_run_writes_manifest_and_prompts(tmp_path):
    repo = _repo_with_pairs(tmp_path)
    report = run_experiment(dry_run=True, repo_root=repo)

    run_dir = repo / "runs" / report["run_id"]
    manifest_path = run_dir / "manifest.json"
    prompts_dir = run_dir / "prompts"

    assert manifest_path.is_file()
    assert prompts_dir.is_dir()
    prompt_files = list(prompts_dir.glob("*.txt"))
    assert len(prompt_files) >= 24

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "git_sha" in manifest
    assert "pairs_hash" in manifest
    assert "timestamp" in manifest
    assert manifest["config"]["mode"] == "dry-run"


def test_dry_run_cli_exits_zero(tmp_path):
    repo = _repo_with_pairs(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "eval.experiment", "--dry-run"],
        cwd=repo,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1])},
    )
    assert result.returncode == 0
    runs = list((repo / "runs").glob("*"))
    assert runs


def test_mock_live_writes_runs_layout(tmp_path):
    repo = _repo_with_pairs(tmp_path)
    report = run_experiment(mock_live=True, repo_root=repo)

    run_dir = repo / "runs" / report["run_id"]
    assert (run_dir / "manifest.json").is_file()
    assert (run_dir / "metrics.json").is_file()
    assert (run_dir / "episodes.jsonl").is_file()
    assert report["mode"] == "mock-live"


def test_stub_as_live_still_writes_eval_artifacts(tmp_path):
    repo = tmp_path / "repo"
    eval_dir = repo / "eval"
    eval_dir.mkdir(parents=True)

    report = run_experiment(stub_as_live=True, repo_root=repo)

    assert (eval_dir / "experiment_run.json").is_file()
    assert report["mode"] == "stub-as-live"


def test_dry_run_makes_no_api_calls(tmp_path, monkeypatch):
    repo = _repo_with_pairs(tmp_path)

    def _forbidden(*_args, **_kwargs):
        raise AssertionError("API call attempted during dry-run")

    monkeypatch.setattr("agents.live.LiveAgent.generate", _forbidden)
    run_experiment(dry_run=True, repo_root=repo)
