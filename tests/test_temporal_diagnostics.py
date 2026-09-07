import copy
import itertools
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


def test_partial_observations_keep_measured_cost_and_unknown_total():
    row = episode()
    row['stages'] = row['stages'][:2]
    row['stages'][1]['cost_microusd'] = None
    result = analyze([row])['horizons']['T1+T2+T3']
    assert result['known_cost_microusd'] == 2
    assert result['missing_cost_episodes'] == 1
    assert result['cost_microusd'] is None


def test_complete_case_zero_false_alerts_does_not_hide_missing_observations():
    complete = episode(defect=False)
    for stage in complete['stages']:
        stage['alert'] = False
    partial = episode('partial', False)
    partial['stages'] = partial['stages'][:1]
    result = analyze([complete, partial])['horizons']['T1+T2+T3']
    assert result['false_alert_rate'] == 0  # Existing complete-case statistic.
    assert result['rate_scope'] == 'complete_stage_labeled_episodes'
    bounds = result['missing_stage_bounds']['nondefective']
    assert bounds == {'labeled_episodes': 2, 'observed_alerts': 0,
                      'unresolved_alert_episodes': 1,
                      'alert_rate_lower': 0, 'alert_rate_upper': 0.5}


@pytest.mark.parametrize('defect,group', [(False, 'nondefective'), (True, 'defective')])
def test_missing_stage_bounds_match_all_possible_boolean_completions(defect, group):
    # Exhaust all absent/false/true observations, not just hand-picked examples.
    for values in itertools.product((None, False, True), repeat=3):
        row = episode(defect=defect)
        row['stages'] = [dict(s, alert=v) for s, v in zip(row['stages'], values)
                         if v is not None]
        horizons = analyze([row])['horizons']
        for size, horizon in enumerate(horizons.values(), 1):
            observed = values[:size]
            completions = [any(completion) for completion in itertools.product(
                *[(False, True) if v is None else (v,) for v in observed])]
            bounds = horizon['missing_stage_bounds'][group]
            assert bounds['alert_rate_lower'] == min(completions)
            assert bounds['alert_rate_upper'] == max(completions)


def test_unlabeled_and_empty_inputs_do_not_fabricate_bounds():
    for rows in ([], [episode(defect=None)]):
        result = analyze(rows)
        assert result['confirmatory_eligible'] is False
        for horizon in result['horizons'].values():
            assert horizon['missing_stage_bounds']['unlabeled_episodes'] == len(rows)
            for group in ('defective', 'nondefective'):
                bounds = horizon['missing_stage_bounds'][group]
                assert bounds['labeled_episodes'] == 0
                assert bounds['alert_rate_lower'] is None
                assert bounds['alert_rate_upper'] is None


def test_first_alert_reports_whether_earlier_stages_are_observed():
    complete = episode()
    partial = episode('partial')
    partial['stages'] = partial['stages'][1:]
    absent = episode('absent')
    absent['stages'] = []
    results = analyze([complete, partial, absent])['episodes']
    assert results[0]['first_alert_prefix_complete'] is True
    assert results[1]['first_alert_prefix_complete'] is False
    assert results[1]['lead_time_ms'] == 70  # Observed lead time, not earliest possible.
    assert results[2]['first_alert_prefix_complete'] is None
