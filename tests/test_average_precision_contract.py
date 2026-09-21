"""Known threshold-level results, independent of implementation structure."""
import itertools

import pytest

from eval.confirmatory_report import average_precision
from eval.calibration import select_family


def test_equal_scores_have_prevalence_precision_in_every_order():
    for labels in set(itertools.permutations([0, 0, 1, 1])):
        assert average_precision([0.5] * 4, labels) == pytest.approx(0.5)


def test_mixed_thresholds_use_whole_tie_groups():
    # First threshold: recall 1/2, precision 1/2; second: recall 1, precision 2/3.
    assert average_precision([0.9, 0.9, 0.1], [1, 0, 1]) == pytest.approx(7 / 12)
    assert average_precision([3, 2, 1], [1, 0, 1]) == pytest.approx(5 / 6)
    assert average_precision([2, 1], [1, 0]) == 1.0
    assert average_precision([2, 1], [0, 1]) == 0.5


@pytest.mark.parametrize('scores, labels', [
    ([1], [1, 0]), ([1, 2], [1]), ([float('nan')], [1]),
    ([float('inf')], [0]), ([1], [2]), ([1], [-1]), ([1], ['1']),
])
def test_invalid_metric_inputs_are_rejected(scores, labels):
    with pytest.raises(ValueError):
        average_precision(scores, labels)


def test_family_selection_cannot_reward_ties_ordered_by_outcome():
    result = select_family({'tied': [1, 1, 1, 1], 'useful': [3, 1, 2, 0]}, [1, 1, 0, 0])
    assert result['selected_family'] == 'useful'
    assert result['candidates']['tied']['pr_auc'] == pytest.approx(0.5)


def test_no_positive_convention_is_explicitly_preserved():
    assert average_precision([], []) == 0.0
    assert average_precision([1, 2], [0, 0]) == 0.0


def test_threshold_evaluation_reports_same_ap_for_tied_outcome_orders():
    from eval.calibration import evaluate_threshold
    for labels in set(itertools.permutations([0, 0, 1, 1])):
        report = evaluate_threshold([1, 1, 1, 1], labels, 0.5)
        assert report['pr_auc'] == pytest.approx(0.5)
