import copy
import json
from pathlib import Path
import pytest
from eval.temporal_warning_readiness import assess, main

ROOT=Path(__file__).resolve().parents[1]

def candidate():
    return json.loads((ROOT/'data/prepilot/temporal-warning-plan.candidate.json').read_text())


def declared():
    p=candidate();p['selection_frozen']=p['split_frozen']=True
    p['project_split']={'strictdoc':'train','CASS':'train','todomvc':'train','realworld':'calibration','kanboard':'test','paperless-ngx':'test'}
    p['independent_human_reviews']=[{'intent_id':i,'source_manifest_sha256':p['candidate_source_manifest']['sha256'],'mapping_approved':True,'manipulation_approved':True,'rights_approved':True,'prior_exposure_and_residual_cues_reviewed':True,'independent_of_author':True,'reviewer_id':'synthetic-test-reviewer'} for i in p['selected_requirements']]
    p['qualified_provider_configurations']=[{'provider':provider,'model':'fixture','model_version':'fixture','mode':'runtime','checkpoint_source':'runtime_native','qualification_passed':True,'t1_t3_before_t4':True,'prompted_snapshot':False,'configuration_hash':'a'*64,'qualification_report_sha256':'b'*64,'qualification_report_path':'synthetic-test-only'} for provider in ['provider-a','provider-b']]
    for field in ['rubric_frozen','annotation_blinding_verified','independent_annotators_ready','prefix_clock_and_collector_qualified','feature_and_score_policy_frozen','schedule_frozen','launch_authorized']:p[field]=True
    p['budget']={'estimated_provider_cost_usd':1,'contingency_fraction':.25,'approved_cap_usd':2}
    return p


def test_live_candidate_is_no_go_not_a_120_episode_gate():
    p=candidate();r=assess(p,ROOT)
    assert r['decision']=='no_go' and r['planned_episodes']==144
    assert len(r['blockers'])==12
    assert r['reviewed_intents']==r['qualified_distinct_providers']==0
    assert p['historical_launch_gate_reference'].endswith('launch-plan.candidate.json')


def test_declarations_never_authorize_collection_or_confirmatory_claims():
    r=assess(declared(),ROOT)
    assert r['decision']=='prerequisites_declared'
    assert r['collection_authorized_by_this_report'] is False
    assert r['confirmatory_eligible'] is False


@pytest.mark.parametrize('field',['selection_frozen','split_frozen','rubric_frozen','annotation_blinding_verified','independent_annotators_ready','prefix_clock_and_collector_qualified','feature_and_score_policy_frozen','schedule_frozen','launch_authorized'])
def test_each_pending_prerequisite_keeps_no_go(field):
    p=declared();p[field]=False
    assert assess(p,ROOT)['decision']=='no_go'


@pytest.mark.parametrize('change',['same_provider_alias','prompted_snapshot','future_boundary','unqualified','review_hash','author_review','missing_intent','split_overlap','budget_nan','budget_exceeded'])
def test_invalid_receipts_and_design_boundaries_fail_closed(change):
    p=declared()
    if change=='same_provider_alias':p['qualified_provider_configurations'][1]['provider']=' PROVIDER-A '
    elif change=='prompted_snapshot':p['qualified_provider_configurations'][1]['prompted_snapshot']=True
    elif change=='future_boundary':p['qualified_provider_configurations'][1]['t1_t3_before_t4']=False
    elif change=='unqualified':p['qualified_provider_configurations'][1]['qualification_passed']=False
    elif change=='review_hash':p['independent_human_reviews'][0]['source_manifest_sha256']='bad'
    elif change=='author_review':p['independent_human_reviews'][0]['independent_of_author']=False
    elif change=='missing_intent':p['independent_human_reviews'].pop()
    elif change=='split_overlap':p['project_split']['realworld']='test'
    elif change=='budget_nan':p['budget']['approved_cap_usd']=float('nan')
    elif change=='budget_exceeded':p['budget']['approved_cap_usd']=.1
    assert assess(p,ROOT)['decision']=='no_go'


def test_source_hash_cannot_be_replaced_by_a_status_flag():
    p=declared();p['candidate_source_manifest']['sha256']='0'*64
    with pytest.raises(ValueError,match='hash mismatch'):assess(p,ROOT)


def test_cli_preserves_report_while_returning_nonzero_for_no_go(tmp_path,monkeypatch):
    monkeypatch.chdir(ROOT);out=tmp_path/'readiness.json'
    assert main(['--output',str(out)])==2
    assert json.loads(out.read_text())['decision']=='no_go'
