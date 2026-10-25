import copy

import pytest

from eval.manipulation_admission import (
    candidate_inventory_sha256,
    prepare_manipulation_admission,
)


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
    assert packet["candidates"][0]["requires_adjudication"] is False
    assert all(packet["candidates"][0]["agreement"].values())
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
    "extra",
    [
        {"metadata": {"reward": 1, "arm": "C"}},
        {"oracleVerdict": "pass"},
        {"Reward": 1},
        {"provider_id": "example"},
        {"unreviewed_note": "extra"},
    ],
)
def test_rejects_fields_outside_the_outcome_blind_review_schema(extra):
    leaked = {**review(), **extra}
    with pytest.raises(ValueError, match="unknown review fields"):
        prepare_manipulation_admission(
            [leaked, review(reviewer="r-2")], expected_candidate_ids=["c-1"]
        )


@pytest.mark.parametrize("decision", [[], {}, None, True])
def test_rejects_non_string_decisions_with_a_validation_error(decision):
    malformed = review()
    malformed["decision"] = decision
    with pytest.raises(ValueError, match="invalid review decision"):
        prepare_manipulation_admission(
            [malformed, review(reviewer="r-2")], expected_candidate_ids=["c-1"]
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


@pytest.mark.parametrize(
    "field,value",
    [
        ("removed_span", "a different span"),
        ("target_constraint_id", "constraint-2"),
        ("dependent_constraint_ids", ["constraint-2"]),
        ("non_target_obligations_preserved", False),
        ("plausible_remainder", False),
        ("decision", "uncertain"),
    ],
)
def test_surfaces_disagreement_for_human_adjudication(field, value):
    second = review(reviewer="r-2")
    second[field] = value
    candidate = prepare_manipulation_admission(
        [review(), second], expected_candidate_ids=["c-1"]
    )["candidates"][0]
    assert candidate["agreement"][field] is False
    assert candidate["requires_adjudication"] is True


def test_consensus_exclusion_still_requires_adjudication():
    rows = [review(), review(reviewer="r-2")]
    for row in rows:
        row["decision"] = "exclude"
        row["dependent_constraint_ids"] = ["constraint-2"]
        row["reason"] = "The removed span also controls constraint-2."
    candidate = prepare_manipulation_admission(
        rows, expected_candidate_ids=["c-1"]
    )["candidates"][0]
    assert all(candidate["agreement"].values())
    assert candidate["requires_adjudication"] is True


def test_dependency_agreement_is_order_insensitive_but_preserves_evidence():
    first = review("c-1", "r-1")
    first["dependent_constraint_ids"] = ["constraint-2", "constraint-3"]
    second = review("c-1", "r-2")
    second["dependent_constraint_ids"] = ["constraint-3", "constraint-2"]

    candidate = prepare_manipulation_admission(
        [first, second], expected_candidate_ids=["c-1"]
    )["candidates"][0]

    assert candidate["agreement"]["dependent_constraint_ids"] is True
    assert candidate["requires_adjudication"] is True
    assert candidate["reviews"][0]["dependent_constraint_ids"] == [
        "constraint-2", "constraint-3"
    ]
    assert candidate["reviews"][1]["dependent_constraint_ids"] == [
        "constraint-3", "constraint-2"
    ]


def test_rejects_reviewer_identity_alias_by_surrounding_whitespace():
    with pytest.raises(ValueError, match="reviewer_id must not have surrounding whitespace"):
        prepare_manipulation_admission(
            [review(reviewer="r-1"), review(reviewer=" r-1 ")],
            expected_candidate_ids=["c-1"],
        )


@pytest.mark.parametrize(
    "field,value,expected_message",
    [
        ("target_constraint_id", " constraint-1", "target_constraint_id"),
        ("dependent_constraint_ids", ["constraint-2 "], "dependent constraint id"),
    ],
)
def test_rejects_noncanonical_constraint_identifiers(field, value, expected_message):
    malformed = review()
    malformed[field] = value
    with pytest.raises(ValueError, match=expected_message):
        prepare_manipulation_admission(
            [malformed, review(reviewer="r-2")],
            expected_candidate_ids=["c-1"],
        )


def test_rejects_noncanonical_expected_candidate_id():
    with pytest.raises(ValueError, match="expected candidate id"):
        prepare_manipulation_admission(
            [review(candidate=" c-1"), review(candidate=" c-1", reviewer="r-2")],
            expected_candidate_ids=[" c-1"],
        )


def test_packet_commits_to_the_ordered_candidate_inventory():
    ids = ["c-1", "c-2"]
    rows = [
        review("c-1", "r-1"),
        review("c-1", "r-2"),
        review("c-2", "r-1"),
        review("c-2", "r-2"),
    ]
    packet = prepare_manipulation_admission(rows, expected_candidate_ids=ids)
    assert packet["candidate_inventory_sha256"] == candidate_inventory_sha256(ids)
    assert packet["candidate_inventory_sha256"] != candidate_inventory_sha256(list(reversed(ids)))


def test_inventory_digest_is_utf8_and_json_canonical():
    assert candidate_inventory_sha256(["ação", "c-2"]) == (
        "b56475d55f2ae2032550dcb2cb15e964950945a1687dfc2fc3b8804b9d67fa0a"
    )
