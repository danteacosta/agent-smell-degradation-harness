"""Offline temporal diagnostics on a predeclared alert policy, never H2 training.

Input times are milliseconds from the same monotonic episode origin. Costs are
incremental per-stage integer micro-USD, including measured failed attempts.
Terminal labels are used only after alert collection and must be identified
externally as construction, machine, or human labels.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

STAGES = ('T1', 'T2', 'T3')


def _time(value):
    if type(value) not in {int, float} or not math.isfinite(value) or value < 0:
        raise ValueError('timestamps must be finite nonnegative milliseconds')
    return value


def analyze(rows):
    episodes = []
    seen = set()
    horizons = {}
    for horizon in range(1, 4):
        horizons['+'.join(STAGES[:horizon])] = {
            'planned_episodes': len(rows), 'complete_stage_episodes': 0,
            'missing_stage_episodes': 0, 'outcome_labeled_episodes': 0,
            'nondefective_labeled_episodes': 0, 'alerts': 0, 'false_alerts': 0,
            'cost_microusd': 0, 'known_cost_microusd': 0,
            'missing_cost_episodes': 0, 'false_alert_rate': None}
    for row in rows:
        identifier = row['episode_id']
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            raise ValueError('episode ids must be unique nonempty strings')
        seen.add(identifier)
        if not isinstance(row.get('intent_id'), str) or not row['intent_id']:
            raise ValueError('intent identity is required for clustered future analysis')
        terminal = _time(row['terminal_ms'])
        defect = row['terminal_defect']
        if defect is not None and type(defect) is not bool:
            raise ValueError('terminal_defect must be a boolean or null')
        stages = {}
        for observation in row['stages']:
            stage = observation['stage']
            if stage not in STAGES or stage in stages:
                raise ValueError('unsupported or duplicate stage')
            if _time(observation['available_ms']) >= terminal:
                raise ValueError('stage observation must precede the terminal artifact')
            if type(observation['alert']) is not bool:
                raise ValueError('stage alert must be boolean; omit unavailable stages')
            cost = observation['cost_microusd']
            if cost is not None and (type(cost) is not int or cost < 0):
                raise ValueError('cost must be nonnegative integer micro-USD or null')
            stages[stage] = observation
        times = [stages[s]['available_ms'] for s in STAGES if s in stages]
        if times != sorted(times):
            raise ValueError('stages must be temporally ordered')
        first = next((stages[s] for s in STAGES if s in stages and stages[s]['alert']), None)
        episodes.append({'episode_id': identifier, 'intent_id': row['intent_id'],
                         'first_alert_stage': first['stage'] if first else None,
                         'lead_time_ms': terminal-first['available_ms'] if first else None,
                         'observation_complete': len(stages) == 3})
        for horizon, result in horizons.items():
            required = horizon.split('+')
            if any(s not in stages for s in required):
                result['missing_stage_episodes'] += 1
                continue
            result['complete_stage_episodes'] += 1
            alert = any(stages[s]['alert'] for s in required)
            result['alerts'] += alert
            result['outcome_labeled_episodes'] += defect is not None
            result['nondefective_labeled_episodes'] += defect is False
            result['false_alerts'] += alert and defect is False
            costs = [stages[s]['cost_microusd'] for s in required]
            if any(c is None for c in costs):
                result['missing_cost_episodes'] += 1
            else:
                result['known_cost_microusd'] += sum(costs)
    for result in horizons.values():
        n = result['nondefective_labeled_episodes']
        result['false_alert_rate'] = result['false_alerts']/n if n else None
        result['cost_microusd'] = (None if result['missing_cost_episodes'] or result['missing_stage_episodes']
                                   else result['known_cost_microusd'])
    return {'schema_version': 'temporal-diagnostics/v1', 'confirmatory_eligible': False,
            'policy': 'any_predeclared_alert_in_available_prefix',
            'distinct_intents': len({r['intent_id'] for r in rows}),
            'horizons': horizons, 'episodes': episodes}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--episodes', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.episodes.read_text().splitlines() if line.strip()]
    report = analyze(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write('\n')
    print(json.dumps({'schema_version': report['schema_version'], 'horizons': report['horizons']}))
