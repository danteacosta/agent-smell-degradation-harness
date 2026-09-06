import importlib.util
import json
from pathlib import Path

import pytest

from agents.providers import ProviderRequest
from eval.exploratory_cost import ProviderPricing


def api():
    assert importlib.util.find_spec('eval.pilot_ledger'), 'pilot ledger is missing'
    from eval import pilot_ledger
    return pilot_ledger


def prices():
    return {s: ProviderPricing(s, s+'-model', 'pinned', '2026-09-02', 'frozen-source',
                               '0.001', '0.0001', '0.003') for s in ('a', 'b')}


def plan():
    return [{'id':s, 'slot':s, 'phase':'screening', 'input_bound':1000, 'output_bound':100} for s in ('a','b')]


class Provider:
    def __init__(self, *, missing=False, error=False, wrong_model=False):
        self.calls=0
        self.last_call_metadata={'usage':{'input_tokens':100,'output_tokens':10}}
        self.missing=missing
        self.error=error
        self.wrong_model=wrong_model

    def complete(self, request):
        self.calls += 1
        if self.error: raise TimeoutError('uncertain provider outcome')
        if not self.missing:
            self.last_call_metadata={'usage':{'input_tokens':100,'output_tokens':10,'cached_tokens':0},
                                     'response_model':'wrong' if self.wrong_model else 'a-model', 'response_id':'id1'}
        return '{"ok":true}'


def test_reserved_before_dispatch_reconciled_and_reusable_without_second_call(tmp_path):
    p=api(); path=tmp_path/'ledger.jsonl'
    provider=Provider()
    request=ProviderRequest('json',{},'opaque','screening',100)
    with p.PilotLedger(path,plan(),prices(),approval=True) as ledger:
        assert ledger.complete('a',provider,request)=='{"ok":true}'
        assert ledger.report()['spent_microusd']==130
        assert ledger.report()['pending_count']==0
    with p.PilotLedger(path,plan(),prices(),approval=True) as ledger:
        assert ledger.complete('a',provider,request)=='{"ok":true}'
        assert provider.calls==1
    events=[json.loads(x) for x in path.read_text().splitlines()]
    assert [e['event'] for e in events]==['plan','reserve','observation','reconcile']


@pytest.mark.parametrize('failure', ['missing','error','wrong_model'])
def test_unverified_charge_stops_and_preserves_reservation_without_retry(tmp_path,failure):
    p=api(); path=tmp_path/'ledger.jsonl'; provider=Provider(**{failure:True})
    with p.PilotLedger(path,plan(),prices(),approval=True) as ledger:
        with pytest.raises(p.PilotStop): ledger.complete('a',provider,ProviderRequest('json',{},'opaque','screening',100))
        assert provider.calls==1
        assert ledger.report()['pending_count']==1
        if failure != 'error':
            assert '{\\"ok\\":true}' in path.read_text()
        with pytest.raises(p.PilotStop): ledger.complete('a',provider,ProviderRequest('json',{},'opaque','screening',100))
    with pytest.raises(p.PilotStop): p.PilotLedger(path,plan(),prices(),approval=True)


def test_unapproved_and_overbudget_plan_never_dispatch(tmp_path):
    p=api()
    with pytest.raises(ValueError): p.PilotLedger(tmp_path/'a',plan(),prices(),approval=False)
    big=[{**c,'input_bound':10_000_000} for c in plan()]
    with pytest.raises(ValueError): p.PilotLedger(tmp_path/'b',big,prices(),approval=True)


def test_prompt_limit_and_unknown_call_rejected_before_api(tmp_path):
    p=api(); provider=Provider()
    with p.PilotLedger(tmp_path/'ledger',plan(),prices(),approval=True) as ledger:
        with pytest.raises(p.PilotStop): ledger.complete('a',provider,ProviderRequest('x'*1001,{},'opaque','screening',100))
        assert provider.calls==0


def test_changed_plan_and_corrupt_journal_cannot_reset_budget(tmp_path):
    p=api(); path=tmp_path/'ledger'
    with p.PilotLedger(path,plan(),prices(),approval=True): pass
    changed=[{**c,'input_bound':1001} for c in plan()]
    with pytest.raises(p.PilotStop): p.PilotLedger(path,changed,prices(),approval=True)
    path.write_text(path.read_text().replace('1000','1001',1))
    with pytest.raises(p.PilotStop): p.PilotLedger(path,plan(),prices(),approval=True)


def test_only_one_writer_can_own_the_pilot_budget(tmp_path):
    p=api(); path=tmp_path/'ledger'
    with p.PilotLedger(path,plan(),prices(),approval=True):
        with pytest.raises(p.PilotStop): p.PilotLedger(path,plan(),prices(),approval=True)


def test_reconciled_call_cannot_be_reused_for_changed_prompt(tmp_path):
    p=api(); provider=Provider()
    with p.PilotLedger(tmp_path/'ledger',plan(),prices(),approval=True) as ledger:
        ledger.complete('a',provider,ProviderRequest('json',{},'opaque','screening',100))
        with pytest.raises(p.PilotStop): ledger.complete('a',provider,ProviderRequest('different json',{},'opaque','screening',100))
        assert provider.calls==1
