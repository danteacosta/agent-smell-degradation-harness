import copy

import pytest

from eval.blind_semantic_review import prepare_blind_review


def row():
    return {"run_id": "run-a", "replication_id": "rep-a", "constraint_id": "rule-a",
            "original_rule": "Obtain confirmation before committing.",
            "scenario": "A simulated change request.", "trajectory": "User asks; agent acts.",
            "reward": 1, "model": "hidden-model", "variant": "hidden-treatment"}


def test_review_view_is_allowlisted_and_reward_invariant():
    source = row()
    first = prepare_blind_review([source])
    source.update(reward=0, model="different-model", variant="different-treatment")
    second = prepare_blind_review([source])
    assert first["review_view"] == second["review_view"]
    assert set(first["review_view"][0]) == {"blind_id", "original_rule", "scenario", "trajectory"}
    assert first["private_join_key"][0]["source"]["reward"] == 1


def test_preserves_all_rows_and_does_not_mutate_input():
    records = [row(), {**row(), "run_id": "run-b", "reward": None}]
    before = copy.deepcopy(records)
    result = prepare_blind_review(records)
    assert result["scheduled_denominator"] == len(result["review_view"]) == 2
    result["private_join_key"][0]["source"]["reward"] = -1
    assert records == before
    assert result["confirmatory_eligible"] is False


def test_duplicate_identity_is_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        prepare_blind_review([row(), row()])


@pytest.mark.parametrize("field", ["run_id", "trajectory", "original_rule"])
def test_missing_required_evidence_cannot_silently_shrink_the_batch(field):
    value = row()
    value[field] = ""
    with pytest.raises(ValueError, match=field):
        prepare_blind_review([row(), value])
