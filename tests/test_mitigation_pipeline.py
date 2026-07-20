from pathlib import Path

from eval.runner import run_eval
from mitigation.pipeline import prepare_requirement
from pairs.loader import load_all_pairs


def test_prepare_requirement_rewrite_uses_clean_on_smelly():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    prepared = prepare_requirement(pair, variant="smelly", policy="rewrite")
    assert prepared.text == pair["clean_requirement"]
    assert prepared.policy == "rewrite"
    assert prepared.generation_variant == "clean"
    assert prepared.mitigation_meta.get("rewrite_changed") is True


def test_prepare_requirement_direct_smelly_unchanged():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    prepared = prepare_requirement(pair, variant="smelly", policy="direct")
    assert prepared.text == pair["smelly_requirement"]
    assert prepared.generation_variant == "smelly"


def test_smell_blind_rewrite_eliminates_degradation(tmp_path):
    output_path = tmp_path / "metrics.json"
    traces_dir = tmp_path / "traces"

    metrics_direct, _ = run_eval(
        failure_mode="smell-blind",
        policy="direct",
        output_path=output_path,
        traces_dir=traces_dir,
    )
    metrics_rw, _ = run_eval(
        failure_mode="smell-blind",
        policy="rewrite",
        output_path=tmp_path / "metrics_rewrite.json",
        traces_dir=tmp_path / "traces_rewrite",
    )
    assert metrics_direct["paired_degradation_rate"] > 0
    assert metrics_rw["paired_degradation_rate"] == 0


def test_smell_blind_clarify_eliminates_degradation(tmp_path):
    metrics_direct, _ = run_eval(
        failure_mode="smell-blind",
        policy="direct",
        output_path=tmp_path / "metrics_direct.json",
        traces_dir=tmp_path / "traces_direct",
    )
    metrics_cl, _ = run_eval(
        failure_mode="smell-blind",
        policy="clarify",
        output_path=tmp_path / "metrics_clarify.json",
        traces_dir=tmp_path / "traces_clarify",
    )
    assert metrics_direct["paired_degradation_rate"] > 0
    assert metrics_cl["paired_degradation_rate"] == 0
