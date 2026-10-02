"""Supplementary comparison of sealed prefix scores with separately held labels.

This consumes scores from frozen detector artifacts, not terminal traces. It
never fits detectors and cannot certify how external score producers operated.
The primary H2 definitions and F1 threshold policy remain unchanged.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from eval.temporal_comparator import fit_fpr_threshold, STAGES
from eval.confirmatory_report import clustered_pr_auc_delta
from protocol.metrics import average_precision

DETECTORS = ('B0', 'B3', 'S-structure')


def _finite(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('finite numeric measurement required')
    return value


def compare(predictions, outcomes, *, max_fpr):
    """Join only after prediction seal; tune an any-prefix policy on calibration.

    Every detector sees exactly the same supplied episodes and checkpoints.
    Incomplete cohorts fail closed rather than silently changing denominators.
    A source/schedule completeness check must precede this function.
    """
    if not predictions or not outcomes:
        raise ValueError('nonempty predictions and independent outcomes required')
    labels = {}
    for row in outcomes:
        if set(row) != {'episode_id', 'constraint_id', 'terminal_defect', 'terminal_ms'}:
            raise ValueError('outcome field allowlist violated')
        if not isinstance(row['constraint_id'], str) or not row['constraint_id'].strip():
            raise ValueError('predeclared target constraint required')
        if row['episode_id'] in labels or type(row['terminal_defect']) is not int or row['terminal_defect'] not in (0, 1):
            raise ValueError('unique independently labeled episodes required')
        if _finite(row['terminal_ms']) <= 0:
            raise ValueError('positive terminal time required')
        labels[row['episode_id']] = row
    seen = set(); project_splits = {}; intent_projects = {}; samples = {'calibration': [], 'test': []}
    for row in predictions:
        if set(row) != {'episode_id', 'project_id', 'intent_id', 'run_id', 'replication_id', 'constraint_id', 'split', 'stages'}:
            raise ValueError('prediction field allowlist violated')
        for key in ('episode_id', 'project_id', 'intent_id', 'run_id', 'replication_id', 'constraint_id'):
            if not isinstance(row[key], str) or not row[key].strip():
                raise ValueError('nonempty identity strings required')
        identifier = row['episode_id']
        if identifier in seen or identifier not in labels:
            raise ValueError('unique matched episodes required')
        if row['constraint_id'] != labels[identifier]['constraint_id']:
            raise ValueError('target constraint mismatch')
        seen.add(identifier)
        split = row['split']; project = row['project_id'].strip().casefold()
        if split not in samples:
            raise ValueError('only calibration and test scores admitted')
        if project_splits.setdefault(project, split) != split:
            raise ValueError('project crosses calibration/test split')
        if intent_projects.setdefault(row['intent_id'], project) != project:
            raise ValueError('related intent crosses project groups')
        observations = row['stages']
        if len(observations) != 3 or [s['stage'] for s in observations] != list(STAGES):
            raise ValueError('all ordered prefix checkpoints required')
        previous = -1
        for observation in observations:
            if set(observation) != {'stage', 'available_ms', 'scores'} or set(observation['scores']) != set(DETECTORS):
                raise ValueError('stage score field allowlist violated')
            time = _finite(observation['available_ms'])
            if time < 0 or time < previous or time >= labels[identifier]['terminal_ms']:
                raise ValueError('prefix observations must be ordered and precede T4')
            previous = time
            for score in observation['scores'].values():
                _finite(score)
        samples[split].append(row)
    if seen != set(labels):
        raise ValueError('unmatched outcomes would change cohort denominator')
    for subset in samples.values():
        if {labels[r['episode_id']]['terminal_defect'] for r in subset} != {0, 1}:
            raise ValueError('both outcome classes required in calibration and test')
    test = samples['test']; calibration = samples['calibration']
    y = [labels[r['episode_id']]['terminal_defect'] for r in test]
    report = {'schema_version': 'temporal-comparison-supplement/v1', 'confirmatory_eligible': False,
              'primary_h2_unchanged': True, 'detectors': {}, 'test_episodes': len(test),
              'test_projects': len({r['project_id'] for r in test}),
              'limitations': ['Input sealing, trained-model provenance and complete schedule require external verification.',
                             'Empirical calibration FPR budget is not a test-set guarantee.',
                             'Project-bootstrap validity gates apply; this engineering pilot is not confirmatory.']}
    max_scores = {}
    for detector in DETECTORS:
        maximum = lambda r: max(s['scores'][detector] for s in r['stages'])
        policy = fit_fpr_threshold([maximum(r) for r in calibration],
                                  [labels[r['episode_id']]['terminal_defect'] for r in calibration],
                                  split='calibration', max_fpr=max_fpr)
        threshold = policy['threshold']; episode_results = []
        for row in test:
            first = next((s for s in row['stages'] if threshold is not None and s['scores'][detector] >= threshold), None)
            positive = labels[row['episode_id']]['terminal_defect'] == 1
            episode_results.append({'episode_id': row['episode_id'], 'project_id': row['project_id'],
                                    'constraint_id': row['constraint_id'], 'alert': first is not None, 'terminal_defect': int(positive),
                                    'first_alert_stage': first['stage'] if first else None,
                                    'lead_time_ms': labels[row['episode_id']]['terminal_ms']-first['available_ms'] if first else None,
                                    'lead_time_scope': 'true_positive' if first and positive else 'false_positive' if first else 'no_alert'})
        negatives = y.count(0); positives = y.count(1)
        max_scores[detector] = [maximum(r) for r in test]
        report['detectors'][detector] = {
            'policy': policy, 'policy_unit': 'episode_any_T1_T2_T3_alert',
            'pr_auc_average_precision_by_stage': {stage: average_precision([r['stages'][i]['scores'][detector] for r in test], y) for i, stage in enumerate(STAGES)},
            'pr_auc_max_prefix_score': average_precision(max_scores[detector], y),
            'recall': sum(r['alert'] and r['terminal_defect'] == 1 for r in episode_results)/positives,
            'fpr': sum(r['alert'] and r['terminal_defect'] == 0 for r in episode_results)/negatives,
            'episodes': episode_results}
    report['project_grouped_deltas'] = {
        'B3_minus_'+baseline: clustered_pr_auc_delta(test, max_scores['B3'], max_scores[baseline], y)
        for baseline in ('B0', 'S-structure')}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--predictions', type=Path, required=True)
    parser.add_argument('--outcomes', type=Path, required=True)
    parser.add_argument('--max-fpr', type=float, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = compare(json.loads(args.predictions.read_text()), json.loads(args.outcomes.read_text()), max_fpr=args.max_fpr)
    report['input_sha256'] = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in [('predictions', args.predictions), ('outcomes', args.outcomes)]}
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
