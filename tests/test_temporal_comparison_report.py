import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import pytest
from eval.temporal_comparison_report import compare, DETECTORS

ROOT=Path(__file__).resolve().parents[1]


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


@pytest.mark.parametrize('destination', ['existing_report','predictions','outcomes','linked_predictions'])
def test_cli_preserves_existing_evidence(destination, tmp_path):
    p,o=sample()
    predictions=tmp_path/'predictions.json';outcomes=tmp_path/'outcomes.json'
    previous=tmp_path/'previous-report.json'
    predictions.write_text(json.dumps(p));outcomes.write_text(json.dumps(o))
    previous.write_bytes(b'previous evidence must remain unchanged\n')
    originals={path:path.read_bytes() for path in (predictions,outcomes,previous)}
    output={'existing_report':previous,'predictions':predictions,'outcomes':outcomes}.get(destination)
    if destination == 'linked_predictions':
        output=tmp_path/'linked.json';output.symlink_to(predictions)
    result=subprocess.run([sys.executable,'-m','eval.temporal_comparison_report',
                           '--predictions',str(predictions),'--outcomes',str(outcomes),
                           '--max-fpr','0.05','--output',str(output)],
                          cwd=ROOT,capture_output=True,text=True)
    assert result.returncode != 0
    assert {path:path.read_bytes() for path in originals} == originals


def test_cli_hashes_the_same_input_bytes_it_analyzed(tmp_path, monkeypatch):
    from eval import temporal_comparison_report as module
    p,o=sample()
    predictions=tmp_path/'predictions.json';outcomes=tmp_path/'outcomes.json'
    output=tmp_path/'report.json'
    original={predictions:json.dumps(p).encode()+b'\n',outcomes:json.dumps(o).encode()+b'\n'}
    for path,data in original.items():path.write_bytes(data)
    real_compare=module.compare
    def compare_then_change_files(*args, **kwargs):
        result=real_compare(*args, **kwargs)
        # Simulate input files changing after analysis, before export.
        for path,data in original.items():path.write_bytes(b'\n'+data)
        return result
    monkeypatch.setattr(module,'compare',compare_then_change_files)
    assert module.main(['--predictions',str(predictions),'--outcomes',str(outcomes),
                        '--max-fpr','0.05','--output',str(output)]) == 0
    report=json.loads(output.read_bytes())
    assert report['test_episodes'] == 4
    assert report['input_sha256'] == {
        'predictions':hashlib.sha256(original[predictions]).hexdigest(),
        'outcomes':hashlib.sha256(original[outcomes]).hexdigest()}
    assert all(hashlib.sha256(path.read_bytes()).hexdigest() != report['input_sha256'][name]
               for name,path in [('predictions',predictions),('outcomes',outcomes)])


def test_same_episodes_project_grouped_comparison_and_leadtime():
    p,o=sample(); r=compare(p,o,max_fpr=.05)
    assert r['test_episodes']==4 and r['test_projects']==2
    for d in DETECTORS:
        assert r['detectors'][d]['recall']==1 and r['detectors'][d]['fpr']==0
        positive=next(e for e in r['detectors'][d]['episodes'] if e['terminal_defect'])
        assert positive['first_alert_stage']=='T1' and positive['lead_time_ms']==9
    assert r['project_grouped_deltas']['B3_minus_B0']['claim']=='descriptive_only'
    assert r['confirmatory_eligible'] is False


@pytest.mark.parametrize('mode', ['mixed', 'no_alerts'])
def test_operating_point_counts_and_precision_have_explicit_denominators(mode):
    p,o=sample()
    if mode == 'mixed':
        # One TP, FP, FN and TN among the four held-out episodes.
        for row in p:
            if row['split'] == 'test':
                score=.9 if row['project_id'] == 'test-1' else .1
                for stage in row['stages']:
                    stage['scores']={detector:score for detector in DETECTORS}
        expected={'true_positives':1,'false_positives':1,
                  'false_negatives':1,'true_negatives':1}
        precision=.5
    else:
        # Every calibration threshold with a true alert violates max_fpr=0.
        for row in p:
            if row['episode_id'] == 'cal-0':
                for stage in row['stages']:
                    stage['scores']={detector:.95 for detector in DETECTORS}
        expected={'true_positives':0,'false_positives':0,
                  'false_negatives':2,'true_negatives':2}
        precision=None
    report=compare(p,o,max_fpr=0)
    assert report['cohort_counts_by_split'] == {
        'calibration':{'episodes':2,'projects':1,'defective_episodes':1,
                       'nondefective_episodes':1,'defect_prevalence':.5},
        'test':{'episodes':4,'projects':2,'defective_episodes':2,
                'nondefective_episodes':2,'defect_prevalence':.5}}
    for detector in DETECTORS:
        result=report['detectors'][detector]
        assert result['confusion_counts'] == expected
        assert sum(result['confusion_counts'].values()) == 4
        assert result['precision'] == precision
        assert result['recall'] == (.5 if mode == 'mixed' else 0)
        assert result['fpr'] == (.5 if mode == 'mixed' else 0)
        assert result['policy_unit'] == 'episode_any_T1_T2_T3_alert'


