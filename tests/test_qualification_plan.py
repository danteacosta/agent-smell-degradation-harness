"""Planning reads a frozen runtime and retains every earlier commitment."""
import copy
import json
import subprocess

import pytest

from eval import addressed_comparison_live, scoped_judge_study
from eval.pilot_ledger import PilotStop
from test_addressed_comparison_custody import prepared
from test_addressed_comparison_live import factory
from test_addressed_comparison_plan import snapshot


def api():
    from eval import qualification_plan
    return qualification_plan


def failed_comparison(tmp_path, *, missing_usage=False, passing=False):
    parent, grandparent, directory, manifest = prepared(tmp_path)
    try:
        addressed_comparison_live.run_phase(directory, 'development', approval=True,
            provider_factory=factory(manifest['plan'], [], wrong_v4=not passing,
                                     missing_usage=missing_usage))
    except PilotStop:
        if not missing_usage:
            raise
    return parent, grandparent, directory


def make_plan(tmp_path):
    _, _, predecessor = failed_comparison(tmp_path)
    return api().prepare_plan(predecessor, scoped_judge_study.ROOT)


def test_plan_is_read_only_exactly_matched_and_has_new_identities(tmp_path):
    _, grandparent, predecessor = failed_comparison(tmp_path)
    before = snapshot(tmp_path)
    plan = api().prepare_plan(predecessor, scoped_judge_study.ROOT)
    assert snapshot(tmp_path) == before
    assert api().validate_plan(plan) == plan
    assert plan['candidate'] == 'v5' and plan['main_collection_released'] is False
    assert len(plan['cases']) == 36 and len(plan['calls']) == 144
    assert sum(c['phase']=='development' for c in plan['calls']) == 48
    assert sum(c['phase']=='evaluation' for c in plan['calls']) == 96
    assert {c['id'].split(':')[1] for c in plan['calls']} == {'v4','v5'}
    assert all(c['output_bound']==512 for c in plan['calls'])
    old = json.loads((predecessor/'manifest.json').read_text())['plan']
    assert not {c['id'] for c in old['cases']} & {c['id'] for c in plan['cases']}
    seeds = json.loads((grandparent/'manifest.json').read_text())['seeds']
    contexts = {s['source_intent_id']:s['context'] for s in seeds}
    for case in plan['cases']:
        if case['oracle']['operation'] in {'distributed_complete','long_omission'}:
            assert contexts[case['oracle']['source_intent_id']] in case['item']['criteria']
    assert plan['providers'] == old['providers']
    assert len(plan['case_lineage']) == 36


def test_budget_carries_ancestor_spending_and_releases_only_unused_predecessor(tmp_path):
    _, _, predecessor = failed_comparison(tmp_path)
    old = addressed_comparison_live.report(predecessor)
    plan = api().prepare_plan(predecessor, scoped_judge_study.ROOT)
    budget = plan['budget']
    released = old['budget']['remaining_direct_microusd'] + old['budget']['retained_contingency_microusd']
    assert budget['retained_shared_microusd'] == old['budget']['shared_committed_microusd']-released
    assert budget['retained_auxiliary_microusd'] == old['budget']['auxiliary_committed_microusd']-released
    assert budget['predecessor_spent_microusd'] == old['accounting']['spent_microusd']
    assert budget['earlier_unresolved_retained_microusd'] == 218
    current = api().check_budget(plan, 0, {})
    assert current['shared_committed_microusd'] == budget['retained_shared_microusd']+budget['new_envelope']['reserved_microusd']
    assert current['auxiliary_committed_microusd'] == budget['retained_auxiliary_microusd']+budget['new_envelope']['reserved_microusd']
    with pytest.raises(ValueError, match='budget_exceeded'): api().check_budget(plan,7_000_001,{})
    for amount in (-1,True,1.5):
        with pytest.raises(ValueError): api().check_budget(plan,amount,{})


