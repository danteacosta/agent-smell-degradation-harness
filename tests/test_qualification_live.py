"""Verified receipts, rather than saved verdicts, control sequential collection."""
import json
from collections import defaultdict, deque
from pathlib import Path

import pytest

from eval import scoped_judge_study as historical
from eval.pilot_ledger import PilotStop
from eval.pilot_preparation import digest
from label_plane.qualified_judge import build_prompt
from test_addressed_comparison_plan import snapshot
from test_qualification_audit import answers
from test_qualification_custody import prepared_qualification
from test_qualification_plan import make_plan


def api():
    from eval import qualification_live
    return qualification_live


def factory(plan, observed, *, wrong_phase=None, invalid_baseline=False, missing_usage=False, crash=False):
    responses = answers(plan)
    cases = {c['id']: c for c in plan['cases']}
    lookup = defaultdict(deque)
    for call in plan['calls']:
        case, arm, slot = call['id'].split(':', 2)
        lookup[(slot, build_prompt(cases[case]['item'], arm))].append(call)

    class Provider:
        def __init__(self, slot, env): self.slot = slot

        def complete(self, request):
            observed.append(request)
            if crash: raise KeyboardInterrupt
            self.last_call_metadata = {} if missing_usage else {
                'usage': {'input_tokens': 100, 'output_tokens': 80, 'cached_tokens': 0, 'total_tokens': 180},
                'response_model': self.slot.model, 'response_id': 'PRIVATE-fixture'}
            call = lookup[(self.slot.id, request.prompt)].popleft()
            arm = call['id'].split(':')[1]
            if invalid_baseline and arm == 'v4': return 'PRIVATE-invalid'
            raw = json.loads(responses[call['id']]['response'])
            if wrong_phase == call['phase'] and arm == 'v5': raw['checks'][0]['status'] = 'uncertain'
            return json.dumps(raw)
    return Provider


def test_full_collection_and_resume_do_not_repurchase_or_release_main(tmp_path):
    directory, manifest = prepared_qualification(tmp_path)
    before = snapshot(tmp_path/'old'); observed = []
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
    assert final['accounting']['spent_microusd'] > 0
    assert final['accounting']['pending_attempts'] == 0
    assert final['accounting']['invoice_reconciled'] is False
    for phase in ('development', 'evaluation'):
        api().run_phase(directory, phase, approval=True, provider_factory=provider)
    assert len(observed) == 144 and snapshot(tmp_path/'old') == before
    for private in ('openai', 'deepseek', 'PRIVATE', str(directory), 'ledger_head', 'sha256', 'raw_response'):
        assert private not in json.dumps(final)


@pytest.mark.parametrize('state', ['missing', 'failed', 'invalid_baseline'])
def test_evaluation_uses_receipts_and_candidate_rule_not_forged_report(tmp_path, state):
    directory, manifest = prepared_qualification(tmp_path); observed = []
    provider = factory(manifest['plan'], observed, wrong_phase='development' if state == 'failed' else None,
                       invalid_baseline=state == 'invalid_baseline')
    if state != 'missing': api().run_phase(directory, 'development', approval=True, provider_factory=provider)
    (directory/'development-report.json').write_text('{"decision":"pass_auxiliary_only"}')
    if state == 'invalid_baseline':
        result = api().run_phase(directory, 'evaluation', approval=True, provider_factory=provider)
        assert result['audit']['totals']['invalid'] == 72 and len(observed) == 144
    else:
        with pytest.raises(ValueError, match='development_gate_failed'):
            api().run_phase(directory, 'evaluation', approval=True, provider_factory=provider)
        assert len(observed) == (48 if state == 'failed' else 0)


def test_failed_evaluation_remains_failed_without_retry(tmp_path):
    directory, manifest = prepared_qualification(tmp_path); observed = []
    provider = factory(manifest['plan'], observed, wrong_phase='evaluation')
    api().run_phase(directory, 'development', approval=True, provider_factory=provider)
    result = api().run_phase(directory, 'evaluation', approval=True, provider_factory=provider)
    assert result['phases'] == {'development': 'pass_auxiliary_only', 'evaluation': 'pause'}
    api().run_phase(directory, 'evaluation', approval=True, provider_factory=provider)
    assert len(observed) == 144


@pytest.mark.parametrize('kind', ['missing_usage', 'crash'])
def test_ambiguous_attempt_retains_reserve_and_cannot_be_retried(tmp_path, kind):
    directory, manifest = prepared_qualification(tmp_path); observed = []
    with pytest.raises((PilotStop, KeyboardInterrupt)):
        api().run_phase(directory, 'development', approval=True,
                        provider_factory=factory(manifest['plan'], observed, **{kind: True}))
    before = (directory/'ledger.jsonl').read_bytes()
    with pytest.raises(PilotStop):
        api().run_phase(directory, 'development', approval=True,
                        provider_factory=factory(manifest['plan'], observed))
    result = api().report(directory)
    assert len(observed) == 1 and (directory/'ledger.jsonl').read_bytes() == before
    assert result['accounting']['pending_attempts'] == 1
    assert result['accounting']['active_reserved_microusd'] > 0
    assert result['accounting']['cost_complete_for_reserved_attempts'] is False
    assert result['phases']['development'] == 'pause'


