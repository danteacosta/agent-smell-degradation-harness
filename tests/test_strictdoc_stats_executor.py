"""Observable classification of the StrictDoc statistics screen."""
import hashlib
import json

import pytest

from eval import strictdoc_stats_executor as oracle


HASH = hashlib.sha256(b'<html></html>').hexdigest()


def report(**changes):
    states = {key: 'passed' for key in oracle.ASSERTION_IDS}
    states.update(changes)
    observations = []
    for clock, text in (('clock-one', '2032 04 17'), ('clock-two', '2034 11 23')):
        observed = dict(oracle.CONTRACT['expected'])
        for group, keys in oracle.CONTRACT['groups'].items():
            if states[group] == 'failed':
                observed[keys[0]] = 'wrong'
        passed = states['generation_date_visible'] == 'passed'
        observations.append({'clock_id': clock, 'observed': observed,
            'date_visible': passed, 'matched_date': text if passed else None,
            'visible_text': text if passed else '', 'scroll_positions': [0],
            'screenshot': clock + '.png', 'console_errors': [],
            'visible_text_sha256': hashlib.sha256((text if passed else '').encode()).hexdigest()})
    return json.dumps({'schema_version': 'strictdoc-stats-browser/v1',
                       'status': 'complete', 'app_sha256': HASH,
                       'observations': observations,
                       'cases': [{'id': key, 'status': value} for key, value in states.items()]}).encode()


def test_target_only_and_non_target_failures_remain_distinct():
    assert oracle.classify_report(report(generation_date_visible='failed'), 1) == {
        'category': 'target_only_failure', 'target_failed': True, 'non_target_failed': []}
    assert oracle.classify_report(report(project_identity='failed'), 1) == {
        'category': 'non_target_only_failure', 'target_failed': False,
        'non_target_failed': ['project_identity']}


@pytest.mark.parametrize('raw,rc', [
    (b'{}', 0), (report(), 1),
    (report(generation_date_visible='failed'), 0),
    (report(unknown='failed'), 1),
    (report(generation_date_visible='not_evaluable'), 1),
])
def test_inconsistent_reports_fail_closed(raw, rc):
    assert oracle.classify_report(raw, rc)['category'] == 'browser_error'


def test_duplicate_fields_and_unhashable_ids_fail_closed():
    raw = report().replace(b'"status": "complete",', b'"status": "complete", "status": "complete",')
    assert oracle.classify_report(raw, 0)['category'] == 'browser_error'
    value = json.loads(report())
    value['cases'][0]['id'] = []
    assert oracle.classify_report(json.dumps(value).encode(), 0)['category'] == 'browser_error'


def test_interface_error_is_not_target_failure():
    raw = json.dumps({'schema_version': 'strictdoc-stats-browser/v1',
                      'status': 'interface_error', 'app_sha256': HASH,
                      'error': 'missing observation handle'}).encode()
    assert oracle.classify_report(raw, 2)['category'] == 'interface_error'


@pytest.mark.parametrize('change', [
    lambda value: value.update(observations=[{}, {}]),
    lambda value: value['observations'][0].update(date_visible=False, matched_date=None),
    lambda value: value['observations'][0]['observed'].update({'git-revision': 'wrong'}),
    lambda value: value['observations'][0].update(visible_text_sha256='0' * 64),
    lambda value: value['observations'][0].update(clock_id='clock-two'),
    lambda value: value['observations'][0].update(
        visible_text='No date here', visible_text_sha256=hashlib.sha256(b'No date here').hexdigest()),
    lambda value: value['observations'][0].update(matched_date='2034 11 23'),
])
def test_missing_or_contradictory_observations_fail_closed(change):
    value = json.loads(report())
    change(value)
    assert oracle.classify_report(json.dumps(value).encode(), 0)['category'] == 'browser_error'
