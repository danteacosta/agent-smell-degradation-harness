import json
import pytest

from test_pilot_runtime import inputs, fake_factory
from test_pilot_runtime import admit_fixture
from eval import pilot_runtime as p
from eval.pilot_ledger import PilotStop
from eval.pilot_preparation import write_preparation


def revised(package,output):
    seeds=p.read(package/'control-seeds.json')
    for s in seeds:s['seed_id']+='-review2'
    write_preparation(p.read(package/'corpus-candidates.json')['records'],seeds,
                      p.read(package/'natural-sample-with-history.json')['selected'],
                      p.read(package/'prices.json'),output)
    return output


def test_revision_carries_all_charges_and_reuses_only_identical_packets(tmp_path):
    package,specs,auth=inputs(tmp_path); old=tmp_path/'old'; new=tmp_path/'new'
    p.create_run(package,specs,auth,old); calls=[]
    p.run_phase(old,'screening',provider_factory=fake_factory(package,calls))
    before=p.preflight(old)['spent_microusd']
    updated=revised(package,tmp_path/'revised')
    run=p.revise_screening(old,updated,new)
    assert run['counts']['total_calls']==2760
    assert p.preflight(new)['spent_microusd']==before
    assert p.preflight(new)['completed_calls']==60
    with pytest.raises(PilotStop):p.run_phase(old,'screening',provider_factory=lambda s:pytest.fail('old budget active'))
    p.run_phase(new,'screening',provider_factory=fake_factory(updated,calls))
    assert len(calls)==72
    assert p.preflight(new)['completed_calls']==72
    assert p.preflight(new)['spent_microusd']>before
    assert run['budget']['approved_cap_microusd']==7000000


def test_revision_cannot_discard_a_pending_charge(tmp_path):
    package,specs,auth=inputs(tmp_path); old=tmp_path/'old'
    p.create_run(package,specs,auth,old)
    class Broken:
        name='fixture'
        def __init__(self,slot):pass
        def complete(self,request):raise TimeoutError()
    with pytest.raises(PilotStop):p.run_phase(old,'screening',provider_factory=Broken)
    with pytest.raises(PilotStop):p.revise_screening(old,revised(package,tmp_path/'revised'),tmp_path/'new')
    assert not (tmp_path/'new').exists()


def test_revision_is_forbidden_after_diagnostic_outcomes(tmp_path):
    package,specs,auth=inputs(tmp_path); old=tmp_path/'old'
    run=p.create_run(package,specs,auth,old); factory=fake_factory(package,[])
    p.run_phase(old,'screening',provider_factory=factory); admit_fixture(old,run)
    p.run_phase(old,'diagnostics',provider_factory=factory)
    with pytest.raises(ValueError):p.revise_screening(old,revised(package,tmp_path/'revised'),tmp_path/'new')
    assert not (tmp_path/'new').exists()


def test_successor_requires_a_durably_stopped_predecessor(tmp_path):
    package,specs,auth=inputs(tmp_path); old=tmp_path/'old'; new=tmp_path/'new'
    p.create_run(package,specs,auth,old); p.run_phase(old,'screening',provider_factory=fake_factory(package,[]))
    original=(old/'ledger.jsonl').read_text()
    p.revise_screening(old,revised(package,tmp_path/'revised'),new)
    (old/'ledger.jsonl').write_text(original)
    with pytest.raises(ValueError):p.run_phase(new,'screening',provider_factory=lambda s:pytest.fail('two active budgets'))


def test_changed_corpus_is_not_a_screening_only_revision(tmp_path):
    package,specs,auth=inputs(tmp_path); old=tmp_path/'old'
    p.create_run(package,specs,auth,old)
    p.run_phase(old,'screening',provider_factory=fake_factory(package,[]))
    updated=revised(package,tmp_path/'revised')
    records=p.read(updated/'corpus-candidates.json')
    records['records'][0]['source_locator']='changed'
    (updated/'corpus-candidates.json').write_text(json.dumps(records))
    with pytest.raises(ValueError):p.revise_screening(old,updated,tmp_path/'new')
    assert not (tmp_path/'new').exists()
