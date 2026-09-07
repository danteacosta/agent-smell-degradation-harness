"""Descriptive supplied-response audit, never a provider receipt or release gate."""
from __future__ import annotations

from collections import Counter

from eval.addressed_comparison_plan import AUTHORITY, PHASES, ComparisonError, validate_plan
from label_plane import addressed_judge, scoped_judge
from label_plane.artifact_segments import EvidenceContractError

REQUIRED_OPERATIONS = ('long_omission', 'partial_missing', 'partial_complete', 'partial_contradiction')
COUNT_FIELDS = ('planned', 'observed', 'valid', 'invalid', 'missing', 'aggregate_matches', 'exact_matches')


def _observations(records, calls):
    if not isinstance(records, list) or len(records) > len(calls):
        raise ComparisonError('invalid_observations')
    rows = {}
    for row in records:
        if (not isinstance(row, dict) or set(row) != {'call_id', 'prompt_sha256', 'raw_response'}
                or not isinstance(row['call_id'], str) or row['call_id'] not in calls
                or row['call_id'] in rows
                or row['prompt_sha256'] != calls[row['call_id']]['prompt_sha256']):
            raise ComparisonError('invalid_observations')
        rows[row['call_id']] = row['raw_response']
    return rows


def _score(raw, case, arm):
    count = dict.fromkeys(COUNT_FIELDS, 0)
    count['planned'] = 1
    if raw is None:
        count['missing'] = 1
        return count, None
    count['observed'] = 1
    try:
        if not isinstance(raw, str) or len(raw) > addressed_judge.MAX_RESPONSE_CHARS:
            raise ValueError
        if arm == 'v3':
            result = scoped_judge.parse_response(raw, case['item'], 'v3')
            statuses = result['checks']
        else:
            result = addressed_judge.parse_response(raw, case['item'])
            statuses = [c['status'] for c in result['checks']]
    except (ValueError, TypeError, RecursionError) as exc:
        count['invalid'] = 1
        error = str(exc) if isinstance(exc, EvidenceContractError) else f'invalid_{arm}_response'
        return count, error
    count['valid'] = 1
    count['aggregate_matches'] = int(result['status'] == case['oracle']['status'])
    count['exact_matches'] = int(statuses == case['oracle']['checks'])
    return count, None


def _sum(rows):
    rows = list(rows)
    return {key: sum(r[key] for r in rows) for key in COUNT_FIELDS}


def _candidate_rule(strata, phase):
    phase_rows = [r for r in strata if r['phase'] == phase]
    if any(r['missing'] for r in phase_rows):
        return False
    for slot in {r['provider_slot'] for r in phase_rows}:
        rows = [r for r in phase_rows if r['provider_slot'] == slot and r['arm'] == 'v4']
        total = _sum(rows)
        if (not rows or total['valid'] != total['planned']
                or total['exact_matches'] * 6 < total['planned'] * 5):
            return False
        for operation in REQUIRED_OPERATIONS:
            counts = _sum(r for r in rows if r['operation'] == operation)
            if not counts['planned'] or counts['exact_matches'] != counts['planned']:
                return False
    return True


def audit_comparison(plan, records):
    plan = validate_plan(plan)
    calls = {c['id']: c for c in plan['calls']}
    observed = _observations(records, calls)
    cases = {c['id']: c for c in plan['cases']}
    slots = {s['id']: f'provider_{i + 1}' for i, s in enumerate(plan['providers'])}
    source_ids = list(dict.fromkeys(c['oracle']['source_intent_id'] for c in plan['cases']))
    projects = list(dict.fromkeys(c['oracle']['project_id'] for c in plan['cases']))
    sources = {s: f'source_{i + 1}' for i, s in enumerate(source_ids)}
    project_groups = {p: f'project_{i + 1}' for i, p in enumerate(projects)}
    strata, errors, outcomes = [], Counter(), {}
    for call in plan['calls']:
        case_id, arm, slot = call['id'].split(':', 2)
        case = cases[case_id]
        counts, error = _score(observed.get(call['id']), case, arm)
        if error:
            errors[error] += 1
        outcomes[(case_id, slot, arm)] = counts
        strata.append({'phase': call['phase'], 'provider_slot': slots[slot], 'arm': arm,
                       'source_group': sources[case['oracle']['source_intent_id']],
                       'project_group': project_groups[case['oracle']['project_id']],
                       'operation': case['oracle']['operation'], **counts})
    arms, paired = [], []
    for phase in PHASES:
        for slot, opaque in slots.items():
            for arm in ('v3', 'v4'):
                rows = [r for r in strata if r['phase'] == phase and r['provider_slot'] == opaque and r['arm'] == arm]
                arms.append({'phase': phase, 'provider_slot': opaque, 'arm': arm, **_sum(rows)})
            pair = dict.fromkeys(('planned_pairs', 'both_exact', 'only_v3_exact', 'only_v4_exact',
                                  'neither_exact', 'unscorable_pairs'), 0)
            for case in plan['cases']:
                if case['oracle']['split'] != phase:
                    continue
                v3, v4 = (outcomes[(case['id'], slot, arm)] for arm in ('v3', 'v4'))
                pair['planned_pairs'] += 1
                category = {(1, 1): 'both_exact', (1, 0): 'only_v3_exact',
                            (0, 1): 'only_v4_exact', (0, 0): 'neither_exact'}[
                                (v3['exact_matches'], v4['exact_matches'])]
                pair[category] += 1
                pair['unscorable_pairs'] += int(not v3['valid'] or not v4['valid'])
            paired.append({'phase': phase, 'provider_slot': opaque, **pair})
    development = _candidate_rule(strata, 'development')
    evaluation = development and _candidate_rule(strata, 'evaluation')
    return {'schema_version': 'addressed-comparison-audit/v1', 'mode': 'offline_supplied_responses',
            **AUTHORITY, 'usage_cost_verified': False,
            'totals': _sum(strata), 'arms': arms, 'strata': strata, 'paired': paired,
            'first_error_counts': dict(sorted(errors.items())),
            'candidate_response_rules': {
                'development': 'met_offline_only' if development else 'not_met',
                'evaluation': 'met_offline_only' if evaluation else 'not_met'}}
