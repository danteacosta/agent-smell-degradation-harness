"""All planned observations count; authored answers are not provider evidence."""
import json

import pytest

from eval.addressed_comparison_plan import prepare_comparison
from label_plane.artifact_segments import build_snapshot
from test_addressed_comparison_plan import failed_predecessor


def api():
    from eval import addressed_comparison_audit
    return addressed_comparison_audit


def plan_fixture(tmp_path):
    _, run = failed_predecessor(tmp_path)
    return prepare_comparison(run, approval=True)


def responses(plan, phase=None):
    cases = {c['id']: c for c in plan['cases']}
    rows = []
    for call in plan['calls']:
        if phase and call['phase'] != phase: continue
        case_id, arm, _ = call['id'].split(':', 2)
        case = cases[case_id]
        checks = []
        for obligation, status in zip(case['item']['obligations'], case['oracle']['checks']):
            check = {'id': obligation['id'], 'status': status}
            if arm == 'v3':
                check['evidence'] = obligation['text'] if status == 'covered' else ''
            else:
                check['evidence_ids'] = [s['id'] for s in build_snapshot(case['item']['criteria'])['segments']
                                         if obligation['text'] in s['text']] if status == 'covered' else []
            checks.append(check)
        rows.append({'call_id': call['id'], 'prompt_sha256': call['prompt_sha256'],
                     'raw_response': json.dumps({'checks': checks})})
    return rows


def test_missing_records_and_pairs_are_not_dropped(tmp_path):
    plan = plan_fixture(tmp_path)
    report = api().audit_comparison(plan, [])
    assert report['totals']['planned'] == report['totals']['missing'] == 144
    assert report['totals']['observed'] == report['totals']['valid'] == 0
    assert sum(p['planned_pairs'] for p in report['paired']) == 72
    assert sum(p['neither_exact'] for p in report['paired']) == 72
    assert report['candidate_response_rules'] == {'development': 'not_met', 'evaluation': 'not_met'}


def test_complete_authored_answers_meet_response_rule_but_never_authorize_execution(tmp_path):
    plan = plan_fixture(tmp_path)
    report = api().audit_comparison(plan, responses(plan))
    assert report['totals']['planned'] == report['totals']['valid'] == report['totals']['exact_matches'] == 144
    assert report['candidate_response_rules'] == {'development': 'met_offline_only', 'evaluation': 'met_offline_only'}
    assert report['execution_authorized'] is report['main_collection_released'] is False
    assert report['provider_calls_dispatched'] == 0
    assert report['semantic_validity'] == 'not_measured'
    assert report['usage_cost_verified'] is False
    assert sum(p['both_exact'] for p in report['paired']) == 72
    assert len({s['source_group'] for s in report['strata']}) == 6
    assert len({s['project_group'] for s in report['strata']}) == 2
    assert len({s['operation'] for s in report['strata']}) == 6
    public = json.dumps(report)
    for value in ('openai', 'deepseek', 'The service', 'prompt_sha256', 'raw_response', 'seg-', str(tmp_path)):
        assert value not in public


def test_schema_failure_explicit_missing_and_wrong_labels_have_distinct_counts(tmp_path):
    plan = plan_fixture(tmp_path)
    rows = responses(plan)
    rows[0]['raw_response'] = 'PRIVATE not JSON'
    rows[1]['raw_response'] = None
    raw = json.loads(rows[2]['raw_response'])
    raw['checks'][0]['status'] = 'uncertain'
    rows[2]['raw_response'] = json.dumps(raw)
    report = api().audit_comparison(plan, rows)
    totals = report['totals']
    assert (totals['planned'], totals['observed'], totals['valid'], totals['invalid'], totals['missing']) == (144, 143, 142, 1, 1)
    assert totals['exact_matches'] == 141
    assert sum(p['unscorable_pairs'] for p in report['paired']) == 2
    assert sum(p['only_v4_exact'] for p in report['paired']) == 1
    assert report['candidate_response_rules']['development'] == 'not_met'


def test_aggregate_omission_can_match_while_exact_vector_fails_gate(tmp_path):
    plan = plan_fixture(tmp_path)
    rows = responses(plan)
    cases = {c['id']: c for c in plan['cases']}
    for row in rows:
        case_id, arm, _ = row['call_id'].split(':', 2)
        if arm == 'v4' and cases[case_id]['oracle']['operation'] == 'long_omission':
            raw = json.loads(row['raw_response'])
            raw['checks'][0]['status'] = 'uncertain'
            row['raw_response'] = json.dumps(raw)
    report = api().audit_comparison(plan, rows)
    assert report['totals']['aggregate_matches'] == 144
    assert report['totals']['exact_matches'] == 132
    assert report['candidate_response_rules']['development'] == 'not_met'


def test_evaluation_rule_never_passes_without_development_records(tmp_path):
    plan = plan_fixture(tmp_path)
    report = api().audit_comparison(plan, responses(plan, 'evaluation'))
    assert report['totals']['exact_matches'] == 96
    assert report['candidate_response_rules']['evaluation'] == 'not_met'


@pytest.mark.parametrize('mutation', ['duplicate', 'unknown', 'prompt', 'extra', 'null', 'unhashable', 'rows_type'])
def test_invalid_observation_inventory_fails_instead_of_overwriting(tmp_path, mutation):
    plan = plan_fixture(tmp_path)
    rows = responses(plan)[:1]
    if mutation == 'duplicate': rows *= 2
    elif mutation == 'unknown': rows[0]['call_id'] = 'PRIVATE_unknown'
    elif mutation == 'prompt': rows[0]['prompt_sha256'] = '0' * 64
    elif mutation == 'extra': rows[0]['answer'] = 'covered'
    elif mutation == 'null': rows = [None]
    elif mutation == 'unhashable': rows[0]['call_id'] = []
    elif mutation == 'rows_type': rows = {}
    with pytest.raises(ValueError, match='invalid_observations'):
        api().audit_comparison(plan, rows)


def test_invalid_v4_citation_counts_against_planned_and_gate(tmp_path):
    plan = plan_fixture(tmp_path)
    rows = responses(plan)
    row = next(r for r in rows if ':v4:' in r['call_id'])
    raw = json.loads(row['raw_response']); raw['checks'][0]['evidence_ids'] = ['PRIVATE-unknown']
    row['raw_response'] = json.dumps(raw)
    report = api().audit_comparison(plan, rows)
    assert report['totals']['invalid'] == 1
    assert report['first_error_counts'] == {'unknown_segment': 1}
    assert report['candidate_response_rules']['development'] == 'not_met'
