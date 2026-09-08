"""Exclusive successor custody; frozen predecessors are read, never rewritten."""
from __future__ import annotations

from contextlib import ExitStack, contextmanager
import subprocess

from eval import scoped_judge_study as historical
from eval.addressed_comparison_custody import file_hash, write_new
from eval.addressed_comparison_plan import ComparisonError, read_bytes, read_json, safe_path
from eval.live_judge_controls import prepare_private_output
from eval.pilot_ledger import PilotLedger
from eval.pilot_preparation import digest
from eval.qualification_lineage import verify_files, verify_runtime
from eval.qualification_plan import check_budget, prices_for, validate_plan

AUTHORIZATION = {'qualified_comparison_approved': True, 'shared_cap_microusd': 7_000_000,
                 'auxiliary_cap_microusd': 1_000_000, 'main_collection_released': False}


def claim_path(plan):
    parent = safe_path(plan['lineage']['ancestors'][0])
    return parent.parent / (parent.name + '.qualified-comparison-claim.json')


@contextmanager
def custody_locks(plan):
    directories = [*plan['lineage']['ancestors'], plan['lineage']['directory']]
    with ExitStack() as stack:
        for directory in directories:
            directory = safe_path(directory)
            read_bytes(directory / 'ledger.jsonl.lock')
            stack.enter_context(historical.parent_lock(directory))
        yield


def verify_plan_custody(plan):
    lineage = plan['lineage']
    verify_files(lineage['custody_sha256'])
    verify_runtime(lineage['runtime'], lineage['source_sha256'])
    if (historical.source_hashes() != plan['source_sha256']
            or digest(historical.environment()) != digest(plan['environment'])):
        raise ComparisonError('runtime_changed')


def _closure(manifest, identity):
    budget = manifest['plan']['budget']
    return {'schema_version': 'qualified-comparison-closure/v1', 'successor_manifest_sha256': identity,
            'predecessor_custody_sha256': manifest['plan']['lineage']['custody_sha256'],
            'retained_predecessor_spent_microusd': budget['predecessor_spent_microusd'],
            'cancelled_direct_microusd': budget['cancelled_direct_microusd'],
            'released_contingency_microusd': budget['released_contingency_microusd'],
            'retained_shared_microusd': budget['retained_shared_microusd'],
            'retained_auxiliary_microusd': budget['retained_auxiliary_microusd'],
            'earlier_unresolved_retained_microusd': budget['earlier_unresolved_retained_microusd'],
            'authorization': AUTHORIZATION}


def verify_custody(directory, manifest):
    directory = safe_path(directory)
    plan = manifest['plan']
    verify_plan_custody(plan)
    identity = file_hash(directory / 'manifest.json')
    if (read_json(directory / 'manifest.json') != manifest
            or read_json(directory / 'manifest-integrity.json') != {'sha256': identity}):
        raise ComparisonError('manifest_changed')
    if read_json(directory / 'closure.json') != _closure(manifest, identity):
        raise ComparisonError('closure_changed')
    expected = {'directory': str(directory), 'manifest_sha256': identity,
                'closure_sha256': file_hash(directory / 'closure.json')}
    if read_json(claim_path(plan)) != expected:
        raise ComparisonError('successor_claim_changed')
    read_bytes(directory / 'ledger.jsonl')
    read_bytes(directory / 'ledger.jsonl.lock')


def create_run(approved_plan, directory, *, approval=False):
    if approval is not True:
        raise ComparisonError('approval_required')
    plan = validate_plan(approved_plan)
    directory = safe_path(directory)
    if directory != directory.resolve():
        raise ComparisonError('invalid_private_path')
    if directory.exists():
        raise ComparisonError('private_output_exists')
    with custody_locks(plan):
        verify_plan_custody(plan)
        if claim_path(plan).exists() or claim_path(plan).is_symlink():
            raise ComparisonError('successor_already_claimed')
        check_budget(plan, 0, {})
        manifest = {'schema_version': 'qualified-comparison-live/v1', 'plan': plan,
                    'authorization': AUTHORIZATION, 'source_revision': subprocess.check_output(
                        ['git', 'rev-parse', 'HEAD'], cwd=historical.ROOT, text=True).strip()}
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
            or set(manifest) != {'schema_version', 'plan', 'authorization', 'source_revision'}
            or manifest['schema_version'] != 'qualified-comparison-live/v1'
            or manifest['authorization'] != AUTHORIZATION):
        raise ComparisonError('invalid_live_manifest')
    validate_plan(manifest['plan'])
    with custody_locks(manifest['plan']):
        verify_custody(directory, manifest)
    return manifest
