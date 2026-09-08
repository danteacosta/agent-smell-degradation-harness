"""Live contract with authored adapters, real journals, parsers and budgets."""
import json

import pytest

from eval import scoped_judge_study as old
from eval.addressed_comparison_plan import prompt_for
from eval.pilot_ledger import PilotStop
from eval.pilot_preparation import digest
from test_addressed_comparison_audit import responses
from test_addressed_comparison_custody import prepared
from test_addressed_comparison_plan import snapshot


def api():
    from eval import addressed_comparison_live
    return addressed_comparison_live


def factory(plan, observed, *, wrong_v4=False, invalid_v3=False, missing_usage=False, crash=False):
    answers = {row['call_id']: row['raw_response'] for row in responses(plan)}
    cases = {c['id']: c for c in plan['cases']}
    lookup = {}
    for call in plan['calls']:
        case_id, arm, slot = call['id'].split(':', 2)
        lookup[(slot, prompt_for(cases[case_id]['item'], arm))] = (call['id'], arm)

    class Provider:
        def __init__(self, slot, env): self.slot = slot

        def complete(self, request):
            observed.append(request)
            if crash: raise KeyboardInterrupt
            self.last_call_metadata = {} if missing_usage else {
                'usage': {'input_tokens': 100, 'output_tokens': 80, 'cached_tokens': 0, 'total_tokens': 180},
                'response_model': self.slot.model, 'response_id': 'fixture'}
            identifier, arm = lookup[(self.slot.id, request.prompt)]
            if invalid_v3 and arm == 'v3': return 'PRIVATE-invalid'
            raw = json.loads(answers[identifier])
            if wrong_v4 and arm == 'v4': raw['checks'][0]['status'] = 'uncertain'
            return json.dumps(raw)
    return Provider


def test_both_phases_and_resume_preserve_custody_and_do_not_repurchase(tmp_path):
    _, _, directory, manifest = prepared(tmp_path)
    before = snapshot(tmp_path / 'old'); observed = []
    provider = factory(manifest['plan'], observed)
    first = api().run_phase(directory, 'development', approval=True, provider_factory=provider)
    assert first['phases']['development'] == 'pass_auxiliary_only'
    assert first['accounting']['reconciled_completions'] == 48
    assert first['accounting']['unattempted_calls'] == 96
    final = api().run_phase(directory, 'evaluation', approval=True, provider_factory=provider)
    assert final['phases']['evaluation'] == 'pass_auxiliary_only'
    assert final['audit']['totals']['exact_matches'] == 144
    assert final['main_collection_released'] is False
    assert final['semantic_validity'] == 'not_measured'
    assert final['audit']['usage_cost_verified'] is False
    api().run_phase(directory, 'development', approval=True, provider_factory=provider)
    api().run_phase(directory, 'evaluation', approval=True, provider_factory=provider)
    assert len(observed) == 144
    assert snapshot(tmp_path / 'old') == before
    assert final['accounting']['spent_microusd'] > 0
    assert final['accounting']['pending_attempts'] == 0
    public = json.dumps(final)
    for private in ('openai', 'deepseek', 'fixture', str(directory), 'ledger_head', 'prompt_sha256', 'raw_response'):
        assert private not in public


@pytest.mark.parametrize('development', ['missing', 'wrong', 'invalid_baseline'])
def test_evaluation_depends_on_receipts_and_v4_rule_not_saved_report(tmp_path, development):
    _, _, directory, manifest = prepared(tmp_path)
    observed = []
    provider = factory(manifest['plan'], observed, wrong_v4=development == 'wrong',
                       invalid_v3=development == 'invalid_baseline')
    if development != 'missing':
        api().run_phase(directory, 'development', approval=True, provider_factory=provider)
    (directory / 'development-report.json').write_text('{"decision":"pass_auxiliary_only"}')
    if development == 'invalid_baseline':
        result = api().run_phase(directory, 'evaluation', approval=True, provider_factory=provider)
        assert result['audit']['totals']['invalid'] == 72
        assert len(observed) == 144
    else:
        with pytest.raises(ValueError, match='development_gate_failed'):
            api().run_phase(directory, 'evaluation', approval=True, provider_factory=provider)
        assert len(observed) == (48 if development == 'wrong' else 0)


