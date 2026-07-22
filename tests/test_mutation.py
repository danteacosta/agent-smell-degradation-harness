from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval.mutation import score_test_gen_mutation
from eval.runner import run_eval
from pairs.loader import load_all_pairs


def _pair(intent_id: str) -> dict:
    return next(p for p in load_all_pairs() if p["intent_id"] == intent_id)


def test_clean_rf09_test_gen_catches_all_mutants():
    pair = _pair("RF-09")
    artifact = pair["oracle_spec"]["test_gen"]
    score = score_test_gen_mutation("RF-09", artifact, pair["oracle_spec"])
    assert score == 1.0


def test_weak_rf09_test_gen_catches_fewer_mutants():
    pair = _pair("RF-09")
    weak = {
        "must_reject_minutes": [],
        "must_accept_minutes": [6],
        "criterion": "after significant time",
    }
    score = score_test_gen_mutation("RF-09", weak, pair["oracle_spec"])
    assert score < 1.0


def test_runner_attaches_mutation_score_for_test_gen(tmp_path: Path):
    episodes_path = tmp_path / "episodes.jsonl"
    traces_dir = tmp_path / "traces"
    _, episodes = run_eval(
        failure_mode="smell-blind",
        output_path=tmp_path / "metrics.json",
        traces_dir=traces_dir,
        episodes_path=episodes_path,
    )

    test_gen = [ep for ep in episodes if ep["task_family"] == "test_gen"]
    assert test_gen
    for episode in test_gen:
        assert "mutation_score" in episode
        assert 0.0 <= episode["mutation_score"] <= 1.0


@pytest.mark.parametrize("intent_id", ["RF-04", "RF-07", "RF-09", "RF-11", "RF-13"])
def test_clean_test_gen_perfect_mutation_score(intent_id: str):
    pair = _pair(intent_id)
    score = score_test_gen_mutation(
        intent_id,
        pair["oracle_spec"]["test_gen"],
        pair["oracle_spec"],
    )
    assert score == 1.0
