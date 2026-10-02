import copy
import pytest
from eval.temporal_comparison_report import compare, DETECTORS


def sample():
    predictions=[]; outcomes=[]
    for split, project in [('calibration','cal'),('test','test-1'),('test','test-2')]:
        for label in [0,1]:
            identifier=f'{project}-{label}'
            predictions.append({'episode_id':identifier,'project_id':project,'intent_id':identifier,
                                'run_id':'run','replication_id':'rep-1','constraint_id':identifier+'-c01','split':split,
                                'stages':[{'stage':stage,'available_ms':i+1,'scores':{d:.9 if label else .1 for d in DETECTORS}} for i,stage in enumerate(['T1','T2','T3'])]})
            outcomes.append({'episode_id':identifier,'constraint_id':identifier+'-c01','terminal_defect':label,'terminal_ms':10})
    return predictions,outcomes


def test_same_episodes_project_grouped_comparison_and_leadtime():
    p,o=sample(); r=compare(p,o,max_fpr=.05)
    assert r['test_episodes']==4 and r['test_projects']==2
    for d in DETECTORS:
        assert r['detectors'][d]['recall']==1 and r['detectors'][d]['fpr']==0
        positive=next(e for e in r['detectors'][d]['episodes'] if e['terminal_defect'])
        assert positive['first_alert_stage']=='T1' and positive['lead_time_ms']==9
    assert r['project_grouped_deltas']['B3_minus_B0']['claim']=='descriptive_only'
    assert r['confirmatory_eligible'] is False


def test_episode_budget_does_not_accumulate_three_stage_false_alarms():
    p,o=sample()
    # Three different calibration negatives exceed .9 in different checkpoints.
    p=[r for r in p if not (r['split']=='calibration' and r['episode_id']=='cal-0')]
    o=[r for r in o if r['episode_id']!='cal-0']
    template=copy.deepcopy(p[0])
    for i in range(3):
        row=copy.deepcopy(template);row['episode_id']=row['intent_id']=f'negative-{i}'
        for j,s in enumerate(row['stages']):s['scores']={d:.95 if i==j else .1 for d in DETECTORS}
        p.append(row);o.append({'episode_id':row['episode_id'],'constraint_id':row['constraint_id'],'terminal_defect':0,'terminal_ms':10})
    r=compare(p,o,max_fpr=1/3)
    assert all(r['detectors'][d]['policy']['threshold'] is None for d in DETECTORS)
    assert all(r['detectors'][d]['policy']['fpr']==0 for d in DETECTORS)


@pytest.mark.parametrize('change', ['project_overlap','project_alias','intent_overlap','future','nonmonotonic','missing_stage','missing_detector','duplicate','unknown_label','unmatched_label','constraint_mismatch','identity_feature'])
def test_invalid_cohort_fails_closed(change):
    p,o=sample()
    if change=='project_overlap':p[2]['project_id']='cal'
    elif change=='project_alias':p[2]['project_id']=' CAL '
    elif change=='intent_overlap':p[2]['intent_id']='cal-1'
    elif change=='future':p[2]['stages'][2]['available_ms']=10
    elif change=='nonmonotonic':p[2]['stages'][1]['available_ms']=.5
    elif change=='missing_stage':p[2]['stages'].pop()
    elif change=='missing_detector':p[2]['stages'][0]['scores'].pop('B3')
    elif change=='duplicate':p.append(copy.deepcopy(p[2]))
    elif change=='unknown_label':o[2]['terminal_defect']=None
    elif change=='unmatched_label':o.pop()
    elif change=='constraint_mismatch':o[2]['constraint_id']='other'
    elif change=='identity_feature':p[2]['stages'][0]['scores']['project_id']='leak'
    with pytest.raises(ValueError):compare(p,o,max_fpr=.05)


def test_test_outcomes_do_not_change_fitted_operating_point():
    p,o=sample();before=compare(p,o,max_fpr=.05)
    for row in o:
        if row['episode_id'].startswith('test'):row['terminal_defect']=1-row['terminal_defect']
    after=compare(p,o,max_fpr=.05)
    for d in DETECTORS:assert before['detectors'][d]['policy']==after['detectors'][d]['policy']
