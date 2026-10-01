"""Offline accounting audit; never imports collectors or calls a provider.

This reconciles public records. It cannot authenticate private artifacts or
establish that a visible contextual cue caused an observed behavior.
"""
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALUABLE = {'pass', 'target_only_failure'}


def compare(old, new):
    if old not in EVALUABLE or new not in EVALUABLE:
        return 'unknown'
    if old == new:
        return 'equal'
    return 'improved' if new == 'pass' else 'worsened'


def audit_pairs(data):
    seen, counts, ties = set(), Counter(), Counter()
    for row in data['pairs']:
        key = (row['model'], row['replication'])
        if key in seen:
            raise ValueError(f'duplicate paired identity: {key}')
        seen.add(key)
        actual = compare(row['old'], row['new'])
        if actual != row['comparison']:
            raise ValueError(f'pair classification mismatch: {key}')
        counts[actual] += 1
        if actual == 'equal':
            ties[row['old']] += 1
    if len(seen) != 6:
        raise ValueError('expected six nested pairs, not six requirements')
    if 'comparison_counts' in data and dict(counts) != data['comparison_counts']:
        raise ValueError('comparison totals mismatch')
    return {'pairs': len(seen), 'comparisons': dict(counts), 'equal_outcomes': dict(ties)}


def audit_browser_rows(path):
    data = json.loads(path.read_text())
    seen, counts, hashes = set(), defaultdict(lambda: defaultdict(Counter)), 0
    for row in data['browser_rows']:
        key = (row['model'], row['arm'], row['replication'])
        if key in seen:
            raise ValueError(f'duplicate browser identity: {key}')
        seen.add(key)
        counts[row['model']][row['arm']][row['category']] += 1
        if 'report' in row and 'report_sha256' in row:
            report = path.parent / row['report']
            if hashlib.sha256(report.read_bytes()).hexdigest() != row['report_sha256']:
                raise ValueError(f'report hash mismatch: {report}')
            hashes += 1
    expected = { (model, arm, rep) for model in ('gpt-5.6-luna', 'gpt-5.6-sol')
                 for arm in ('A', 'B', 'C') for rep in (1, 2, 3) }
    if seen != expected:
        raise ValueError(f'incomplete or unexpected schedule: {path}')
    if json.loads(json.dumps(counts)) != data['counts']:
        raise ValueError(f'arm counts mismatch: {path}')
    return {'counts': counts, 'report_hashes_verified': hashes}


def audit(root=ROOT):
    paired, inventories, controlled = {}, 0, {}
    for path in sorted(root.glob('data/e2e-decontamination-*/*/analysis-summary.json')):
        paired[str(path.relative_to(root))] = audit_pairs(json.loads(path.read_text()))
        inventory = path.parent / 'SHA256SUMS.json'
        for name, digest in json.loads(inventory.read_text()).items():
            if hashlib.sha256((path.parent / name).read_bytes()).hexdigest() != digest:
                raise ValueError(f'public inventory mismatch: {path.parent / name}')
            inventories += 1
    cases = [('kanboard-duplicate-title', 'secure-replication-20260926'),
             ('paperless-duplicate-consumption', 'results-20260926'),
             ('realworld-favorites', 'results-20260926'),
             ('openproject-invalid-remaining', 'results-20260926'),
             ('paperless-nested-tags', 'results-20260927'),
             ('kanboard-closed-filter', 'results-20260927'),
             ('nextcloud-restore-conflict', 'results-20260927'),
             ('todomvc-persistence-bridge', 'results-20260926')]
    for case, lot in cases:
        path = root / f'data/e2e-{case}/{lot}/summary.json'
        controlled[case] = audit_browser_rows(path)
    closure = root / 'data/e2e-decontamination-20260930/historical-26-closure.csv'
    rows = list(csv.DictReader(closure.open()))
    tested = [r for r in rows if r['disposition'] == 'tested']
    if len({r['requirement_group'] for r in tested}) != len(tested):
        raise ValueError('duplicate requirement in historical closure')
    return {'schema_version': 'e2e-public-accounting-audit/v1',
            'scope': 'Public packet accounting only; no private seal or causal validation.',
            'paired_packets': paired, 'public_inventory_hashes_verified': inventories,
            'controlled_packets': controlled,
            'historical_registry_dispositions': dict(Counter(r['disposition'] for r in rows)),
            'historical_registry_unique_tested_requirements': len(tested),
            'confirmatory_eligible': False}


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2, sort_keys=True))
