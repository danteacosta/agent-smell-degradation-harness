import copy

import pytest

from eval.manipulation_admission import prepare_manipulation_admission


def review(candidate="c-1", reviewer="r-1"):
    return {
        "candidate_id": candidate,
        "reviewer_id": reviewer,
        "removed_span": "after explicit approval",
        "target_constraint_id": "constraint-1",
        "dependent_constraint_ids": [],
        "non_target_obligations_preserved": True,
        "plausible_remainder": True,
        "decision": "admit",
        "reason": "The remaining requirement is self-contained.",
    }


def test_prepares_complete_packet_without_automatic_admission():
    rows = [review(), review(reviewer="r-2")]
    before = copy.deepcopy(rows)
    packet = prepare_manipulation_admission(rows, expected_candidate_ids=["c-1"])
    assert packet["candidate_count"] == 1
    assert packet["review_count"] == 2
    assert packet["confirmatory_eligible"] is False
    packet["candidates"][0]["reviews"][0]["reason"] = "changed"
    assert rows == before


def test_requires_exact_frozen_candidate_coverage():
    with pytest.raises(ValueError, match="two independent reviews"):
        prepare_manipulation_admission(
            [review(), review(reviewer="r-2")],
            expected_candidate_ids=["c-1", "c-2"],
        )
    with pytest.raises(ValueError, match="outside expected inventory"):
        prepare_manipulation_admission(
            [review("c-2"), review("c-2", "r-2")],
            expected_candidate_ids=["c-1"],
        )


def test_requires_two_distinct_reviewers():
    with pytest.raises(ValueError, match="duplicate candidate-reviewer"):
        prepare_manipulation_admission(
            [review(), review()], expected_candidate_ids=["c-1"]
        )


@pytest.mark.parametrize("field", ["reward", "terminal_defect", "arm", "provider"])
def test_rejects_outcome_and_treatment_leakage(field):
    leaked = review()
    leaked[field] = 1
    with pytest.raises(ValueError, match="forbidden"):
        prepare_manipulation_admission(
            [leaked, review(reviewer="r-2")], expected_candidate_ids=["c-1"]
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("removed_span", ""),
        ("decision", "approve"),
        ("dependent_constraint_ids", [""]),
        ("non_target_obligations_preserved", None),
        ("plausible_remainder", "yes"),
    ],
)
def test_rejects_malformed_review_evidence(field, value):
    malformed = review()
    malformed[field] = value
    with pytest.raises(ValueError):
        prepare_manipulation_admission(
            [malformed, review(reviewer="r-2")], expected_candidate_ids=["c-1"]
        )


def test_preserves_frozen_candidate_order_not_review_input_order():
    rows = [
        review("c-2", "r-2"), review("c-1", "r-2"),
        review("c-2", "r-1"), review("c-1", "r-1"),
    ]
    packet = prepare_manipulation_admission(
        rows, expected_candidate_ids=["c-1", "c-2"]
    )
    assert [item["candidate_id"] for item in packet["candidates"]] == ["c-1", "c-2"]
