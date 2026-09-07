"""Read-only comparison preparation. A budget proposal is not a spending token."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import stat

from eval import scoped_judge_study as predecessor
from eval.exploratory_cost import TokenBounds
from eval.pilot_ledger import PilotStop, envelope, inspect_ledger
from eval.pilot_preparation import digest
from eval.provider_runtime_config import parse_provider_slot
from label_plane import addressed_judge, scoped_judge
from label_plane.evidence_json import load_json

MAX_FILE_BYTES = 16 * 1024 * 1024
SCHEMA = 'addressed-comparison-plan/v1'
PHASES = ('development', 'evaluation')
AUTHORITY = {'execution_authorized': False, 'main_collection_released': False,
             'provider_calls_dispatched': 0, 'semantic_validity': 'not_measured'}


class ComparisonError(ValueError):
    """Fixed public error code; do not include values, paths or raw exceptions."""


def safe_path(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ComparisonError('invalid_private_path')
    return path


def read_bytes(path):
    path = safe_path(path)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE_BYTES:
                raise ComparisonError('invalid_private_file')
            data = stream.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise ComparisonError('invalid_private_file')
        return data
    except OSError as exc:
        raise ComparisonError('invalid_private_file') from exc


def read_json(path):
    try:
        return load_json(read_bytes(path).decode('utf-8'))
    except (ValueError, RecursionError) as exc:
        raise ComparisonError('invalid_private_json') from exc


def prompt_for(item, arm):
    if arm == 'v3':
        return scoped_judge.build_prompt(item, 'v3')
    if arm == 'v4':
        return addressed_judge.build_prompt(item)
    raise ComparisonError('invalid_arm')


def matched_calls(cases, specs):
    calls = []
    for phase in PHASES:
        for index, case in enumerate(c for c in cases if c['oracle']['split'] == phase):
            arms = ('v3', 'v4') if index % 2 == 0 else ('v4', 'v3')
            slots = specs if index % 2 == 0 else list(reversed(specs))
            for arm in arms:
                raw = prompt_for(case['item'], arm).encode('utf-8')
                for slot in slots:
                    calls.append({'id': f'{case["id"]}:{arm}:{slot["id"]}',
                                  'slot': slot['id'], 'phase': phase,
                                  'input_bound': len(raw) + 64, 'output_bound': 512,
                                  'prompt_sha256': hashlib.sha256(raw).hexdigest()})
    return calls


def budget_proposal(parent, spent, remaining, old_envelope, new_envelope):
    try:
        components = [parent[k] for k in ('spent_microusd', 'remaining_direct_microusd',
                                          'retained_contingency_microusd')]
        amounts = components + [spent, remaining, old_envelope['reserved_microusd'],
                                old_envelope['contingency_microusd'], new_envelope['reserved_microusd']]
        if any(type(value) is not int or value < 0 for value in amounts):
            raise ValueError
    except (KeyError, TypeError, ValueError) as exc:
        raise ComparisonError('invalid_budget') from exc
    retained = sum(components)
    unresolved = predecessor.EARLIER_UNRESOLVED
    new_reserved = new_envelope['reserved_microusd']
    shared = retained + spent + unresolved + new_reserved
    auxiliary = spent + new_reserved
    if shared > predecessor.CAP or auxiliary > predecessor.AUXILIARY_CAP:
        raise ComparisonError('budget_exceeded')
    return {'closure_applied': False, 'closure_required_before_dispatch': True,
            'predecessor_spent_microusd': spent,
            'proposed_cancelled_direct_microusd': remaining,
            'proposed_released_contingency_microusd': old_envelope['contingency_microusd'],
            'earlier_unresolved_retained_microusd': unresolved,
            'new_envelope': new_envelope, 'shared_proposed_microusd': shared,
            'auxiliary_proposed_microusd': auxiliary,
            'shared_with_old_full_reserve_microusd':
                retained + unresolved + old_envelope['reserved_microusd'] + new_reserved,
            'shared_cap_microusd': predecessor.CAP,
            'auxiliary_cap_microusd': predecessor.AUXILIARY_CAP}


def _custody(directory, parent):
    paths = [directory / name for name in ('manifest.json', 'manifest-integrity.json', 'ledger.jsonl')]
    paths += [parent / name for name in ('launch.json', 'launch-integrity.json', 'diagnostics.json', 'ledger.jsonl')]
    paths += [predecessor.claim_path(parent)]
    return {str(p): hashlib.sha256(read_bytes(p)).hexdigest() for p in paths}


def _verify_bank(manifest):
    seeds = manifest['seeds']
    if Counter(s['split'] for s in seeds) != {'development': 2, 'evaluation': 4}:
        raise ComparisonError('invalid_predecessor_bank')
    if any(len({s['project_id'] for s in seeds if s['split'] == phase}) != 2 for phase in PHASES):
        raise ComparisonError('invalid_predecessor_bank')
    locators = {(s['project_id'], s['source_revision_id'], s['source_locator']) for s in seeds}
    if len(locators) != 6 or scoped_judge.build_cases(seeds) != manifest['cases']:
        raise ComparisonError('invalid_predecessor_bank')
    if predecessor.planned_calls(manifest['cases'], manifest['providers']) != manifest['calls']:
        raise ComparisonError('invalid_predecessor_bank')


def _prepare(directory):
    initial = read_json(directory / 'manifest.json')
    parent = safe_path(initial['parent']['directory'])
    # Existing locks are opened read-only, in the original runner's order.
    safe_path(parent / 'ledger.jsonl.lock')
    safe_path(directory / 'ledger.jsonl.lock')
    with predecessor.parent_lock(parent), predecessor.parent_lock(directory):
        before = _custody(directory, parent)
        for path in before:
            if not path.endswith('.jsonl'):
                read_json(path)  # Strict, bounded JSON before legacy readers.
        manifest = predecessor.load_study(directory, check_runtime=False)
        if manifest['parent']['directory'] != str(parent):
            raise ComparisonError('custody_changed')
        if digest(manifest['providers']) != digest(read_json(parent / 'launch.json')['providers']):
            raise ComparisonError('predecessor_provider_changed')
        current_sources = predecessor.source_hashes()
        required = {'label_plane/scoped_judge.py', 'eval/scoped_judge_study.py',
                    'eval/pilot_ledger.py', 'eval/exploratory_cost.py',
                    'eval/provider_runtime_config.py'}
        frozen = manifest['source_sha256']
        if (not isinstance(frozen, dict) or not required <= frozen.keys()
                or any(current_sources.get(k) != v for k, v in frozen.items())):
            raise ComparisonError('predecessor_source_changed')
        _verify_bank(manifest)
        prices = {s['id']: parse_provider_slot(s).pricing for s in manifest['providers']}
        ledger, completed = inspect_ledger(directory / 'ledger.jsonl', manifest['calls'], prices)
        dev_ids = {c['id'] for c in manifest['calls'] if c['phase'] == 'development'}
        if (ledger['state'] != 'ready' or ledger['pending_count'] or set(completed) != dev_ids
                or predecessor._phase_scores(manifest, completed, 'development')['decision'] != 'pause'):
            raise ComparisonError('predecessor_not_closable')
        old_envelope = envelope(manifest['calls'], prices)
        parent_snapshot = manifest['parent']
        old_budget = manifest['budget']
        expected_combined = (sum(parent_snapshot[k] for k in ('spent_microusd', 'remaining_direct_microusd',
                            'retained_contingency_microusd')) + old_envelope['reserved_microusd']
                            + predecessor.EARLIER_UNRESOLVED)
        if (old_budget['auxiliary_reserved_microusd'] != old_envelope['reserved_microusd']
                or old_budget['combined_reserved_microusd'] != expected_combined
                or old_budget['earlier_unresolved_retained_microusd'] != predecessor.EARLIER_UNRESOLVED
                or old_budget['shared_cap_microusd'] != predecessor.CAP
                or old_budget['auxiliary_cap_microusd'] != predecessor.AUXILIARY_CAP):
            raise ComparisonError('invalid_predecessor_budget')
        remaining = sum(prices[c['slot']].reservation_microusd(TokenBounds(c['input_bound'], c['output_bound']))
                        for c in manifest['calls'] if c['id'] not in completed)
        calls = matched_calls(manifest['cases'], manifest['providers'])
        proposal = budget_proposal(parent_snapshot, ledger['spent_microusd'], remaining,
                                   old_envelope, envelope(calls, prices))
        if _custody(directory, parent) != before:
            raise ComparisonError('custody_changed')
        return {'schema_version': SCHEMA, 'mode': 'offline_comparison_plan', **AUTHORITY,
                'predecessor_directory': str(directory), 'custody_sha256': before,
                'parent': parent_snapshot, 'providers': manifest['providers'],
                'cases': manifest['cases'], 'calls': calls, 'budget_proposal': proposal,
                'source_sha256': current_sources,
                'environment': json.loads(json.dumps(predecessor.environment()))}


def prepare_comparison(directory, *, approval=False):
    if approval is not True:
        raise ComparisonError('approval_required')
    try:
        return _prepare(safe_path(directory))
    except ComparisonError:
        raise
    except (OSError, ValueError, TypeError, KeyError, RecursionError, PilotStop) as exc:
        raise ComparisonError('invalid_predecessor') from exc


def validate_plan(plan):
    try:
        expected = prepare_comparison(plan['predecessor_directory'], approval=True)
        if digest(plan) != digest(expected):
            raise ValueError
        return expected
    except (ValueError, TypeError, KeyError, RecursionError) as exc:
        raise ComparisonError('invalid_plan') from exc


def preparation_summary(plan):
    return {'schema_version': 'addressed-comparison-preparation/v1', **AUTHORITY,
            'mode': 'offline_preparation', 'planned_calls': len(plan['calls']),
            'phase_counts': dict(Counter(c['phase'] for c in plan['calls'])),
            'budget_proposal': plan['budget_proposal']}
