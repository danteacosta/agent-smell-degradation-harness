import pytest

from eval.construction_shortcut import construction_shortcut_control


def test_order_marker_that_separates_classes_is_flagged_in_either_direction():
    labels = [0, 0, 0, 1, 1, 1]
    result = construction_shortcut_control(
        labels, {"position": [1, 2, 3, 4, 5, 6], "reversed": [6, 5, 4, 3, 2, 1], "noise": [1, 3, 2, 2, 3, 1]}
    )
    assert result["shortcut_detected"] is True
    assert result["flagged_features"] == ["position", "reversed"]
    assert result["directionless_auroc"]["position"] == 1.0
    assert result["directionless_auroc"]["reversed"] == 1.0
    assert result["directionless_auroc"]["noise"] < 0.9
    assert result["claim"] == "descriptive_only"


def test_uninformative_construction_fields_report_no_shortcut():
    result = construction_shortcut_control([0, 1, 0, 1], {"id_length": [3, 3, 3, 3]})
    assert result["shortcut_detected"] is False
    assert result["flagged_features"] == []


@pytest.mark.parametrize("labels", [[0, 0], [1, 1], [], [True, False], [0, 2], [0.0, 1.0]])
def test_labels_must_be_binary_integers_with_both_classes(labels):
    with pytest.raises(ValueError, match="labels"):
        construction_shortcut_control(labels, {"x": [0] * len(labels)})


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), True, "1", None])
def test_invalid_feature_values_are_rejected(invalid):
    with pytest.raises(ValueError, match="finite"):
        construction_shortcut_control([0, 1], {"x": [invalid, 1]})


def test_feature_length_mismatch_and_empty_features_are_rejected():
    with pytest.raises(ValueError, match="length"):
        construction_shortcut_control([0, 1], {"x": [1]})
    with pytest.raises(ValueError, match="empty"):
        construction_shortcut_control([0, 1], {})


@pytest.mark.parametrize("invalid", [0.4, 1.1, float("nan"), True, "0.9", None])
def test_invalid_threshold_is_rejected(invalid):
    with pytest.raises(ValueError, match="threshold"):
        construction_shortcut_control([0, 1], {"x": [0, 1]}, threshold=invalid)
