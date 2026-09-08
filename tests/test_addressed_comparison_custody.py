"""Exclusive budget succession uses real preserved journals, without providers."""
import copy
import json
import os

import pytest

from eval import scoped_judge_study as old
from eval.addressed_comparison_plan import prepare_comparison
from test_addressed_comparison_plan import failed_predecessor, snapshot


def api():
    from eval import addressed_comparison_custody
    return addressed_comparison_custody


def prepared(tmp_path):
    parent, predecessor = failed_predecessor(tmp_path / 'old')
    approved = prepare_comparison(predecessor, approval=True)
    directory = tmp_path / 'new'
    manifest = api().create_run(approved, directory, approval=True)
    return parent, predecessor, directory, manifest


def test_closure_preserves_old_bytes_and_retains_actual_spending(tmp_path):
    parent, predecessor = failed_predecessor(tmp_path / 'old')
    before = snapshot(tmp_path / 'old')
    plan = prepare_comparison(predecessor, approval=True)
    directory = tmp_path / 'new'
    manifest = api().create_run(plan, directory, approval=True)
    after = snapshot(tmp_path / 'old')
    assert all(after[k] == value for k, value in before.items())
    assert len(after) == len(before) + 1  # Only the separate successor claim.
    assert manifest['plan'] == plan
    assert api().load_run(directory) == manifest
    closure = json.loads((directory / 'closure.json').read_text())
    assert closure['retained_predecessor_spent_microusd'] == plan['budget_proposal']['predecessor_spent_microusd']
    assert closure['cancelled_direct_microusd'] == plan['budget_proposal']['proposed_cancelled_direct_microusd']
    assert old.claim_path(parent).read_bytes() == before[str(old.claim_path(parent).relative_to(tmp_path / 'old'))]
    assert os.stat(directory).st_mode & 0o777 == 0o700
    assert os.stat(api().claim_path(plan)).st_mode & 0o777 == 0o600
    with pytest.raises(ValueError, match='successor_already_claimed'):
        api().create_run(plan, tmp_path / 'another', approval=True)
    assert not (tmp_path / 'another').exists()


def test_missing_approval_has_no_effect(tmp_path):
    _, predecessor = failed_predecessor(tmp_path / 'old')
    before = snapshot(tmp_path)
    with pytest.raises(ValueError, match='approval_required'):
        api().create_run(prepare_comparison(predecessor, approval=True), tmp_path / 'new')
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize('field', ['cases', 'calls', 'budget_proposal', 'source_sha256', 'environment'])
def test_approved_contract_cannot_be_silently_changed(tmp_path, field):
    _, predecessor = failed_predecessor(tmp_path / 'old')
    plan = prepare_comparison(predecessor, approval=True)
    changed = copy.deepcopy(plan)
    changed[field] = {} if isinstance(plan[field], dict) else []
    with pytest.raises(ValueError): api().create_run(changed, tmp_path / 'new', approval=True)
    assert not (tmp_path / 'new').exists()


@pytest.mark.parametrize('filename', ['manifest.json', 'manifest-integrity.json', 'closure.json', 'ledger.jsonl', 'ledger.jsonl.lock'])
def test_missing_durable_file_is_not_recreated(tmp_path, filename):
    _, _, directory, _ = prepared(tmp_path)
    (directory / filename).unlink()
    before = snapshot(tmp_path)
    with pytest.raises((ValueError, OSError)): api().load_run(directory)
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize('target', ['claim', 'closure', 'parent', 'source', 'environment'])
def test_custody_changes_block_loading(tmp_path, monkeypatch, target):
    parent, _, directory, manifest = prepared(tmp_path)
    if target == 'claim': api().claim_path(manifest['plan']).write_text('{}')
    elif target == 'closure': (directory / 'closure.json').write_text('{}')
    elif target == 'parent': (parent / 'diagnostics.json').write_text('{}')
    elif target == 'source': monkeypatch.setattr(old, 'source_hashes', lambda: {})
    else: monkeypatch.setattr(old, 'environment', lambda: {})
    with pytest.raises(ValueError): api().load_run(directory)


def test_partial_directory_is_preserved_and_cannot_dispatch(tmp_path):
    _, predecessor = failed_predecessor(tmp_path / 'old')
    plan = prepare_comparison(predecessor, approval=True)
    directory = tmp_path / 'new'; directory.mkdir()
    marker = directory / 'manifest.json'; marker.write_text('{}')
    with pytest.raises((ValueError, OSError)): api().create_run(plan, directory, approval=True)
    assert marker.read_text() == '{}'
    assert not api().claim_path(plan).exists()


def test_budget_retains_full_remaining_envelope_after_partial_receipts(tmp_path):
    _, _, _, manifest = prepared(tmp_path)
    plan = manifest['plan']; proposed = plan['budget_proposal']
    result = api().check_budget(plan, 0, {})
    assert result['shared_committed_microusd'] == proposed['shared_proposed_microusd']
    assert result['auxiliary_committed_microusd'] == proposed['auxiliary_proposed_microusd']
    with pytest.raises(ValueError, match='budget_exceeded'): api().check_budget(plan, 7_000_001, {})
    with pytest.raises(ValueError): api().check_budget(plan, -1, {})


def test_symlink_output_is_rejected_without_following(tmp_path):
    _, predecessor = failed_predecessor(tmp_path / 'old')
    plan = prepare_comparison(predecessor, approval=True)
    target = tmp_path / 'target'; target.mkdir()
    link = tmp_path / 'link'; link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError): api().create_run(plan, link / 'new', approval=True)
    assert list(target.iterdir()) == []


def test_new_runtime_files_do_not_change_the_approved_experimental_contract(tmp_path):
    _, predecessor = failed_predecessor(tmp_path / 'old')
    approved = prepare_comparison(predecessor, approval=True)
    for name in ('eval/addressed_comparison_custody.py', 'eval/addressed_comparison_live.py'):
        approved['source_sha256'].pop(name)
    manifest = api().create_run(approved, tmp_path / 'new', approval=True)
    assert manifest['plan']['calls'] == approved['calls']
    assert manifest['plan']['cases'] == approved['cases']
    assert manifest['plan']['budget_proposal'] == approved['budget_proposal']
    assert set(approved['source_sha256']) < set(manifest['plan']['source_sha256'])


def test_shared_cap_is_inclusive_and_one_microdollar_over_is_rejected(tmp_path):
    _, _, _, manifest = prepared(tmp_path)
    plan = copy.deepcopy(manifest['plan'])
    current = api().check_budget(plan, 0, {})['shared_committed_microusd']
    plan['parent']['remaining_direct_microusd'] += 7_000_000 - current
    assert api().check_budget(plan, 0, {})['shared_committed_microusd'] == 7_000_000
    plan['parent']['remaining_direct_microusd'] += 1
    with pytest.raises(ValueError, match='budget_exceeded'): api().check_budget(plan, 0, {})
