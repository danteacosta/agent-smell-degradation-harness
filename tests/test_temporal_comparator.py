import pytest
from eval.temporal_comparator import structural_features, fit_fpr_threshold


def event(stage='T1', time=1, activity='interpretation.completed'):
    return {'stage': stage, 'available_ms': time, 'activity': activity}


def test_structure_keeps_order_and_has_no_semantic_payload():
    first = structural_features([event(), event(time=2, activity='tool.completed'), event(time=3)], stage='T1', cutoff_ms=3)
    second = structural_features([event(), event(time=2), event(time=3, activity='tool.completed')], stage='T1', cutoff_ms=3)
    assert first['activity_counts'] == second['activity_counts']
    assert first['transition_counts'] != second['transition_counts']
    assert first['repeated_activity_fraction'] == pytest.approx(1/3)


@pytest.mark.parametrize('field', ['terminal_defect', 'oracle_passed', 'final_text', 'constraint_id', 'total_trace_length', 'label'])
def test_terminal_and_semantic_payload_cannot_enter_structure(field):
    row = event(); row[field] = 'hidden'
    with pytest.raises(ValueError, match='allowlist'):
        structural_features([row], stage='T1', cutoff_ms=3)


@pytest.mark.parametrize('row', [event(stage='T4'), event(stage='T3'), event(time=4), event(activity='Delete only for author')])
def test_future_or_unregistered_evidence_is_rejected(row):
    with pytest.raises(ValueError):
        structural_features([row], stage='T1', cutoff_ms=3)


def test_nonmonotonic_rows_fail_closed():
    with pytest.raises(ValueError, match='nonmonotonic'):
        structural_features([event(time=2), event(time=1)], stage='T1', cutoff_ms=3)


def test_empty_prefix_is_missing_evidence_not_zero_repetition():
    assert structural_features([], stage='T1', cutoff_ms=3)['repeated_activity_fraction'] is None


def test_fpr_threshold_maximizes_recall_within_predeclared_budget():
    result = fit_fpr_threshold([.9, .8, .7, .6], [1, 0, 1, 0], split='calibration', max_fpr=0)
    assert result['threshold'] == .9
    assert result['recall'] == .5
    assert result['fpr'] == 0


def test_no_valid_positive_alert_operating_point_abstains():
    result = fit_fpr_threshold([.9, .8], [0, 1], split='calibration', max_fpr=0)
    assert result['threshold'] is None


@pytest.mark.parametrize('split', ['train', 'test'])
def test_test_or_training_outcomes_cannot_tune_threshold(split):
    with pytest.raises(ValueError, match='calibration'):
        fit_fpr_threshold([.9, .8], [0, 1], split=split, max_fpr=.05)


@pytest.mark.parametrize('labels', [[1, 1], [0, 0], [False, True]])
def test_threshold_requires_valid_independent_classes(labels):
    with pytest.raises(ValueError, match='classes'):
        fit_fpr_threshold([.9, .8], labels, split='calibration', max_fpr=.05)


def test_stage_order_cannot_move_backward_even_with_increasing_timestamps():
    with pytest.raises(ValueError, match='stages must be ordered'):
        structural_features([event(stage='T2'), event(stage='T1', time=2)], stage='T3', cutoff_ms=3)


@pytest.mark.parametrize('scores', [[float('nan'), .8], [float('inf'), .8]])
def test_nonfinite_scores_cannot_calibrate(scores):
    with pytest.raises(ValueError, match='finite scores'):
        fit_fpr_threshold(scores, [0, 1], split='calibration', max_fpr=.05)
