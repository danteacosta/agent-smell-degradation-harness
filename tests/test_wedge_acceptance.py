from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from eval.h2_detection import main as h2_main
from eval.runner import run_eval
from pairs.loader import load_all_pairs
from wedge.check import main as wedge_main
from wedge.decisions import Decision


def test_acceptance_tier_a_features_no_label_leakage(tmp_path: Path):
    episodes_path = tmp_path / "episodes.jsonl"
    traces_dir = tmp_path / "traces"
    run_eval(
        failure_mode="smell-blind",
        output_path=tmp_path / "metrics.json",
        traces_dir=traces_dir,
        episodes_path=episodes_path,
    )

    from observability.features import extract_tier_a_features

    for line in episodes_path.read_text().splitlines():
        if not line.strip():
            continue
        episode = json.loads(line)
        features = extract_tier_a_features(episode, episode["provenance_path"])
        blob = json.dumps(features)
        assert "oracle_passed" not in blob
        assert "oracle_verdict" not in blob


def test_acceptance_wedge_cli_fixtures():
    clean = subprocess.run(
        [sys.executable, "-m", "wedge", "--fixture", "demo-clean"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert clean.returncode == 0
    assert Decision.APPROVE.value in clean.stdout

    smelly = subprocess.run(
        [sys.executable, "-m", "wedge", "--fixture", "demo-smelly"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert smelly.returncode != 0
    assert Decision.CLARIFY.value in smelly.stdout


def test_acceptance_h2_module_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    episodes_path = tmp_path / "episodes.jsonl"
    traces_dir = tmp_path / "traces"
    run_eval(
        failure_mode="smell-blind",
        output_path=tmp_path / "metrics.json",
        traces_dir=traces_dir,
        episodes_path=episodes_path,
    )
    assert h2_main(["--episodes", str(episodes_path), "--k", "2"]) == 0


def test_acceptance_rf11_in_benchmark_seed():
    intent_ids = {pair["intent_id"] for pair in load_all_pairs()}
    assert "RF-11" in intent_ids


def test_acceptance_mutation_score_on_test_gen_episodes(tmp_path: Path):
    episodes_path = tmp_path / "episodes.jsonl"
    traces_dir = tmp_path / "traces"
    _, episodes = run_eval(
        failure_mode=None,
        output_path=tmp_path / "metrics.json",
        traces_dir=traces_dir,
        episodes_path=episodes_path,
    )
    test_gen = [ep for ep in episodes if ep["task_family"] == "test_gen"]
    assert all("mutation_score" in ep for ep in test_gen)
    assert all(ep["mutation_score"] == 1.0 for ep in test_gen if ep["variant"] == "clean")
