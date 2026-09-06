import copy
import pytest
from eval.temporal_diagnostics import analyze


def episode(identifier='a', defect=True):
    return {'episode_id': identifier, 'intent_id': identifier, 'terminal_ms': 100,
            'terminal_defect': defect, 'stages': [
                {'stage': 'T1', 'available_ms': 10, 'alert': False, 'cost_microusd': 2},
                {'stage': 'T2', 'available_ms': 30, 'alert': True, 'cost_microusd': 3},
                {'stage': 'T3', 'available_ms': 50, 'alert': False, 'cost_microusd': 0}]}


def test_first_alert_and_cumulative_ablation_cost_are_computed_per_episode():
    report = analyze([episode(), episode('b', False)])
    assert report['horizons']['T1']['alerts'] == 0
    assert report['horizons']['T1+T2']['alerts'] == 2
    assert report['horizons']['T1+T2']['false_alerts'] == 1
    assert report['horizons']['T1+T2']['cost_microusd'] == 10
    assert report['episodes'][0]['first_alert_stage'] == 'T2'
    assert report['episodes'][0]['lead_time_ms'] == 70


def test_missing_stages_outcomes_and_costs_remain_missing():
    row = episode(defect=None)
    row['stages'] = row['stages'][:1]
    row['stages'][0]['cost_microusd'] = None
    report = analyze([row])
    assert report['horizons']['T1']['missing_cost_episodes'] == 1
    assert report['horizons']['T1']['cost_microusd'] is None
    assert report['horizons']['T1+T2']['missing_stage_episodes'] == 1
    assert report['horizons']['T1']['outcome_labeled_episodes'] == 0
    assert report['horizons']['T1']['false_alert_rate'] is None


def test_post_final_or_duplicate_stages_are_rejected():
    for timestamp in (100, 110, float('nan')):
        row = episode()
        row['stages'][0]['available_ms'] = timestamp
        with pytest.raises(ValueError):
            analyze([row])
    row = episode()
    row['stages'].append(copy.deepcopy(row['stages'][0]))
    with pytest.raises(ValueError):
        analyze([row])


def test_duplicate_episodes_cannot_inflate_denominators():
    with pytest.raises(ValueError):
        analyze([episode(), episode()])
