"""Construction agreement and interface validity, without semantic promotion."""
from __future__ import annotations

from eval.addressed_comparison_plan import ComparisonError, PHASES
from label_plane import qualified_judge

ARMS = ('v4', 'v5')
COUNTS = ('planned', 'observed', 'missing', 'valid', 'invalid', 'exact_matches', 'aggregate_matches')
REQUIRED = ('long_omission', 'partial_missing', 'partial_complete', 'partial_contradiction')


def _sum(rows):
    rows = list(rows)
    return {key: sum(row[key] for row in rows) for key in COUNTS}


def _score(case, arm, receipt):
    counts = dict.fromkeys(COUNTS, 0)
    counts['planned'] = 1
    if receipt is None:
        counts['missing'] = 1
        return counts
    counts['observed'] = 1
    try:
        parsed = qualified_judge.parse_response(receipt.get('response'), case['item'], arm)
    except (ValueError, TypeError, RecursionError):
        counts['invalid'] = 1
        return counts
    counts['valid'] = 1
    counts['aggregate_matches'] = int(parsed['status'] == case['oracle']['status'])
    counts['exact_matches'] = int([c['status'] for c in parsed['checks']] == case['oracle']['checks'])
    return counts


def _passes(rows):
    if not rows or any(row['missing'] for row in rows):
        return False
    slots = {row['provider_slot'] for row in rows}
    if len(slots) != 2:
        return False
    for slot in slots:
        candidate = [r for r in rows if r['provider_slot'] == slot and r['arm'] == 'v5']
        total = _sum(candidate)
        if (not candidate or total['valid'] != total['planned']
                or total['exact_matches'] * 6 < total['planned'] * 5):
            return False
        for operation in REQUIRED:
            subtotal = _sum(r for r in candidate if r['operation'] == operation)
            if not subtotal['planned'] or subtotal['exact_matches'] != subtotal['planned']:
                return False
    return True


def audit(plan, completed):
    if not set(completed) <= {c['id'] for c in plan['calls']}:
        raise ComparisonError('invalid_completed_inventory')
    cases = {c['id']: c for c in plan['cases']}
    slots = {s['id']: f'provider_{i+1}' for i, s in enumerate(plan['providers'])}
    sources = {s: f'source_{i+1}' for i, s in enumerate(dict.fromkeys(
        c['oracle']['source_intent_id'] for c in plan['cases']))}
    projects = {p: f'project_{i+1}' for i, p in enumerate(dict.fromkeys(
        c['oracle']['project_id'] for c in plan['cases']))}
    strata, outcomes = [], {}
    for call in plan['calls']:
        case_id, arm, slot = call['id'].split(':', 2)
        case = cases[case_id]
        counts = _score(case, arm, completed.get(call['id']))
        outcomes[(case_id, arm, slot)] = counts
        strata.append({'phase': call['phase'], 'provider_slot': slots[slot], 'arm': arm,
                       'source_group': sources[case['oracle']['source_intent_id']],
                       'project_group': projects[case['oracle']['project_id']],
                       'operation': case['oracle']['operation'], **counts})
    arms, paired = [], []
    for phase in PHASES:
        for slot, opaque in slots.items():
            for arm in ARMS:
                arms.append({'phase': phase, 'provider_slot': opaque, 'arm': arm, **_sum(
                    r for r in strata if r['phase'] == phase and r['provider_slot'] == opaque and r['arm'] == arm)})
            keys = ('planned_pairs', 'both_valid_pairs', 'unscorable_pairs', 'both_exact',
                    'only_v4_exact', 'only_v5_exact', 'neither_exact', 'both_valid_both_exact',
                    'both_valid_only_v4_exact', 'both_valid_only_v5_exact', 'both_valid_neither_exact')
            pair = dict.fromkeys(keys, 0)
            for case in (c for c in plan['cases'] if c['oracle']['split'] == phase):
                v4, v5 = (outcomes[(case['id'], arm, slot)] for arm in ARMS)
                category = {(1, 1): 'both_exact', (1, 0): 'only_v4_exact',
                            (0, 1): 'only_v5_exact', (0, 0): 'neither_exact'}[
                                v4['exact_matches'], v5['exact_matches']]
                pair['planned_pairs'] += 1
                pair[category] += 1
                if v4['valid'] and v5['valid']:
                    pair['both_valid_pairs'] += 1
                    pair['both_valid_' + category] += 1
                else:
                    pair['unscorable_pairs'] += 1
            paired.append({'phase': phase, 'provider_slot': opaque, **pair})
    passed = {p: _passes([r for r in strata if r['phase'] == p]) for p in PHASES}
    passed['evaluation'] = passed['development'] and passed['evaluation']
    return {'schema_version': 'qualified-comparison-audit/v1', 'usage_cost_verified': False,
            'main_collection_released': False, 'semantic_validity': 'not_measured',
            'totals': _sum(strata), 'arms': arms, 'strata': strata, 'paired': paired,
            'candidate_passed': passed}
