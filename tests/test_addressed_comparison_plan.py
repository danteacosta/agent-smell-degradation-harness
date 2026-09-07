"""Read-only preparation against real journals containing authored receipts."""
import copy
import hashlib
import json

import pytest

from eval import scoped_judge_study as old
from eval.pilot_ledger import PilotStop
from test_scoped_judge_study import prepare, factory


def api():
    from eval import addressed_comparison_plan
    return addressed_comparison_plan


def failed_predecessor(tmp_path):
    parent, run, manifest = prepare(tmp_path)
    old.run_phase(run, 'development', provider_factory=factory(manifest, [], wrong=True))
    return parent, run


def snapshot(path):
    return {str(p.relative_to(path)): p.read_bytes() for p in path.rglob('*') if p.is_file()}


def reseal(run, manifest):
    (run / 'manifest.json').write_text(json.dumps(manifest))
    identity = old.file_hash(run / 'manifest.json')
    (run / 'manifest-integrity.json').write_text(json.dumps({'sha256': identity}))
    old.claim_path(manifest['parent']['directory']).write_text(json.dumps(
        {'directory': str(run), 'manifest_sha256': identity}))


def test_prepare_retains_spending_and_plans_144_matched_calls_without_writes(tmp_path):
    _, run = failed_predecessor(tmp_path)
    before = snapshot(tmp_path)
    plan = api().prepare_comparison(run, approval=True)
    assert snapshot(tmp_path) == before
    assert len(plan['calls']) == 144
    assert sum(c['phase'] == 'development' for c in plan['calls']) == 48
    assert {c['output_bound'] for c in plan['calls']} == {512}
    assert plan['execution_authorized'] is plan['main_collection_released'] is False
    proposal = plan['budget_proposal']
    parent = plan['parent']
    assert proposal['closure_applied'] is False
    assert proposal['predecessor_spent_microusd'] > 0
    assert proposal['shared_proposed_microusd'] == (
        parent['spent_microusd'] + parent['remaining_direct_microusd']
        + parent['retained_contingency_microusd']
        + proposal['predecessor_spent_microusd'] + 218
        + proposal['new_envelope']['reserved_microusd'])
    assert proposal['shared_proposed_microusd'] <= 7_000_000
    assert proposal['auxiliary_proposed_microusd'] <= 1_000_000
    cases = {c['id']: c for c in plan['cases']}
    for call in plan['calls']:
        case_id, arm, _ = call['id'].split(':', 2)
        item = cases[case_id]['item']
        prompt = api().prompt_for(item, arm)
        assert call['prompt_sha256'] == hashlib.sha256(prompt.encode()).hexdigest()
        assert call['input_bound'] == len(prompt.encode()) + 64
    assert [c['id'].split(':')[1] for c in plan['calls'][:8]] == [
        'v3', 'v3', 'v4', 'v4', 'v4', 'v4', 'v3', 'v3']
    assert api().validate_plan(plan) == plan
    summary = json.dumps(api().preparation_summary(plan))
    for private in ('openai', 'deepseek', str(run), 'prompt_sha256', 'The service'):
        assert private not in summary


def test_missing_approval_has_no_effect(tmp_path):
    _, run = failed_predecessor(tmp_path)
    before = snapshot(tmp_path)
    with pytest.raises(ValueError, match='approval_required'):
        api().prepare_comparison(run)
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize('state', ['incomplete', 'passing', 'evaluation', 'pending'])
def test_only_complete_failed_development_with_no_evaluation_can_be_proposed(tmp_path, state):
    _, run, manifest = prepare(tmp_path)
    if state == 'pending':
        with pytest.raises(PilotStop):
            old.run_phase(run, 'development', provider_factory=factory(manifest, [], missing_usage=True))
    elif state in ('passing', 'evaluation'):
        old.run_phase(run, 'development', provider_factory=factory(manifest, []))
        if state == 'evaluation':
            old.run_phase(run, 'evaluation', provider_factory=factory(manifest, []))
    before = snapshot(tmp_path)
    with pytest.raises(ValueError):
        api().prepare_comparison(run, approval=True)
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize('target', ['claim', 'parent', 'journal', 'baseline', 'gate', 'cases'])
def test_changed_custody_is_rejected_without_repair(tmp_path, target):
    parent, run = failed_predecessor(tmp_path)
    if target == 'claim': old.claim_path(parent).write_text('{}')
    elif target == 'parent': (parent / 'diagnostics.json').write_text('{}')
    elif target == 'journal': (run / 'ledger.jsonl').write_text('{}\n')
    else:
        manifest = old.read(run / 'manifest.json')
        if target in ('baseline', 'gate'):
            key = 'label_plane/scoped_judge.py' if target == 'baseline' else 'eval/scoped_judge_study.py'
            manifest['source_sha256'][key] = '0' * 64
        else: manifest['cases'][0]['oracle']['checks'] = ['omitted', 'omitted']
        reseal(run, manifest)
    before = snapshot(tmp_path)
    with pytest.raises(ValueError): api().prepare_comparison(run, approval=True)
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize('target', ['calls', 'cases', 'budget_proposal', 'execution_authorized', 'extra'])
def test_modified_plan_is_not_accepted_as_a_freeze(tmp_path, target):
    _, run = failed_predecessor(tmp_path)
    plan = copy.deepcopy(api().prepare_comparison(run, approval=True))
    if target == 'calls': plan['calls'][0]['output_bound'] = 513
    elif target == 'cases': plan['cases'][0]['item']['criteria'] += 'changed'
    elif target == 'budget_proposal': plan['budget_proposal']['shared_proposed_microusd'] = 0
    else: plan[target] = True
    with pytest.raises(ValueError, match='invalid_plan'): api().validate_plan(plan)


