"""Pure scores never change the candidate, denominator or semantic authority."""
import json

import pytest

from label_plane import qualified_judge
from label_plane.artifact_segments import build_snapshot
from test_scoped_judge import seed


def api():
    from eval import qualification_audit
    return qualification_audit


def scoring_plan():
    seeds=[]
    for i in range(6):
        s=seed(f'PRIVATE-source-{i}',f'PRIVATE-project-{i%2}')
        s['split']='development' if i<2 else 'evaluation'
        seeds.append(s)
    cases=qualified_judge.build_cases(seeds)
    return {'cases':cases,'providers':[{'id':'PRIVATE-provider-a'},{'id':'PRIVATE-provider-b'}],
            'calls':[{'id':f'{c["id"]}:{a}:{p}', 'phase':c['oracle']['split'],'slot':p}
                     for c in cases for a in ('v4','v5') for p in ('PRIVATE-provider-a','PRIVATE-provider-b')]}


def answers(plan):
    cases={c['id']:c for c in plan['cases']}
    result={}
    for call in plan['calls']:
        case=cases[call['id'].split(':')[0]]
        ids=[s['id'] for s in build_snapshot(case['item']['criteria'])['segments']][:8]
        raw={'checks':[{'id':o['id'],'status':status,'evidence_ids':ids if status=='covered' else []}
                       for o,status in zip(case['item']['obligations'],case['oracle']['checks'])]}
        result[call['id']]={'response':json.dumps(raw)}
    return result


def test_both_phases_retain_all_denominators_and_do_not_claim_validity():
    plan=scoring_plan(); report=api().audit(plan,answers(plan))
    assert report['candidate_passed']=={'development':True,'evaluation':True}
    assert report['totals']=={'planned':144,'observed':144,'missing':0,'valid':144,'invalid':0,
                             'exact_matches':144,'aggregate_matches':144}
    assert report['usage_cost_verified'] is False
    assert report['semantic_validity']=='not_measured'
    assert report['main_collection_released'] is False
    assert all(row['both_valid_pairs']==row['planned_pairs'] for row in report['paired'])
    assert 'PRIVATE' not in json.dumps(report)


@pytest.mark.parametrize('phase',['development','evaluation'])
def test_one_required_omission_abstention_fails_candidate_despite_high_total(phase):
    plan=scoring_plan(); rows=answers(plan)
    case=next(c for c in plan['cases'] if c['oracle']['split']==phase and c['oracle']['operation']=='long_omission')
    identifier=f'{case["id"]}:v5:PRIVATE-provider-a'
    value=json.loads(rows[identifier]['response'])
    for check in value['checks']:
        if check['status']=='omitted': check['status']='uncertain'
    rows[identifier]['response']=json.dumps(value)
    report=api().audit(plan,rows)
    assert report['candidate_passed'][phase] is False
    assert report['candidate_passed']['evaluation'] is False
    assert report['totals']['exact_matches']==143 and report['totals']['valid']==144


def test_baseline_invalidity_does_not_change_primary_candidate_but_remains_visible():
    plan=scoring_plan(); rows=answers(plan)
    for key,value in rows.items():
        if ':v4:' in key: value['response']='PRIVATE-invalid'
    report=api().audit(plan,rows)
    assert report['totals']['invalid']==72
    assert report['candidate_passed']['evaluation'] is True
    assert sum(p['unscorable_pairs'] for p in report['paired'])==72
    assert sum(p['both_valid_pairs'] for p in report['paired'])==0


def test_missing_baseline_receipt_cannot_be_skipped_to_release_evaluation():
    plan=scoring_plan(); rows=answers(plan); rows.pop(plan['calls'][0]['id'])
    report=api().audit(plan,rows)
    assert report['totals']['missing']==1
    assert report['candidate_passed']=={'development':False,'evaluation':False}


def test_empty_receipts_and_empty_plan_do_not_pass_vacuously():
    plan=scoring_plan()
    assert not any(api().audit(plan,{})['candidate_passed'].values())
    assert not any(api().audit({'calls':[],'cases':[],'providers':[]},{})['candidate_passed'].values())


def test_jointly_valid_pairs_are_separate_from_planned_denominator_wins():
    plan=scoring_plan(); rows=answers(plan)
    rows[plan['calls'][0]['id']]['response']='invalid'
    report=api().audit(plan,rows)
    pair=report['paired'][0]
    assert pair['planned_pairs']==12
    assert pair['both_valid_pairs']==11
    assert pair['only_v5_exact']==1 and pair['both_valid_only_v5_exact']==0
