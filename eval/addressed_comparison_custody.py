"""Exclusive auxiliary succession; historical journals remain untouched."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
import subprocess

from eval import scoped_judge_study as old
from eval.addressed_comparison_plan import (
    ComparisonError, prepare_comparison, read_bytes, read_json, safe_path, validate_plan,
)
from eval.exploratory_cost import TokenBounds
from eval.live_judge_controls import prepare_private_output
from eval.pilot_ledger import PilotLedger
from eval.pilot_preparation import digest
from eval.provider_runtime_config import parse_provider_slot

AUTHORIZATION = {'auxiliary_comparison_approved': True, 'shared_cap_microusd': 7_000_000,
                 'auxiliary_cap_microusd': 1_000_000, 'main_collection_released': False}


def file_hash(path):
    return hashlib.sha256(read_bytes(path)).hexdigest()


def write_new(path, value):
    """Publish one private durable file, never replace an existing artifact."""
    path = safe_path(path)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    directory_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def claim_path(plan):
    parent = safe_path(plan['parent']['directory'])
    return parent.parent / (parent.name + '.addressed-comparison-claim.json')


@contextmanager
def custody_locks(plan):
    parent = safe_path(plan['parent']['directory'])
    predecessor = safe_path(plan['predecessor_directory'])
    for directory in (parent, predecessor):
        read_bytes(directory / 'ledger.jsonl.lock')
    with old.parent_lock(parent), old.parent_lock(predecessor):
        yield


def prices_for(plan):
    return {s['id']: parse_provider_slot(s).pricing for s in plan['providers']}


def verify_plan_custody(plan):
    for path, expected in plan['custody_sha256'].items():
        if file_hash(path) != expected:
            raise ComparisonError('custody_changed')
    if (old.source_hashes() != plan['source_sha256']
            or digest(old.environment()) != digest(plan['environment'])):
        raise ComparisonError('runtime_changed')


def _closure(manifest, identity):
    proposal = manifest['plan']['budget_proposal']
    return {'schema_version': 'addressed-comparison-closure/v1',
            'successor_manifest_sha256': identity,
            'predecessor_custody_sha256': manifest['plan']['custody_sha256'],
            'retained_predecessor_spent_microusd': proposal['predecessor_spent_microusd'],
            'cancelled_direct_microusd': proposal['proposed_cancelled_direct_microusd'],
            'released_contingency_microusd': proposal['proposed_released_contingency_microusd'],
            'earlier_unresolved_retained_microusd': proposal['earlier_unresolved_retained_microusd'],
            'authorization': AUTHORIZATION}


def verify_custody(directory, manifest):
    """Recheck identities inside acquired locks, without nested validation locks."""
    directory = safe_path(directory)
    plan = manifest['plan']
    verify_plan_custody(plan)
    if read_json(directory / 'manifest.json') != manifest:
        raise ComparisonError('manifest_changed')
    identity = file_hash(directory / 'manifest.json')
    if read_json(directory / 'manifest-integrity.json') != {'sha256': identity}:
        raise ComparisonError('manifest_changed')
    if read_json(directory / 'closure.json') != _closure(manifest, identity):
        raise ComparisonError('closure_changed')
    expected = {'directory': str(directory), 'manifest_sha256': identity,
                'closure_sha256': file_hash(directory / 'closure.json')}
    if read_json(claim_path(plan)) != expected:
        raise ComparisonError('successor_claim_changed')
    read_bytes(directory / 'ledger.jsonl')
    read_bytes(directory / 'ledger.jsonl.lock')


def check_budget(plan, spent, completed):
    if type(spent) is not int or spent < 0:
        raise ComparisonError('invalid_budget')
    calls = {c['id']: c for c in plan['calls']}
    if not set(completed) <= calls.keys():
        raise ComparisonError('invalid_completed_inventory')
    prices = prices_for(plan)
    remaining = sum(prices[c['slot']].reservation_microusd(
        TokenBounds(c['input_bound'], c['output_bound']))
        for c in calls.values() if c['id'] not in completed)
    proposal = plan['budget_proposal']
    new = spent + remaining + proposal['new_envelope']['contingency_microusd']
    auxiliary = proposal['predecessor_spent_microusd'] + new
    parent = sum(plan['parent'][k] for k in ('spent_microusd', 'remaining_direct_microusd',
                                           'retained_contingency_microusd'))
    shared = parent + auxiliary + proposal['earlier_unresolved_retained_microusd']
    if shared > old.CAP or auxiliary > old.AUXILIARY_CAP:
        raise ComparisonError('budget_exceeded')
    return {'shared_committed_microusd': shared, 'auxiliary_committed_microusd': auxiliary,
            'remaining_direct_microusd': remaining,
            'retained_contingency_microusd': proposal['new_envelope']['contingency_microusd'],
            'shared_cap_microusd': old.CAP, 'auxiliary_cap_microusd': old.AUXILIARY_CAP,
            'earlier_unresolved_retained_microusd': proposal['earlier_unresolved_retained_microusd']}


def create_run(approved_plan, directory, *, approval=False):
    if approval is not True:
        raise ComparisonError('approval_required')
    plan = prepare_comparison(approved_plan['predecessor_directory'], approval=True)
    frozen = approved_plan.get('source_sha256')
    required = {'label_plane/addressed_judge.py', 'label_plane/artifact_segments.py',
                'eval/addressed_comparison_audit.py'}
    if (not isinstance(frozen, dict) or not required <= frozen.keys()
            or any(plan['source_sha256'].get(k) != v for k, v in frozen.items())
            or digest({**approved_plan, 'source_sha256': plan['source_sha256']}) != digest(plan)):
        raise ComparisonError('approved_contract_changed')
    directory = safe_path(directory)
    if directory != directory.resolve():
        raise ComparisonError('invalid_private_path')
    with custody_locks(plan):
        verify_plan_custody(plan)
        if claim_path(plan).exists() or claim_path(plan).is_symlink():
            raise ComparisonError('successor_already_claimed')
        check_budget(plan, 0, {})
        manifest = {'schema_version': 'addressed-comparison-live/v1', 'plan': plan,
                    'approved_plan_sha256': digest(approved_plan), 'authorization': AUTHORIZATION,
                    'source_revision': subprocess.check_output(
                        ['git', 'rev-parse', 'HEAD'], cwd=old.ROOT, text=True).strip()}
        directory = prepare_private_output(directory)
        write_new(directory / 'manifest.json', manifest)
        identity = file_hash(directory / 'manifest.json')
        write_new(directory / 'manifest-integrity.json', {'sha256': identity})
        write_new(directory / 'closure.json', _closure(manifest, identity))
        with PilotLedger(directory / 'ledger.jsonl', plan['calls'], prices_for(plan), approval=True):
            pass
        write_new(claim_path(plan), {'directory': str(directory), 'manifest_sha256': identity,
                                    'closure_sha256': file_hash(directory / 'closure.json')})
    return manifest


def load_run(directory):
    directory = safe_path(directory)
    manifest = read_json(directory / 'manifest.json')
    if (not isinstance(manifest, dict)
            or set(manifest) != {'schema_version', 'plan', 'approved_plan_sha256', 'authorization', 'source_revision'}
            or manifest['schema_version'] != 'addressed-comparison-live/v1'
            or manifest['authorization'] != AUTHORIZATION):
        raise ComparisonError('invalid_live_manifest')
    validate_plan(manifest['plan'])
    with custody_locks(manifest['plan']):
        verify_custody(directory, manifest)
    return manifest