def test_symlink_predecessor_is_rejected(tmp_path):
    _, run = failed_predecessor(tmp_path)
    link = tmp_path / 'PRIVATE-link'; link.symlink_to(run, target_is_directory=True)
    with pytest.raises(ValueError): api().prepare_comparison(link, approval=True)


def test_shared_and_auxiliary_budget_boundaries_retain_every_component():
    parent = {'spent_microusd': 10, 'remaining_direct_microusd': 5_999_771,
              'retained_contingency_microusd': 1}
    old_envelope = {'reserved_microusd': 100, 'contingency_microusd': 20}
    new_envelope = {'reserved_microusd': 999_990}
    result = api().budget_proposal(parent, 10, 70, old_envelope, new_envelope)
    assert result['shared_proposed_microusd'] == 7_000_000
    assert result['auxiliary_proposed_microusd'] == 1_000_000
    with pytest.raises(ValueError, match='budget_exceeded'):
        api().budget_proposal({**parent, 'spent_microusd': 11}, 10, 70, old_envelope, new_envelope)
    with pytest.raises(ValueError, match='budget_exceeded'):
        api().budget_proposal(parent, 11, 70, old_envelope, new_envelope)


@pytest.mark.parametrize('value', [-1, True, 1.5, '1'])
def test_budget_proposal_requires_nonnegative_integer_microdollars(value):
    parent = {'spent_microusd': 0, 'remaining_direct_microusd': 0, 'retained_contingency_microusd': 0}
    with pytest.raises(ValueError, match='invalid_budget'):
        api().budget_proposal(parent, value, 0, {'reserved_microusd': 1, 'contingency_microusd': 1},
                              {'reserved_microusd': 1})


@pytest.mark.parametrize('owner', ['parent', 'auxiliary'])
def test_existing_writer_lock_blocks_preparation(tmp_path, owner):
    parent, run = failed_predecessor(tmp_path)
    with old.parent_lock(parent if owner == 'parent' else run):
        with pytest.raises(ValueError): api().prepare_comparison(run, approval=True)


def test_duplicate_source_locator_cannot_inflate_independent_units(tmp_path):
    _, run = failed_predecessor(tmp_path)
    manifest = old.read(run / 'manifest.json')
    manifest['seeds'][2]['source_locator'] = manifest['seeds'][0]['source_locator']
    reseal(run, manifest)
    with pytest.raises(ValueError): api().prepare_comparison(run, approval=True)


def test_provider_configuration_must_still_match_its_frozen_parent(tmp_path):
    _, run = failed_predecessor(tmp_path)
    manifest = old.read(run / 'manifest.json')
    # Credential *name* does not change pricing or receipts, but does change
    # the provider contract that was originally inherited from the parent.
    manifest['providers'][0]['api_key_env'] = 'CHANGED_KEY_NAME'
    reseal(run, manifest)
    with pytest.raises(ValueError, match='predecessor_provider_changed'):
        api().prepare_comparison(run, approval=True)


@pytest.mark.parametrize('value', [None, [], 'PRIVATE-invalid'])
def test_malformed_source_inventory_has_a_fixed_error(tmp_path, value):
    _, run = failed_predecessor(tmp_path)
    manifest = old.read(run / 'manifest.json')
    manifest['source_sha256'] = value
    reseal(run, manifest)
    with pytest.raises(ValueError, match='predecessor_source_changed'):
        api().prepare_comparison(run, approval=True)
