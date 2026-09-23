"""Observable classification for the TodoMVC persistence browser oracle."""
import hashlib
import json

import pytest

from eval import persistence_executor as oracle


HASH = hashlib.sha256(b'<html></html>').hexdigest()


def report(**changes):
    cases = {key: 'passed' for key in oracle.ASSERTION_IDS}
    cases.update(changes)
    return json.dumps({'schema_version': 'persistence-browser/v1', 'status': 'complete',
                       'app_sha256': HASH,
                       'cases': [{'id': key, 'status': value} for key, value in cases.items()]}).encode()


def test_target_only_failure_is_separate_from_persistence_failure():
    assert oracle.classify_report(report(editing_not_restored='failed'), 1) == {
        'category': 'target_only_failure', 'target_failed': True, 'non_target_failed': []}
    assert oracle.classify_report(report(completed_survives_reload='failed'), 1) == {
        'category': 'non_target_only_failure', 'target_failed': False,
        'non_target_failed': ['completed_survives_reload']}


def test_missing_todo_does_not_count_as_success_or_failure_of_edit_target():
    value = json.loads(report(todo_survives_reload='failed', editing_not_restored='not_evaluable'))
    value['cases'][-1]['reason'] = 'todo_missing_after_reload'
    assert oracle.classify_report(json.dumps(value).encode(), 1) == {
        'category': 'target_not_evaluable', 'target_failed': None,
        'non_target_failed': ['todo_survives_reload']}


def test_hidden_todo_does_not_count_as_restored_user_visible_state():
    value = json.loads(report(todo_survives_reload='failed',
                              completed_survives_reload='failed',
                              editing_not_restored='not_evaluable'))
    value['cases'][-1]['reason'] = 'todo_not_visible_after_reload'
    assert oracle.classify_report(json.dumps(value).encode(), 1) == {
        'category': 'target_not_evaluable', 'target_failed': None,
        'non_target_failed': ['todo_survives_reload', 'completed_survives_reload']}


def test_ambiguous_todo_after_reload_does_not_count_as_target_failure():
    value = json.loads(report(todo_survives_reload='failed',
                              editing_not_restored='not_evaluable'))
    value['cases'][-1]['reason'] = 'todo_ambiguous_after_reload'
    assert oracle.classify_report(json.dumps(value).encode(), 1) == {
        'category': 'target_not_evaluable', 'target_failed': None,
        'non_target_failed': ['todo_survives_reload']}


def test_missing_required_edit_interface_is_invalid_generation():
    raw = json.dumps({'schema_version': 'persistence-browser/v1',
                      'status': 'interface_error', 'app_sha256': HASH,
                      'error': 'visible edit input required'}).encode()
    assert oracle.classify_report(raw, 2) == {
        'category': 'interface_error', 'reason': 'visible edit input required'}
    assert oracle.classify_report(raw, 1)['category'] == 'browser_error'


@pytest.mark.parametrize('raw,rc', [
    (b'{}', 0),
    (report(), 1),
    (report(editing_not_restored='not_evaluable'), 1),
    (report(unknown='failed'), 1),
    (report(editing_not_restored='failed'), 0),
])
def test_malformed_or_inconsistent_reports_fail_closed(raw, rc):
    assert oracle.classify_report(raw, rc)['category'] == 'browser_error'


def test_duplicate_json_fields_and_unhashable_ids_fail_closed():
    raw = report().replace(b'"status": "complete",', b'"status": "complete", "status": "complete",')
    assert oracle.classify_report(raw, 0)['category'] == 'browser_error'
    value = json.loads(report())
    value['cases'][0]['id'] = []
    assert oracle.classify_report(json.dumps(value).encode(), 0)['category'] == 'browser_error'