def test_class_composition_uses_observed_counts_not_assumed_balance():
    p,o=sample()
    extra=copy.deepcopy(p[3]); outcome=copy.deepcopy(o[3])
    extra['episode_id']=extra['intent_id']='test-extra-positive'
    extra['constraint_id']='test-extra-positive-c01'
    outcome['episode_id']=extra['episode_id'];outcome['constraint_id']=extra['constraint_id']
    p.append(extra);o.append(outcome)
    report=compare(p,o,max_fpr=0)
    assert report['cohort_counts_by_split']['test'] == {
        'episodes':5,'projects':2,'defective_episodes':3,
        'nondefective_episodes':2,'defect_prevalence':.6}
    assert report['cohort_counts_by_split']['calibration']['episodes'] == 2
    for detector in DETECTORS:
        assert report['detectors'][detector]['confusion_counts'] == {
            'true_positives':3,'false_positives':0,'false_negatives':0,'true_negatives':2}


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


def test_project_aliases_within_test_cannot_inflate_bootstrap_clusters():
    p,o=sample();p[3]['project_id']=' TEST-1 '
    with pytest.raises(ValueError,match='bootstrap clusters'):compare(p,o,max_fpr=.05)


@pytest.mark.parametrize('alias', ['ｃａｌ', 'ℂal'])
def test_unicode_project_alias_cannot_cross_calibration_test(alias):
    p,o=sample()
    for row in p:
        if row['project_id'] == 'test-1':
            row['project_id']=alias
    with pytest.raises(ValueError,match='project aliases|crosses calibration/test'):
        compare(p,o,max_fpr=.05)


@pytest.mark.parametrize('alias', ['ｔｅｓｔ－１', 'test-１'])
def test_unicode_project_alias_cannot_manufacture_third_bootstrap_cluster(alias):
    p,o=sample(); p[3]['project_id']=alias
    with pytest.raises(ValueError,match='bootstrap clusters'):
        compare(p,o,max_fpr=.05)


def test_consistent_unicode_project_identity_preserves_grouped_results():
    p,o=sample(); before=compare(p,o,max_fpr=.05)
    for row in p:
        if row['project_id'] == 'test-1':
            row['project_id']='ｔｅｓｔ－１'
    after=compare(p,o,max_fpr=.05)
    assert after['test_projects'] == before['test_projects'] == 2
    assert after['project_grouped_deltas'] == before['project_grouped_deltas']
    assert after['project_grouped_deltas_by_stage'] == before['project_grouped_deltas_by_stage']


@pytest.mark.parametrize('test_projects', [2, 3])
def test_checkpoint_deltas_reveal_gain_hidden_by_max_prefix_score(test_projects):
    p,o=sample()
    if test_projects == 3:
        for label in (0, 1):
            row=copy.deepcopy(p[2+label]); outcome=copy.deepcopy(o[2+label])
            row['project_id']='test-3'
            row['episode_id']=row['intent_id']=f'test-3-{label}'
            row['constraint_id']=row['episode_id']+'-c01'
            outcome['episode_id']=row['episode_id']
            outcome['constraint_id']=row['constraint_id']
            p.append(row);o.append(outcome)
    # At T1 B0 cannot discriminate; it catches up at T2. The max-prefix
    # comparison therefore hides the earlier B3 advantage in this fixture.
    for row in p:
        row['stages'][0]['scores']['B0'] = .1
    report=compare(p,o,max_fpr=.05)
    assert report['project_grouped_deltas']['B3_minus_B0']['delta_pr_auc'] == 0
    by_stage=report['project_grouped_deltas_by_stage']
    assert list(by_stage) == ['T1','T2','T3']
    for stage, expected in [('T1',.5),('T2',0),('T3',0)]:
        assert set(by_stage[stage]) == {'B3_minus_B0','B3_minus_S-structure'}
        for baseline in ('B0','S-structure'):
            effect=by_stage[stage]['B3_minus_'+baseline]
            ap=lambda detector: report['detectors'][detector]['pr_auc_average_precision_by_stage'][stage]
            assert effect['delta_pr_auc'] == ap('B3')-ap(baseline)
            assert effect['bootstrap']['cluster_key'] == 'project_id'
            assert effect['bootstrap']['clusters'] == report['test_projects'] == test_projects
            if test_projects == 2:
                assert effect['claim'] == 'descriptive_only'
                assert effect['ci95'] == {'low':None,'high':None}
            else:
                assert effect['bootstrap']['valid_for_inference'] is True
                assert effect['bootstrap']['draws'] == 2000
                assert effect['ci95'] == {'low':effect['delta_pr_auc'],
                                         'high':effect['delta_pr_auc']}
        assert by_stage[stage]['B3_minus_B0']['delta_pr_auc'] == expected
    assert report['confirmatory_eligible'] is False
    assert report['primary_h2_unchanged'] is True
