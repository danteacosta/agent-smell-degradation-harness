from __future__ import annotations

import pytest

from protocol.paired_stats import paired_probability_of_superiority


def _row(intent: str, project: str, clean: int, defective: int) -> dict:
    return {
        "intent_id": intent,
        "project_id": project,
        "clean_severity": clean,
        "defective_severity": defective,
    }


def test_hand_computed_estimate_weights_intents_equally() -> None:
    # Intent a: one worse pair (1) and one tie (0.5) -> 0.75.
    # Intent b: defective better -> 0.0.  Intent c: defective worse -> 1.0.
    # Mean over intents = (0.75 + 0.0 + 1.0) / 3 = 0.5833...
    rows = [
        _row("a", "P1", 0, 2),
        _row("a", "P1", 0, 0),
        _row("b", "P1", 1, 0),
        _row("c", "P2", 0, 3),
    ]
    result = paired_probability_of_superiority(rows, n_boot=500, seed=3)

    assert result["estimate"] == pytest.approx(1.75 / 3)
    assert result["pair_outcomes"] == {"defective_worse": 2, "tie": 1, "defective_better": 1}
    assert (result["n_pairs"], result["n_intents"], result["n_projects"]) == (4, 3, 2)
    interval = result["ci95_project_cluster"]
    assert interval["low"] <= result["estimate"] <= interval["high"]
    assert result["valid_for_inference"] is True


def test_replications_do_not_inflate_an_intent() -> None:
    many = [_row("a", "P1", 0, 1)] * 9 + [_row("b", "P2", 1, 0)]
    result = paired_probability_of_superiority(many)
    assert result["estimate"] == pytest.approx(0.5)


def test_consistent_harm_gives_small_randomization_pvalue() -> None:
    rows = [_row(f"i{k}", f"P{k % 4}", 0, 2) for k in range(10)]
    result = paired_probability_of_superiority(rows, n_perm=5000, seed=1)
    assert result["estimate"] == 1.0
    assert result["paired_randomization_pvalue"] < 0.01


def test_all_ties_is_null() -> None:
    rows = [_row("a", "P1", 1, 1), _row("b", "P2", 2, 2)]
    result = paired_probability_of_superiority(rows)
    assert result["estimate"] == 0.5
    assert result["paired_randomization_pvalue"] == 1.0


def test_single_project_reports_no_interval() -> None:
    rows = [_row("a", "P1", 0, 2), _row("b", "P1", 0, 1)]
    result = paired_probability_of_superiority(rows)
    assert result["ci95_project_cluster"] == {"low": None, "high": None}
    assert result["valid_for_inference"] is False


@pytest.mark.parametrize(
    "rows",
    [
        [{"intent_id": "a", "clean_severity": 0, "defective_severity": 1}],
        [_row("a", "P1", 0, 1), _row("a", "P2", 0, 1)],
        [{**_row("a", "P1", 0, 1), "defective_severity": "high"}],
    ],
)
def test_invalid_pairs_fail_closed(rows: list[dict]) -> None:
    with pytest.raises(ValueError):
        paired_probability_of_superiority(rows)


@pytest.mark.parametrize("field", ["clean_severity", "defective_severity"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), -1, 4, 0.5, True, None])
def test_out_of_rubric_rating_cannot_become_a_pair_outcome(field, value) -> None:
    row = {**_row("a", "P1", 0, 1), field: value}
    with pytest.raises(ValueError, match="ordinal ratings"):
        paired_probability_of_superiority([row])


@pytest.mark.parametrize("field", ["intent_id", "project_id"])
@pytest.mark.parametrize("value", [None, 123, True, [], {}, "", "  "])
def test_missing_or_nontext_identity_cannot_create_a_cluster(field, value) -> None:
    row = {**_row("a", "P1", 0, 1), field: value}
    with pytest.raises(ValueError, match="intent_id and project_id"):
        paired_probability_of_superiority([row])


def test_integer_valued_float_ratings_preserve_the_registered_scale() -> None:
    result = paired_probability_of_superiority([_row("a", "P1", 0.0, 3.0)])
    assert result["estimate"] == 1.0
    assert result["pair_outcomes"]["defective_worse"] == 1
