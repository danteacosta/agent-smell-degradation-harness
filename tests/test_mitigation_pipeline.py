from pathlib import Path

from eval.runner import run_eval
from mitigation.pipeline import prepare_requirement
from pairs.loader import load_all_pairs


def test_prepare_requirement_structured_rewrite_is_oracle_free():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    prepared = prepare_requirement(pair, variant="smelly", policy="structured_rewrite")
    assert pair["smelly_requirement"] in prepared.text
    assert pair["clean_requirement"] not in prepared.text
    assert prepared.policy == "structured_rewrite"
    assert prepared.generation_variant == "smelly"
    assert prepared.mitigation_meta.get("rewrite_changed") is True
    assert prepared.mitigation_meta["oracle_access"] is False


def test_prepare_requirement_direct_smelly_unchanged():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    prepared = prepare_requirement(pair, variant="smelly", policy="direct")
    assert prepared.text == pair["smelly_requirement"]
    assert prepared.generation_variant == "smelly"


def test_smell_blind_structured_rewrite_does_not_fake_recovery(tmp_path):
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
        policy="structured_rewrite",
        output_path=tmp_path / "metrics_rewrite.json",
        traces_dir=tmp_path / "traces_rewrite",
    )
    assert metrics_direct["paired_degradation_rate"] > 0
    assert metrics_rw["paired_degradation_rate"] > 0


def test_smell_blind_targeted_clarification_requires_external_answer(tmp_path):
    metrics_direct, _ = run_eval(
        failure_mode="smell-blind",
        policy="direct",
        output_path=tmp_path / "metrics_direct.json",
        traces_dir=tmp_path / "traces_direct",
    )
    metrics_cl, _ = run_eval(
        failure_mode="smell-blind",
        policy="targeted_clarification",
        output_path=tmp_path / "metrics_clarify.json",
        traces_dir=tmp_path / "traces_clarify",
    )
    assert metrics_direct["paired_degradation_rate"] > 0
    assert metrics_cl["paired_degradation_rate"] > 0


def test_oracle_upper_bounds_are_explicit_and_recover_clean():
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    rewrite = prepare_requirement(
        pair, variant="smelly", policy="oracle_rewrite_upper_bound"
    )
    clarify = prepare_requirement(
        pair, variant="smelly", policy="oracle_clarification_upper_bound"
    )
    assert rewrite.text == pair["clean_requirement"]
    assert clarify.text == pair["clean_requirement"]
    assert rewrite.mitigation_meta["rq3_admissible"] is False
    assert clarify.mitigation_meta["rq3_admissible"] is False


def test_legacy_policy_names_fail_closed():
    import pytest

    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    with pytest.raises(ValueError, match="ambiguous"):
        prepare_requirement(pair, variant="smelly", policy="rewrite")


def test_runner_accepts_independent_clarification_answers(tmp_path):
    pair = next(p for p in load_all_pairs() if p["intent_id"] == "RF-09")
    _metrics, episodes = run_eval(
        failure_mode="smell-blind",
        policy="targeted_clarification",
        clarification_answers={"RF-09": "Use a strict five-minute boundary."},
        output_path=tmp_path / "metrics.json",
        traces_dir=tmp_path / "traces",
    )
    episode = next(
        item
        for item in episodes
        if item["source_intent_id"] == pair["intent_id"]
        and item["variant"] == "smelly"
    )
    assert "Independent answer: Use a strict five-minute boundary." in episode["requirement_text"]
    assert episode["mitigation_meta"]["answer_source"] == "independent"
