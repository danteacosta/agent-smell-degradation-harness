"""Freeze a matched v4/v5 plan and retain the entire predecessor budget lineage."""
from __future__ import annotations

import hashlib
import json

from eval import scoped_judge_study as historical
from eval.addressed_comparison_plan import ComparisonError, PHASES
from eval.exploratory_cost import TokenBounds
from eval.pilot_ledger import envelope
from eval.pilot_preparation import digest
from eval.provider_runtime_config import parse_provider_slot
from eval.qualification_lineage import predecessor_snapshot
from label_plane import qualified_judge


def prices_for(plan):
    return {slot['id']: parse_provider_slot(slot).pricing for slot in plan['providers']}


def _calls(cases, providers):
    calls = []
    for phase in PHASES:
        for index, case in enumerate(c for c in cases if c['oracle']['split'] == phase):
            arms = ('v4', 'v5') if index % 2 == 0 else ('v5', 'v4')
            slots = providers if index % 2 == 0 else list(reversed(providers))
            for arm in arms:
                prompt = qualified_judge.build_prompt(case['item'], arm).encode('utf-8')
                for slot in slots:
                    calls.append({'id': f'{case["id"]}:{arm}:{slot["id"]}', 'slot': slot['id'], 'phase': phase,
                                  'input_bound': len(prompt) + 64, 'output_bound': 512,
                                  'prompt_sha256': hashlib.sha256(prompt).hexdigest()})
    return calls


def check_budget(plan, spent, completed):
    calls = {c['id']: c for c in plan['calls']}
    if type(spent) is not int or spent < 0 or not set(completed) <= calls.keys():
        raise ComparisonError('invalid_budget')
    prices = prices_for(plan)
    remaining = sum(prices[c['slot']].reservation_microusd(TokenBounds(c['input_bound'], c['output_bound']))
                    for c in calls.values() if c['id'] not in completed)
    budget = plan['budget']
    contingency = budget['new_envelope']['contingency_microusd']
    new_commitment = spent + remaining + contingency
    shared = budget['retained_shared_microusd'] + new_commitment
    auxiliary = budget['retained_auxiliary_microusd'] + new_commitment
    if shared > historical.CAP or auxiliary > historical.AUXILIARY_CAP:
        raise ComparisonError('budget_exceeded')
    return {'shared_committed_microusd': shared, 'auxiliary_committed_microusd': auxiliary,
            'remaining_direct_microusd': remaining, 'retained_contingency_microusd': contingency,
            'shared_cap_microusd': historical.CAP, 'auxiliary_cap_microusd': historical.AUXILIARY_CAP,
            'earlier_unresolved_retained_microusd': historical.EARLIER_UNRESOLVED}


def prepare_plan(predecessor, runtime):
    snapshot = predecessor_snapshot(predecessor, runtime)
    cases = qualified_judge.build_cases(snapshot['seeds'])
    sources = historical.source_hashes()
    if any(sources.get(path) != value for path, value in snapshot['lineage']['source_sha256'].items()):
        raise ComparisonError('historical_source_changed')
    plan = {'schema_version': 'qualified-comparison-plan/v1', 'candidate': 'v5',
            'layout_version': qualified_judge.LAYOUT_VERSION, 'main_collection_released': False,
            'lineage': snapshot['lineage'], 'providers': snapshot['providers'], 'cases': cases,
            'case_lineage': [{'case_id': new['id'], 'predecessor_case_id': old['id']}
                             for new, old in zip(cases, snapshot['old_cases'])],
            'calls': _calls(cases, snapshot['providers']), 'source_sha256': sources,
            'environment': json.loads(json.dumps(historical.environment()))}
    report = snapshot['report']
    old_budget = report['budget']
    cancelled = old_budget['remaining_direct_microusd']
    released = old_budget['retained_contingency_microusd']
    plan['budget'] = {
        'retained_shared_microusd': old_budget['shared_committed_microusd'] - cancelled - released,
        'retained_auxiliary_microusd': old_budget['auxiliary_committed_microusd'] - cancelled - released,
        'predecessor_spent_microusd': report['accounting']['spent_microusd'],
        'cancelled_direct_microusd': cancelled, 'released_contingency_microusd': released,
        'earlier_unresolved_retained_microusd': historical.EARLIER_UNRESOLVED,
        'new_envelope': envelope(plan['calls'], prices_for(plan))}
    amounts = [v for k, v in plan['budget'].items() if k != 'new_envelope']
    if any(type(value) is not int or value < 0 for value in amounts):
        raise ComparisonError('invalid_budget')
    check_budget(plan, 0, {})
    return plan


def validate_plan(plan):
    try:
        lineage = plan['lineage']
        expected = prepare_plan(lineage['directory'], lineage['runtime'])
        if digest(plan) != digest(expected):
            raise ValueError
        return expected
    except (ValueError, TypeError, KeyError, OSError, RecursionError) as exc:
        raise ComparisonError('invalid_plan') from exc


def summary(plan):
    return {'schema_version': 'qualified-comparison-preflight/v1', 'provider_calls_dispatched': 0,
            'main_collection_released': False, 'phase_counts': {p: sum(c['phase'] == p for c in plan['calls'])
                                                              for p in PHASES},
            'budget': check_budget(plan, 0, {}), 'new_envelope': plan['budget']['new_envelope']}
