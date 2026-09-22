"""Observable result classification for the TodoMVC Mark all browser oracle."""
import hashlib
import json
import pytest

from eval import mark_all_executor as oracle

HASH = hashlib.sha256(b'<html></html>').hexdigest()


def report(statuses, target_reason=None, clear_reason=None):
    cases = [{'id': key, 'status': value} for key, value in statuses.items()]
    if target_reason is not None:
        next(c for c in cases if c['id'] == 'clear_master_after_clear_completed')['reason'] = target_reason
    if clear_reason is not None:
        next(c for c in cases if c['id'] == 'clear_completed_removes_items')['reason'] = clear_reason
    return json.dumps({'schema_version': 'mark-all-browser/v1', 'status': 'complete',
        'app_sha256': HASH, 'cases': cases}).encode()


def states(**changes):
    value = {key: 'passed' for key in oracle.ASSERTION_IDS}
    value.update(changes)
    return value


def test_target_only_and_non_target_failures_are_distinct():
    raw = report(states(clear_master_after_clear_completed='failed'))
    assert oracle.classify_report(raw, 1) == {'category': 'target_only_failure',
        'target_failed': True, 'non_target_failed': []}
    raw = report(states(master_tracks_individuals='failed'))
    assert oracle.classify_report(raw, 1) == {'category': 'non_target_only_failure',
        'target_failed': False, 'non_target_failed': ['master_tracks_individuals']}


def test_unmet_clear_prerequisite_does_not_count_as_target_failure():
    raw = report(states(clear_completed_removes_items='failed',
                        clear_master_after_clear_completed='not_evaluable'),
                 target_reason='clear_failed')
    assert oracle.classify_report(raw, 1) == {'category': 'target_not_evaluable',
        'target_failed': None, 'non_target_failed': ['clear_completed_removes_items']}


def test_bulk_failure_does_not_claim_clear_removal_failed():
    raw = report(states(master_sets_items='failed',
                        clear_completed_removes_items='not_evaluable',
                        clear_master_after_clear_completed='not_evaluable'),
                 target_reason='bulk_selection_failed', clear_reason='bulk_selection_failed')
    assert oracle.classify_report(raw, 1) == {'category': 'target_not_evaluable',
        'target_failed': None, 'non_target_failed': ['master_sets_items']}


def test_unrelated_checked_checkbox_makes_removed_master_ambiguous():
    raw = report(states(clear_master_after_clear_completed='not_evaluable'),
                 target_reason='master_identity_ambiguous')
    assert oracle.classify_report(raw, 1) == {'category': 'target_not_evaluable',
        'target_failed': None, 'non_target_failed': []}


@pytest.mark.parametrize('bad,rc', [
    (b'{}', 0), (report(states()), 1),
    (report(states(clear_master_after_clear_completed='not_evaluable')), 0),
    (report(states(clear_master_after_clear_completed='not_evaluable'), target_reason='unknown'), 0),
    (report(states(clear_completed_removes_items='not_evaluable',
                   clear_master_after_clear_completed='not_evaluable'),
            target_reason='bulk_selection_failed'), 1),
    (report(states(unknown='failed')), 1),
    (b'{"schema_version":"mark-all-browser/v1","status":"complete","app_sha256":"' +
     HASH.encode() + b'","cases":[{"id":[],"status":"passed"}]}', 0),
])
def test_inconsistent_or_incomplete_report_fails_closed(bad, rc):
    assert oracle.classify_report(bad, rc)['category'] == 'browser_error'


def test_non_string_case_id_returns_invalid_report_instead_of_throwing():
    value = json.loads(report(states()))
    value['cases'][0]['id'] = []
    assert oracle.classify_report(json.dumps(value).encode(), 0)['category'] == 'browser_error'
