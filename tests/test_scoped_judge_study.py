"""Integration boundaries: custody, shared budget and phase gates, without APIs."""
import json

import pytest

from eval.pilot_ledger import PilotLedger, PilotStop, envelope
from eval.pilot_preparation import digest
from eval.provider_runtime_config import parse_provider_slot
from test_scoped_judge import seed


def api():
    from eval import scoped_judge_study
    return scoped_judge_study


def fixture(tmp_path, input_price='0.0002'):
    parent=tmp_path/'parent';parent.mkdir(parents=True)
    specs=[{'id':k,'kind':k,'model':k+'-model','model_version':'pinned',
            'api_key_env':'TEST_KEY','base_url':None if k=='openai' else 'https://api.deepseek.com',
            'pricing_snapshot_date':'2026-09-02','pricing_source_ref':'fixture',
            'pricing':{'input_usd_per_1k':input_price,'cached_input_usd_per_1k':'0.00002',
                       'output_usd_per_1k':'0.0012'}} for k in ('openai','deepseek')]
    prices={s['id']:parse_provider_slot(s).pricing for s in specs}
    calls=[{'id':k,'slot':k,'phase':'diagnostics','input_bound':100,'output_bound':100} for k in prices]
    launch={'schema_version':'pilot-run/v1','providers':specs,'calls':calls,
            'authorization':{'approved_cap_microusd':7_000_000,'exploratory_llm_scope_confirmed':True},
            'budget':envelope(calls,prices)}
    (parent/'launch.json').write_text(json.dumps(launch))
    # The production parent launch uses canonical JSON hashing, not file bytes.
    (parent/'launch-integrity.json').write_text(json.dumps({'sha256':digest(launch)}))
    (parent/'diagnostics.json').write_text('{"decision":"pause"}')
    with PilotLedger(parent/'ledger.jsonl',calls,prices,approval=True):pass
    seeds=[{**seed(f's{i}',str(i%2)), 'split':'development' if i<2 else 'evaluation'} for i in range(6)]
    return parent,seeds


def prepare(tmp_path):
    parent,seeds=fixture(tmp_path)
    run=tmp_path/'auxiliary'
    manifest=api().create_study(parent,seeds,run,approval=True)
    return parent,run,manifest


def factory(manifest,observed,*,wrong=False,missing_usage=False,wrong_operations=()):
    from label_plane.scoped_judge import build_prompt
    answers={}
    for case in manifest['cases']:
        for arm in ('v2','v3'):
            answers[build_prompt(case['item'],arm)]=(case,arm)
    class Provider:
        def __init__(self,slot,env):self.slot=slot
        def complete(self,request):
            observed.append(request)
            self.last_call_metadata={} if missing_usage else {
                'usage':{'input_tokens':100,'output_tokens':80,'cached_tokens':0,'total_tokens':180},
                'response_model':self.slot.model,'response_id':'fixture'}
            case,arm=answers[request.prompt]
            status=case['oracle']['status']
            if arm=='v2':return json.dumps({'status':status,'label':{
                'covered':'clean','omitted':'moderate','uncertain':'not_visible'}[status],
                'evidence':case['item']['criteria'][:50] if status=='covered' else ''})
            return json.dumps({'checks':[{'id':o['id'],'status':'uncertain' if wrong or case['oracle']['operation'] in wrong_operations else s,
                'evidence':o['text'][:80] if s=='covered' else ''}
                for o,s in zip(case['item']['obligations'],case['oracle']['checks'])]})
    return Provider


def test_study_freezes_144_calls_inside_shared_cap_before_dispatch(tmp_path):
    parent,run,manifest=prepare(tmp_path)
    assert len(manifest['calls'])==144
    assert manifest['budget']['auxiliary_reserved_microusd']<=1_000_000
    assert manifest['budget']['combined_reserved_microusd']<=7_000_000
    assert api().report(run)['main_pilot_released'] is False
    assert not (run/'responses.jsonl').exists()
    with pytest.raises(FileExistsError):api().create_study(parent,manifest['seeds'],tmp_path/'again',approval=True)


def test_missing_approval_and_overbudget_block_before_output(tmp_path):
    parent,seeds=fixture(tmp_path)
    with pytest.raises(ValueError):api().create_study(parent,seeds,tmp_path/'bad',approval=False)
    assert not (tmp_path/'bad').exists()
    parent,seeds=fixture(tmp_path/'expensive',input_price='1')
    with pytest.raises(ValueError):api().create_study(parent,seeds,tmp_path/'too-big',approval=True)
    assert not (tmp_path/'too-big').exists()


def test_evaluation_cannot_start_before_valid_development(tmp_path):
    _,run,manifest=prepare(tmp_path)
    with pytest.raises(ValueError,match='development'):
        api().run_phase(run,'evaluation',provider_factory=lambda *args:pytest.fail('premature provider'))
    observed=[]
    result=api().run_phase(run,'development',provider_factory=factory(manifest,observed,wrong=True))
    assert result['phases']['development']['decision']=='pause'
    with pytest.raises(ValueError,match='development'):
        api().run_phase(run,'evaluation',provider_factory=lambda *args:pytest.fail('failed gate bypass'))
    assert len(observed)==48


def test_successful_phase_and_resume_do_not_repurchase_or_rewrite_parent(tmp_path):
    parent,run,manifest=prepare(tmp_path)
    before=(parent/'ledger.jsonl').read_bytes()
    observed=[]; provider=factory(manifest,observed)
    api().run_phase(run,'development',provider_factory=provider)
    result=api().run_phase(run,'evaluation',provider_factory=provider)
    assert result['phases']['evaluation']['decision']=='pass_auxiliary_only'
    assert len(observed)==144
    api().run_phase(run,'development',provider_factory=provider)
    assert len(observed)==144
    assert (parent/'ledger.jsonl').read_bytes()==before
    assert result['main_pilot_released'] is False


def test_partial_contradictions_cannot_be_hidden_by_good_aggregate_accuracy(tmp_path):
    _,run,manifest=prepare(tmp_path)
    result=api().run_phase(run,'development',provider_factory=factory(
        manifest,[],wrong_operations=('partial_contradiction',)))
    assert result['phases']['development']['decision']=='pause'


@pytest.mark.parametrize('target',['seeds','ledger','source','environment','parent'])
def test_changed_custody_blocks_before_provider(tmp_path,monkeypatch,target):
    parent,run,_=prepare(tmp_path);p=api()
    if target=='seeds':(run/'manifest.json').write_text('{}')
    if target=='ledger':(run/'ledger.jsonl').unlink()
    if target=='source':monkeypatch.setattr(p,'source_hashes',lambda:{})
    if target=='environment':monkeypatch.setattr(p,'environment',lambda:{})
    if target=='parent':(parent/'diagnostics.json').write_text('{"decision":"continue"}')
    with pytest.raises((ValueError,PilotStop)):
        p.run_phase(run,'development',provider_factory=lambda *args:pytest.fail('unfrozen dispatch'))


def test_unverifiable_cost_retains_reservation_and_never_retries(tmp_path):
    _,run,manifest=prepare(tmp_path); observed=[]
    with pytest.raises(PilotStop):
        api().run_phase(run,'development',provider_factory=factory(manifest,observed,missing_usage=True))
    with pytest.raises(PilotStop):
        api().run_phase(run,'development',provider_factory=factory(manifest,observed))
    assert len(observed)==1
    assert 'observation' in (run/'ledger.jsonl').read_text()
    result=api().report(run)
    assert result['ledger']['pending_count']==1
    assert result['phases']['development']['decision']=='pause'
