"""Finite direct-code schedule and source-relative missingness analysis.

This module performs no provider calls, execution, admission or scoring. A later
collector must qualify and freeze its oracle before using the schedule.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import random
import re

MODELS = ('gpt-5.6-luna', 'gpt-5.6-sol')
ARMS = ('A', 'B', 'C')
REPETITIONS = (1, 2, 3)
EXECUTABLE = {
    'pass': False,
    'non_target_only_failure': False,
    'target_only_failure': True,
    'mixed_failure': True,
}
UNKNOWN = frozenset({'not_attempted', 'provider_error', 'invalid_output',
                     'interface_error', 'browser_error', 'timeout', 'oracle_error',
                     'target_not_evaluable'})


def plan_slots(cases: list[dict], seed: int = 20260922) -> list[dict]:
    """Return opaque, balanced schedule metadata for an already qualified cohort."""
    if not isinstance(cases, list) or not cases or type(seed) is not int:
        raise ValueError('nonempty qualified cases and integer seed required')
    ids = set()
    slots = []
    for case in cases:
        if not isinstance(case, dict) or case.get('status') != 'qualified':
            raise ValueError('every scheduled case must be qualified')
        intent, project, variants = case.get('id'), case.get('project_id'), case.get('variants')
        if (not isinstance(intent, str) or not intent.strip() or intent in ids
                or not isinstance(project, str) or not project.strip()
                or not isinstance(variants, dict) or set(variants) != set(ARMS)
                or any(not isinstance(variants[arm], str) or not variants[arm].strip() for arm in ARMS)
                or len(set(variants.values())) != 3):
            raise ValueError('unique intent, project and three distinct variants required')
        ids.add(intent)
        for model in MODELS:
            for repetition in REPETITIONS:
                for variant in ARMS:
                    identity = (intent, project, model, repetition, variant, seed)
                    slot_id = 'behavior-' + hashlib.sha256(json.dumps(identity).encode()).hexdigest()[:20]
                    slots.append({'slot_id': slot_id, 'intent_id': intent,
                                  'project_id': project, 'model': model,
                                  'replication': repetition, 'variant': variant})
    random.Random(seed).shuffle(slots)
    if len({slot['slot_id'] for slot in slots}) != len(slots):
        raise ValueError('slot ID collision')
    return slots


def plan_e2e_slots(cases: list[dict], seed: int = 20260922) -> list[dict]:
    """Schedule only qualified generated-UI cases with frozen prompt and oracle receipts."""
    if not isinstance(cases, list) or not cases:
        raise ValueError('nonempty E2E cohort required')
    for case in cases:
        if (not isinstance(case, dict) or case.get('test_layer') != 'browser'
                or case.get('artifact_interface') != 'generated_ui'
                or any(not isinstance(case.get(key), str)
                       or not re.fullmatch(r'[0-9a-f]{64}', case[key])
                       for key in ('oracle_receipt_sha256', 'prompt_bundle_sha256'))):
            raise ValueError('E2E cases require generated UI, browser oracle and frozen receipts')
    return plan_slots(cases, seed)


def _mean_bounds(values: list[dict]) -> list[float]:
    return [sum(value['difference_bounds'][i] for value in values) / len(values)
            for i in (0, 1)]


def summarize(slots: list[dict], observations: list[dict]) -> dict:
    """Report fixed-denominator failure bounds for every planned arm."""
    if not isinstance(slots, list) or not slots or not isinstance(observations, list):
        raise ValueError('planned slots and observation list required')
    by_id = {}
    design = defaultdict(set)
    intent_projects = {}
    for slot in slots:
        if not isinstance(slot, dict) or not isinstance(slot.get('slot_id'), str) or slot['slot_id'] in by_id:
            raise ValueError('unique planned slot IDs required')
        if (not isinstance(slot.get('intent_id'), str) or not slot['intent_id']
                or not isinstance(slot.get('project_id'), str) or not slot['project_id']
                or slot.get('model') not in MODELS or slot.get('variant') not in ARMS
                or slot.get('replication') not in REPETITIONS):
            raise ValueError('planned slot metadata invalid')
        by_id[slot['slot_id']] = slot
        intent = slot['intent_id']
        if intent in intent_projects and intent_projects[intent] != slot['project_id']:
            raise ValueError('one project per intent required')
        intent_projects[intent] = slot['project_id']
        cell = (slot['project_id'], slot['intent_id'], slot['model'], slot['variant'])
        if slot['replication'] in design[cell]:
            raise ValueError('duplicate planned replication')
        design[cell].add(slot['replication'])
    intents = {(project, intent) for project, intent, _, _ in design}
    expected = {(project, intent, model, arm) for project, intent in intents
                for model in MODELS for arm in ARMS}
    if set(design) != expected or any(reps != set(REPETITIONS) for reps in design.values()):
        raise ValueError('incomplete planned intent/model/arm schedule')
    observed = {}
    for row in observations:
        if not isinstance(row, dict) or row.get('slot_id') not in by_id or row['slot_id'] in observed:
            raise ValueError('duplicate or unplanned observation')
        category, failed = row.get('category'), row.get('target_failed')
        if category in EXECUTABLE:
            if failed is not EXECUTABLE[category]:
                raise ValueError('executable category and target result disagree')
        elif category in UNKNOWN:
            if failed is not None:
                raise ValueError('incomplete observation cannot be scored')
        else:
            raise ValueError('unknown observation category')
        observed[row['slot_id']] = row
    buckets = defaultdict(list)
    for slot in slots:
        key = (slot['project_id'], slot['intent_id'], slot['model'], slot['variant'])
        buckets[key].append(observed.get(slot['slot_id']))
    groups = []
    lookup = {}
    for key, values in sorted(buckets.items()):
        if len(values) != len(REPETITIONS):
            raise ValueError('every intent/model/arm needs three planned positions')
        failed = sum(row is not None and row['target_failed'] is True for row in values)
        passed = sum(row is not None and row['target_failed'] is False for row in values)
        unknown = len(values) - failed - passed
        group = dict(zip(('project_id', 'intent_id', 'model', 'variant'), key))
        group.update(planned=len(values), target_failed=failed, target_passed=passed,
                     unknown=unknown,
                     categories=dict(Counter(row['category'] if row else 'missing_row' for row in values)),
                     target_failure_bounds=[failed / len(values), (failed + unknown) / len(values)])
        groups.append(group)
        lookup[key] = group
    contrasts = []
    for (project, intent, model, arm), baseline in sorted(lookup.items()):
        if arm != 'A':
            continue
        for other in ('C', 'B'):
            comparison = lookup.get((project, intent, model, other))
            if comparison is None:
                raise ValueError('missing planned comparison arm')
            low, high = comparison['target_failure_bounds']
            base_low, base_high = baseline['target_failure_bounds']
            contrasts.append({'project_id': project, 'intent_id': intent, 'model': model,
                              'comparison': other + '-A',
                              'difference_bounds': [low - base_high, high - base_low]})
    project_cells = defaultdict(list)
    intent_cells = defaultdict(list)
    for contrast in contrasts:
        key = (contrast['model'], contrast['comparison'])
        project_cells[(contrast['project_id'], *key)].append(contrast)
        intent_cells[key].append(contrast)
    projects = [{'project_id': project, 'model': model, 'comparison': comparison,
                 'difference_bounds': _mean_bounds(values)}
                for (project, model, comparison), values in sorted(project_cells.items())]
    project_weights = defaultdict(list)
    for cell in projects:
        project_weights[(cell['model'], cell['comparison'])].append(cell)
    project_weighted = [{'model': model, 'comparison': comparison,
                         'projects': len(values), 'difference_bounds': _mean_bounds(values)}
                        for (model, comparison), values in sorted(project_weights.items())]
    intent_weighted = [{'model': model, 'comparison': comparison,
                        'intents': len(values), 'difference_bounds': _mean_bounds(values)}
                       for (model, comparison), values in sorted(intent_cells.items())]
    executable = sum(row['category'] in EXECUTABLE for row in observations)
    return {'schema_version': 'behavioral-expansion-analysis/v1', 'planned': len(slots),
            'recorded_rows': len(observations), 'executable': executable,
            'unknown': len(slots) - executable, 'groups': groups, 'contrasts': contrasts,
            'projects': projects, 'project_weighted': project_weighted,
            'intent_weighted': intent_weighted,
            'limitations': ['missingness bounds are not confidence intervals',
                            'repetitions are nested within intent and project',
                            'no general H1 or H2 inference from purposive sources']}
