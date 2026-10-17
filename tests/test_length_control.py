import pytest

from eval.length_control import length_matched_control


@pytest.mark.parametrize("field", ["scores", "lengths"])
@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -float("inf"), True, "1", None])
def test_invalid_measurements_are_rejected_before_reporting(field, invalid):
    inputs = {"scores": [0.0, 1.0], "labels": [0, 1], "lengths": [1.0, 1.0]}
    inputs[field][0] = invalid
    with pytest.raises(ValueError, match=field):
        length_matched_control(**inputs, min_pairs=1)


def test_negative_trace_lengths_are_rejected():
    with pytest.raises(ValueError, match="lengths"):
        length_matched_control([0, 1], [0, 1], [-1, 1], min_pairs=1)


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -float("inf"), -1, True, "1", None])
def test_invalid_matching_tolerance_is_rejected(invalid):
    with pytest.raises(ValueError, match="tolerance"):
        length_matched_control([0, 1], [0, 1], [1, 1], tolerance=invalid, min_pairs=1)


@pytest.mark.parametrize("invalid", [0, -1, True, 1.0, float("nan"), float("inf"), "1", None])
def test_invalid_minimum_pair_count_cannot_report_success(invalid):
    with pytest.raises(ValueError, match="min_pairs"):
        length_matched_control([], [], [], min_pairs=invalid)


@pytest.mark.parametrize("invalid", [True, False, 1.0, 0.0])
def test_label_aliases_are_rejected(invalid):
    with pytest.raises(ValueError, match="labels"):
        length_matched_control([0, 1], [invalid, 1], [1, 1], min_pairs=1)


@pytest.mark.parametrize("scores,labels,lengths", [([], [], []), ([1], [1], [0])])
def test_valid_data_without_both_classes_remains_insufficient(scores, labels, lengths):
    result = length_matched_control(scores, labels, lengths, min_pairs=1)
    assert result["status"] == "insufficient_pairs"
    assert result["matched_auroc"] is None
    assert result["n_pairs"] == 0


def test_finite_negative_scores_and_nonnegative_fractional_lengths_are_valid():
    result = length_matched_control([-2, -1], [0, 1], [0.5, 0.5], tolerance=0, min_pairs=1)
    assert result["status"] == "ok"
    assert result["matched_auroc"] == 1.0
    assert result["claim"] == "descriptive_only"
