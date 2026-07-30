from __future__ import annotations

import json
from pathlib import Path

from eval.prepilot import run_pre_pilot


def _lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_offline_prepilot_writes_reproducible_120_episode_scientific_export(tmp_path):
    output = run_pre_pilot(output_root=tmp_path, run_id="prepilot-fixed")

    run_dir = Path(output["run_dir"])
    assert len(_lines(run_dir / "episodes.jsonl")) == 120
    assert len(_lines(run_dir / "events.jsonl")) >= 120
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "artifacts").is_dir()
    assert (run_dir / "labels.jsonl").exists()
    assert (run_dir / "features").is_dir()
    assert (run_dir / "analysis" / "estimands.json").exists()
    assert (run_dir / "analysis" / "boundary_map.json").exists()


def test_prepilot_group_splits_hold_out_whole_intents_and_keep_thresholds_in_fold(tmp_path):
    run_dir = Path(run_pre_pilot(output_root=tmp_path, run_id="split-fixed")["run_dir"])
    split = json.loads((run_dir / "analysis" / "group_splits.json").read_text())

    assert split["group_by"] == "intent_id"
    for fold in split["folds"]:
        assert not set(fold["test_intents"]) & set(fold["selection_intents"])
        assert not set(fold["test_intents"]) & set(fold["calibration_intents"])
        assert fold["threshold_path"]["fit_intents"] == fold["calibration_intents"]
