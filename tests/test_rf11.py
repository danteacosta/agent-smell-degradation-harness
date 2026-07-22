from __future__ import annotations

import pytest

from agents.stub import StubAgent
from eval.oracles import score_artifact
from pairs.loader import load_all_pairs
from taxonomy.catalog import DEGRADATION_MODES, INTENT_TO_MODE


def _pair(intent_id: str) -> dict:
    return next(p for p in load_all_pairs() if p["intent_id"] == intent_id)


def test_rf11_pair_loads():
    pair = _pair("RF-11")
    assert pair["smell"]["type"] == "numerical_inconsistency"
    assert pair["oracle_spec"]["codegen"]["refund_window_minutes"] == 10


def test_rf11_codegen_passes_clean_oracle():
    pair = _pair("RF-11")
    spec = pair["oracle_spec"]["codegen"]
    result = score_artifact("RF-11", "codegen", spec, spec)
    assert result.passed is True


def test_rf11_codegen_rejects_15_minute_window():
    pair = _pair("RF-11")
    spec = pair["oracle_spec"]["codegen"]
    result = score_artifact(
        "RF-11",
        "codegen",
        {"refund_window_minutes": 15},
        spec,
    )
    assert result.passed is False


def test_rf11_test_gen_rejects_15_only_interpretation():
    pair = _pair("RF-11")
    spec = pair["oracle_spec"]["test_gen"]
    weak = {
        "must_reject_minutes": [],
        "must_accept_minutes": [15],
        "criterion": "refund within reasonable time",
    }
    result = score_artifact("RF-11", "test_gen", weak, spec)
    assert result.passed is False


def test_rf11_smell_blind_stub_weakening():
    pair = _pair("RF-11")
    agent = StubAgent(failure_mode="smell-blind")
    artifact = agent.generate(pair, variant="smelly", task_family="codegen")
    assert artifact["refund_window_minutes"] == 15


def test_rf11_taxonomy_mapping():
    assert INTENT_TO_MODE["RF-11"] == "numerical_inconsistency"
    assert "numerical_inconsistency" in DEGRADATION_MODES
