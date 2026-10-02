"""Supplementary prefix-only structural features and calibration operating point.

No terminal label, text, oracle or total trace length enters structural_features.
This bounded adapter is not a reproduction of the Automata FSM or an H2 model.
"""
from __future__ import annotations

from collections import Counter
import math

STAGES = ('T1', 'T2', 'T3')
ACTIVITIES = {'interpretation.completed', 'plan.completed', 'execution.started',
              'tool.completed', 'retrieval.completed', 'context.compacted'}


def _number(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('expected finite nonnegative number')
    return value


def structural_features(events, *, stage, cutoff_ms):
    """Consume an already isolated feature-plane prefix, rejecting extra fields.

    Input normalization must occur before this adapter and be bound by hash.
    It deliberately rejects future rows instead of using them to select a prefix.
    """
    if stage not in STAGES:
        raise ValueError('unsupported checkpoint')
    cutoff = _number(cutoff_ms)
    previous = -1
    previous_stage = -1
    activities = []
    for event in events:
        if set(event) != {'stage', 'available_ms', 'activity'}:
            raise ValueError('structural event field allowlist violated')
        if event['stage'] not in STAGES or STAGES.index(event['stage']) > STAGES.index(stage):
            raise ValueError('future or terminal stage forbidden')
        stage_index = STAGES.index(event['stage'])
        if stage_index < previous_stage:
            raise ValueError('checkpoint stages must be ordered')
        previous_stage = stage_index
        timestamp = _number(event['available_ms'])
        if timestamp < previous or timestamp > cutoff:
            raise ValueError('nonmonotonic or post-cutoff event')
        if event['activity'] not in ACTIVITIES:
            raise ValueError('unregistered activity; free text forbidden')
        previous = timestamp
        activities.append(event['activity'])
    counts = Counter(activities)
    transitions = Counter(zip(activities, activities[1:]))
    return {'event_count': len(activities), 'unique_activity_count': len(counts),
            'repeated_activity_fraction': ((len(activities) - len(counts)) / len(activities)
                                           if activities else None),
            'activity_counts': dict(sorted(counts.items())),
            'transition_counts': [{'from': a, 'to': b, 'count': n}
                                  for (a, b), n in sorted(transitions.items())]}


def fit_fpr_threshold(scores, labels, *, split, max_fpr):
    """Supplementary recall-at-FPR calibration; existing H2 F1 policy unchanged.

    max_fpr is frozen before observing calibration outcomes. This is an empirical
    calibration bound, not a guarantee on a small held-out project sample.
    """
    if split != 'calibration':
        raise ValueError('threshold fitting requires calibration split')
    if type(max_fpr) not in (int, float) or not math.isfinite(max_fpr) or not 0 <= max_fpr <= 1:
        raise ValueError('invalid FPR budget')
    if not scores or len(scores) != len(labels):
        raise ValueError('nonempty matched scores and labels required')
    if any(type(y) is not int or y not in (0, 1) for y in labels) or set(labels) != {0, 1}:
        raise ValueError('both independent outcome classes required')
    if any(type(s) not in (int, float) or not math.isfinite(s) for s in scores):
        raise ValueError('finite scores required')
    negatives, positives = labels.count(0), labels.count(1)
    candidates = sorted(set(scores), reverse=True)
    # null is a serializable, explicit abstention operating point (no alerts).
    best = {'threshold': None, 'recall': 0.0, 'fpr': 0.0,
            'fit_split': split, 'max_fpr': max_fpr, 'n': len(scores)}
    for threshold in candidates:
        fp = sum(s >= threshold and y == 0 for s, y in zip(scores, labels))
        tp = sum(s >= threshold and y == 1 for s, y in zip(scores, labels))
        fpr, recall = fp / negatives, tp / positives
        if fpr <= max_fpr and recall > best['recall']:
            best.update(threshold=threshold, recall=recall, fpr=fpr)
    return best
