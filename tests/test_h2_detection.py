from __future__ import annotations

import json
from pathlib import Path

from eval.h2_detection import evaluate_group_split, group_kfold_intent_ids
from eval.runner import run_eval


def test_group_kfold_never_splits_same_intent():
    intent_ids = ["RF-04", "RF-04", "RF-07", "RF-09", "RF-11", "RF-13"]
    folds = group_kfold_intent_ids(intent_ids, k=3)
    seen: set[str] = set()
    for fold in folds:
        for intent_id in fold:
            assert intent_id not in seen
            seen.add(intent_id)


def test_h2_group_split_computes_provenance_auroc(tmp_path: Path):
    episodes_path = tmp_path / "episodes.jsonl"
    traces_dir = tmp_path / "traces"
    _, episodes = run_eval(
        failure_mode="smell-blind",
        output_path=tmp_path / "metrics.json",
        traces_dir=traces_dir,
        episodes_path=episodes_path,
    )

    report = evaluate_group_split(episodes, k=3)
    assert "mean_auroc" in report
    assert "provenance_semantic" in report["mean_auroc"]
    assert 0.0 <= report["mean_auroc"]["provenance_semantic"] <= 1.0
    assert report["folds"]
