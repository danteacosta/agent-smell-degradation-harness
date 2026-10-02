import copy
import json
from pathlib import Path
import pytest
from eval.temporal_cohort_candidate import validate_candidate, audit

ROOT=Path(__file__).resolve().parents[1]

def candidate():
    return json.loads((ROOT/'data/prepilot/temporal-warning-source-drafts.json').read_text())


def test_twelve_draft_pairs_have_exact_source_and_license_hashes():
    assert validate_candidate(candidate(),ROOT)=={'pairs_verified':12,'projects':6}


@pytest.mark.parametrize('change',['source_hash','license_hash','wrong_excerpt','different_deletion','constraint_id','duplicate','false_approval','false_freeze'])
def test_tampering_and_invented_review_are_rejected(change):
    c=candidate();r=c['records'][0]
    if change=='source_hash':r['source']['sha256']='0'*64
    elif change=='license_hash':r['source']['license_sha256']='0'*64
    elif change=='wrong_excerpt':r['source']['start_char']+=1
    elif change=='different_deletion':r['variants']['defective']+=' extra change'
    elif change=='constraint_id':r['target']['constraint_id']='other'
    elif change=='duplicate':c['records'].append(copy.deepcopy(r))
    elif change=='false_approval':c['human_approvals']=1
    elif change=='false_freeze':c['selection_frozen']=True
    with pytest.raises(ValueError):validate_candidate(c,ROOT)


def test_prior_input_match_is_reported_without_granting_prospective_status(tmp_path):
    c=candidate()
    for r in c['records']:
        for key in ['path','license_path']:
            relative=r['source'][key];destination=tmp_path/relative
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes((ROOT/relative).read_bytes())
    (tmp_path/'prior.json').write_text(json.dumps({'requirement_text':'  '+c['records'][0]['variants']['clean'].replace('\n',' ')+'  '}))
    report=audit(c,tmp_path,['prior.json'])
    assert report['exact_or_contained_clean_input_matches'][c['records'][0]['intent_id']]==['prior.json']
    assert report['unmatched_is_not_unexposed'] is True
    assert report['confirmatory_eligible'] is False
    assert report['inventory'][0]['input_strings']==1