@pytest.mark.parametrize('kind', ['missing_usage', 'crash'])
def test_ambiguous_attempt_is_retained_and_never_retried(tmp_path, kind):
    _, _, directory, manifest = prepared(tmp_path); observed = []
    with pytest.raises((PilotStop, KeyboardInterrupt)):
        api().run_phase(directory, 'development', approval=True,
                        provider_factory=factory(manifest['plan'], observed, **{kind: True}))
    before = (directory / 'ledger.jsonl').read_bytes()
    with pytest.raises(PilotStop):
        api().run_phase(directory, 'development', approval=True,
                        provider_factory=factory(manifest['plan'], observed))
    assert len(observed) == 1 and (directory / 'ledger.jsonl').read_bytes() == before
    report = api().report(directory)
    assert report['accounting']['pending_attempts'] == 1
    assert report['accounting']['unattempted_calls'] == 143
    assert report['accounting']['active_reserved_microusd'] > 0
    assert report['accounting']['cost_complete_for_reserved_attempts'] is False
    assert report['phases']['development'] == 'pause'


@pytest.mark.parametrize('owner', ['parent', 'predecessor', 'successor'])
def test_writer_lock_blocks_before_provider(tmp_path, owner):
    parent, predecessor, directory, _ = prepared(tmp_path)
    target = {'parent': parent, 'predecessor': predecessor, 'successor': directory}[owner]
    with old.parent_lock(target), pytest.raises((ValueError, OSError, PilotStop)):
        api().run_phase(directory, 'development', approval=True,
                        provider_factory=lambda *args: pytest.fail('provider created under lock'))


def test_drift_between_calls_stops_before_next_provider_attempt(tmp_path):
    parent, _, directory, manifest = prepared(tmp_path); observed = []
    def progress(_): (parent / 'diagnostics.json').write_text('{}')
    with pytest.raises(ValueError, match='custody_changed'):
        api().run_phase(directory, 'development', approval=True, progress=progress,
                        provider_factory=factory(manifest['plan'], observed))
    assert len(observed) == 1


def test_missing_approval_never_creates_provider(tmp_path):
    _, _, directory, _ = prepared(tmp_path)
    with pytest.raises(ValueError, match='approval_required'):
        api().run_phase(directory, 'development', provider_factory=lambda *args: pytest.fail('unapproved'))


def test_deleted_ledger_is_not_a_new_budget(tmp_path):
    _, _, directory, _ = prepared(tmp_path)
    (directory / 'ledger.jsonl').unlink()
    with pytest.raises(ValueError): api().run_phase(directory, 'development', approval=True)
    assert not (directory / 'ledger.jsonl').exists()


def test_report_rejects_a_journal_changed_during_audit(tmp_path, monkeypatch):
    from eval.addressed_comparison_custody import prices_for
    from eval.pilot_ledger import PilotLedger
    _, _, directory, manifest = prepared(tmp_path)
    original = api().audit_comparison
    def concurrent_stop(plan, rows):
        result = original(plan, rows)
        with PilotLedger(directory / 'ledger.jsonl', plan['calls'], prices_for(plan), approval=True) as ledger:
            with pytest.raises(PilotStop): ledger.stop('test_concurrent_stop')
        return result
    monkeypatch.setattr(api(), 'audit_comparison', concurrent_stop)
    with pytest.raises(ValueError, match='journal_changed'): api().report(directory)


@pytest.mark.parametrize('target', ['prompt', 'model', 'observation', 'duplicate_observation'])
def test_replay_binds_each_paid_receipt_to_request_and_observation(tmp_path, target):
    _, _, directory, manifest = prepared(tmp_path)
    def after_one(_): raise KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        api().run_phase(directory, 'development', approval=True, progress=after_one,
                        provider_factory=factory(manifest['plan'], []))
    path = directory / 'ledger.jsonl'
    events = [json.loads(line) for line in path.read_text().splitlines()]
    for event in events:
        if target == 'prompt' and event['event'] == 'reserve': event['data']['prompt_sha256'] = '0' * 64
        if target == 'model' and event['event'] in ('reconcile', 'observation'):
            event['data']['response_model'] = 'PRIVATE-other-model'
        if target == 'observation' and event['event'] == 'observation': event['data']['response'] = 'PRIVATE-changed'
    if target == 'duplicate_observation':
        original = next(e for e in events if e['event'] == 'observation')
        events.insert(-1, json.loads(json.dumps(original)))
    head = '0' * 64
    for index, event in enumerate(events):
        event['index'] = index
        event['prev'] = head
        event['hash'] = digest({k: v for k, v in event.items() if k != 'hash'})
        head = event['hash']
    path.write_text(''.join(json.dumps(event) + '\n' for event in events))
    with pytest.raises(ValueError, match='invalid_provider_receipt'): api().report(directory)


def test_cost_report_distinguishes_frozen_pricing_from_billed_charge(tmp_path):
    _, _, directory, _ = prepared(tmp_path)
    report = api().report(directory)
    assert report['accounting']['cost_basis'] == 'verified_usage_at_frozen_rates_not_invoice'
    assert report['accounting']['invoice_reconciled'] is False