@pytest.mark.parametrize('owner', [0, 1, 2, 3])
def test_every_chain_owner_blocks_dispatch(tmp_path, owner):
    directory, manifest = prepared_qualification(tmp_path)
    lineage = manifest['plan']['lineage']
    target = [*lineage['ancestors'], lineage['directory'], str(directory)][owner]
    with historical.parent_lock(Path(target)), pytest.raises((ValueError, OSError, PilotStop)):
        api().run_phase(directory, 'development', approval=True,
                        provider_factory=lambda *args: pytest.fail('provider under lock'))


def test_changed_predecessor_between_calls_stops_before_second_attempt(tmp_path):
    directory, manifest = prepared_qualification(tmp_path); observed = []
    parent = Path(manifest['plan']['lineage']['ancestors'][0])
    def changed(_): (parent/'diagnostics.json').write_text('{}')
    with pytest.raises(ValueError, match='custody_changed'):
        api().run_phase(directory, 'development', approval=True, progress=changed,
                        provider_factory=factory(manifest['plan'], observed))
    assert len(observed) == 1


def test_no_approval_or_credentials_means_no_new_attempt(tmp_path):
    directory, _ = prepared_qualification(tmp_path); before = snapshot(tmp_path)
    with pytest.raises(ValueError, match='approval_required'): api().run_phase(directory, 'development')
    with pytest.raises(ValueError, match='missing_credentials'):
        api().run_phase(directory, 'development', approval=True, environ={})
    assert snapshot(tmp_path) == before


def test_deleted_journal_is_not_recreated(tmp_path):
    directory, _ = prepared_qualification(tmp_path); (directory/'ledger.jsonl').unlink()
    with pytest.raises(ValueError): api().run_phase(directory, 'development', approval=True)
    assert not (directory/'ledger.jsonl').exists()


@pytest.mark.parametrize('target', ['prompt', 'model', 'observation', 'duplicate_observation'])
def test_replay_rejects_rehashed_but_unbound_receipts(tmp_path, target):
    directory, manifest = prepared_qualification(tmp_path)
    def after_one(_): raise KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        api().run_phase(directory, 'development', approval=True, progress=after_one,
                        provider_factory=factory(manifest['plan'], []))
    path = directory/'ledger.jsonl'
    events = [json.loads(line) for line in path.read_text().splitlines()]
    for event in events:
        if target == 'prompt' and event['event'] == 'reserve': event['data']['prompt_sha256'] = '0'*64
        if target == 'model' and event['event'] in ('reconcile', 'observation'):
            event['data']['response_model'] = 'PRIVATE-other-model'
        if target == 'observation' and event['event'] == 'observation': event['data']['response'] = 'PRIVATE-changed'
    if target == 'duplicate_observation':
        events.insert(-1, next(e.copy() for e in events if e['event'] == 'observation'))
    head = '0'*64
    for index, event in enumerate(events):
        event['index'], event['prev'] = index, head
        event['hash'] = digest({k: v for k, v in event.items() if k != 'hash'})
        head = event['hash']
    path.write_text(''.join(json.dumps(e)+'\n' for e in events))
    with pytest.raises(ValueError, match='invalid_provider_receipt'): api().report(directory)


def test_cli_report_is_read_only_and_errors_never_print_private_input(tmp_path, capsys):
    directory, _ = prepared_qualification(tmp_path); before = snapshot(tmp_path)
    assert api().main(['report', '--directory', str(directory)]) == 0
    assert snapshot(tmp_path) == before
    assert json.loads(capsys.readouterr().out)['accounting']['reconciled_completions'] == 0
    assert api().main(['development', '--directory', str(directory)]) == 2
    assert json.loads(capsys.readouterr().out)['error'] == 'approval_required'
    assert api().main(['PRIVATE-invalid', '--directory', str(directory)]) == 2
    assert 'PRIVATE' not in capsys.readouterr().out
    assert api().main(['development', '--directory', str(directory), '--approve-live',
                       '--approved-plan', 'PRIVATE']) == 2
    assert 'PRIVATE' not in capsys.readouterr().out
    assert snapshot(tmp_path) == before


def test_cli_prepares_one_private_run_without_credentials_or_dispatch(tmp_path, capsys):
    plan = make_plan(tmp_path/'old')
    path = tmp_path/'approved.json'; path.write_text(json.dumps(plan))
    directory = tmp_path/'qualified'
    assert api().main(['prepare', '--directory', str(directory), '--approved-plan', str(path),
                       '--approve-live']) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['accounting']['reconciled_completions'] == 0
    assert result['accounting']['reserved_attempts'] == 0
    assert result['phases'] == {'development': 'pause', 'evaluation': 'pause'}
    before = snapshot(tmp_path)
    assert api().main(['prepare', '--directory', str(directory), '--approved-plan', str(path),
                       '--approve-live']) == 2
    assert snapshot(tmp_path) == before
    assert json.loads(capsys.readouterr().out)['error'] == 'private_output_exists'