@pytest.mark.parametrize('state', ['pending','passing','incomplete'])
def test_only_complete_failed_predecessor_can_be_closed(tmp_path,state):
    if state=='incomplete':
        _,_,predecessor,_=prepared(tmp_path)
    else:
        _,_,predecessor=failed_comparison(tmp_path,missing_usage=state=='pending',passing=state=='passing')
    before=snapshot(tmp_path)
    with pytest.raises(ValueError,match='predecessor_not_closable'):
        api().prepare_plan(predecessor,scoped_judge_study.ROOT)
    assert snapshot(tmp_path)==before


@pytest.mark.parametrize('field',['calls','cases','case_lineage','budget','source_sha256','environment','candidate'])
def test_frozen_plan_cannot_be_edited(tmp_path,field):
    plan=make_plan(tmp_path); altered=copy.deepcopy(plan)
    altered[field]=None
    with pytest.raises(ValueError): api().validate_plan(altered)


def test_predecessor_change_during_external_report_is_detected(tmp_path,monkeypatch):
    from eval import qualification_lineage
    _,_,predecessor=failed_comparison(tmp_path)
    original=subprocess.run
    def changed(*args,**kwargs):
        result=original(*args,**kwargs)
        path=predecessor/'manifest.json'; path.write_bytes(path.read_bytes()+b' ')
        return result
    monkeypatch.setattr(qualification_lineage.subprocess,'run',changed)
    with pytest.raises(ValueError,match='custody_changed'):
        api().prepare_plan(predecessor,scoped_judge_study.ROOT)


@pytest.mark.parametrize('fault',['timeout','invalid_json','oversized','nonzero','array','null'])
def test_bad_frozen_report_is_rejected_without_exposing_output(tmp_path,monkeypatch,fault):
    from eval import qualification_lineage
    _,_,predecessor=failed_comparison(tmp_path)
    def broken(*args,**kwargs):
        if fault=='timeout': raise subprocess.TimeoutExpired('PRIVATE',20)
        payload = {'array': b'[]', 'null': b'null'}.get(fault, b'PRIVATE')
        kwargs['stdout'].write(payload if fault!='oversized' else b'x'*(qualification_lineage.MAX_REPORT_BYTES+1))
        return subprocess.CompletedProcess(args[0],3 if fault=='nonzero' else 0)
    monkeypatch.setattr(qualification_lineage.subprocess,'run',broken)
    with pytest.raises(ValueError) as error:
        api().prepare_plan(predecessor,scoped_judge_study.ROOT)
    assert 'PRIVATE' not in str(error.value)


def test_report_subprocess_does_not_inherit_provider_keys(tmp_path,monkeypatch):
    from eval import qualification_lineage
    _,_,predecessor=failed_comparison(tmp_path)
    monkeypatch.setenv('PANEL_OPENAI_API_KEY','PRIVATE-key')
    original=subprocess.run
    def checked(*args,**kwargs):
        assert not any('KEY' in k or 'TOKEN' in k for k in kwargs['env'])
        assert kwargs['env']['PYTHONPATH'] == str(scoped_judge_study.ROOT)
        assert kwargs['timeout']<=30 and not kwargs.get('shell')
        assert args[0][1:4]==['-m','eval.addressed_comparison_live','report']
        return original(*args,**kwargs)
    monkeypatch.setattr(qualification_lineage.subprocess,'run',checked)
    assert api().prepare_plan(predecessor,scoped_judge_study.ROOT)['candidate']=='v5'


def test_wrong_or_symlink_runtime_is_rejected_before_subprocess(tmp_path,monkeypatch):
    from eval import qualification_lineage
    _,_,predecessor=failed_comparison(tmp_path)
    empty=tmp_path/'empty'; empty.mkdir()
    link=tmp_path/'link'; link.symlink_to(scoped_judge_study.ROOT,target_is_directory=True)
    monkeypatch.setattr(qualification_lineage.subprocess,'run',lambda *a,**k:pytest.fail('unverified runtime'))
    for root in (empty,link):
        with pytest.raises(ValueError): api().prepare_plan(predecessor,root)
