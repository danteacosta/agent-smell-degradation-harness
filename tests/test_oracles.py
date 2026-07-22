from __future__ import annotations

import pytest

from agents.stub import StubAgent
from eval.oracles import score_artifact
from pairs.loader import load_all_pairs


def _pair(intent_id: str) -> dict:
    return next(p for p in load_all_pairs() if p["intent_id"] == intent_id)


def test_rf09_codegen_pass():
    spec = {"delay_threshold_minutes": 5, "comparator": ">"}
    r = score_artifact("RF-09", "codegen", {"delay_threshold_minutes": 5, "comparator": ">"}, spec)
    assert r.passed is True


def test_rf09_test_gen_rejects_vague():
    spec = {
        "must_reject_minutes": [0, 5],
        "must_accept_minutes": [6],
        "criterion": "delay_minutes > 5",
    }
    weak = {
        "must_reject_minutes": [],
        "must_accept_minutes": [6],
        "criterion": "after significant time",
    }
    r = score_artifact("RF-09", "test_gen", weak, spec)
    assert r.passed is False


@pytest.mark.parametrize(
    "intent_id",
    ["RF-04", "RF-07", "RF-09", "RF-11", "RF-13"],
)
def test_codegen_passes_matching_artifact(intent_id: str):
    pair = _pair(intent_id)
    spec = pair["oracle_spec"]["codegen"]
    r = score_artifact(intent_id, "codegen", spec, spec)
    assert r.passed is True


@pytest.mark.parametrize(
    ("intent_id", "weak_artifact"),
    [
        ("RF-04", {"order_id_pattern": r"^P-\d+$"}),
        ("RF-07", {"sort_key": "order_code"}),
        ("RF-09", {"delay_threshold_minutes": 5, "comparator": ">="}),
        ("RF-13", {"cardinality": 10, "selection": "oldest_active"}),
    ],
)
def test_codegen_rejects_weakened_artifact(intent_id: str, weak_artifact: dict):
    spec = _pair(intent_id)["oracle_spec"]["codegen"]
    r = score_artifact(intent_id, "codegen", weak_artifact, spec)
    assert r.passed is False


@pytest.mark.parametrize(
    "intent_id",
    ["RF-04", "RF-07", "RF-09", "RF-11", "RF-13"],
)
def test_test_gen_passes_matching_artifact(intent_id: str):
    pair = _pair(intent_id)
    spec = pair["oracle_spec"]["test_gen"]
    r = score_artifact(intent_id, "test_gen", spec, spec)
    assert r.passed is True


@pytest.mark.parametrize(
    ("intent_id", "weak_artifact"),
    [
        (
            "RF-04",
            {
                "must_reject_ids": [],
                "must_accept_ids": ["P-014"],
                "criterion": "starts with P- followed by digits",
            },
        ),
        (
            "RF-07",
            {
                "required_sort_key": "order_code",
                "forbidden_sort_keys": ["order_code", "seed"],
                "criterion": "cards ordered by order antiquity",
            },
        ),
        (
            "RF-09",
            {
                "must_reject_minutes": [],
                "must_accept_minutes": [6],
                "criterion": "after significant time",
            },
        ),
        (
            "RF-13",
            {
                "exact_cardinality": 10,
                "criterion": "display old active orders in sufficient quantity",
            },
        ),
    ],
)
def test_test_gen_rejects_weakened_artifact(intent_id: str, weak_artifact: dict):
    spec = _pair(intent_id)["oracle_spec"]["test_gen"]
    r = score_artifact(intent_id, "test_gen", weak_artifact, spec)
    assert r.passed is False


def test_smell_blind_stub_fails_codegen_oracle():
    pair = _pair("RF-09")
    agent = StubAgent(failure_mode="smell-blind")
    artifact = agent.generate(pair, variant="smelly", task_family="codegen")
    spec = pair["oracle_spec"]["codegen"]
    r = score_artifact("RF-09", "codegen", artifact, spec)
    assert r.passed is False


def test_smell_blind_stub_fails_test_gen_oracle():
    pair = _pair("RF-09")
    agent = StubAgent(failure_mode="smell-blind")
    artifact = agent.generate(pair, variant="smelly", task_family="test_gen")
    spec = pair["oracle_spec"]["test_gen"]
    r = score_artifact("RF-09", "test_gen", artifact, spec)
    assert r.passed is False
