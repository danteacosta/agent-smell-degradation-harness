"""Offline accounting audit; never imports collectors or calls a provider.

This reconciles public records. It cannot authenticate private artifacts or
establish that a visible contextual cue caused an observed behavior.
"""
import argparse
import importlib.util
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


RECENT_PACKETS = (
    ('data/e2e-replications-20261001/realworld-favorites', 'realworld-favorites'),
    ('data/e2e-replications-20261001/openproject-invalid-remaining', 'openproject-invalid-remaining'),
    ('data/e2e-replications-20261001/paperless-duplicate-consumption', 'paperless-duplicate-consumption'),
    ('data/e2e-todomvc-clear-button/replication-20261001', 'todomvc-clear-button-v5'),
    ('data/e2e-realworld-comment-delete/replication-20261001', 'realworld-comment-delete'),
    ('data/e2e-paperless-inbox-suggestions/replication-20261001-v3', 'paperless-inbox-suggestions'),
)


def _packet_file(packet, name):
    path = packet / name
    if Path(name).is_absolute() or '..' in Path(name).parts or path.is_symlink():
        raise ValueError('unsafe public packet path')
    if not path.resolve().is_relative_to(packet.resolve()) or not path.is_file():
        raise ValueError('missing or escaped public packet file')
    return path


def audit_recent_packet(packet, classify):
    """Reclassify stored observations, not browser execution or provider replay."""
    summary = json.loads((packet / 'summary.json').read_text())
    inventory = json.loads((packet / 'receipt.json').read_text())['files']
    if 'summary.json' not in inventory:
        raise ValueError('receipt must bind summary')
    for name, digest in inventory.items():
        if hashlib.sha256(_packet_file(packet, name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'public receipt mismatch: {name}')
    rows = summary.get('browser_rows', summary.get('rows'))
    expected = {(m, a, r) for m in ('gpt-5.6-luna', 'gpt-5.6-sol')
                for a in ('A', 'B', 'C') for r in (1, 2, 3)}
    seen, counts, by_pair = set(), defaultdict(lambda: defaultdict(Counter)), defaultdict(dict)
    for row in rows:
        key = (row['model'], row['arm'], row['replication'])
        if key in seen:
            raise ValueError('duplicate browser identity')
        seen.add(key)
        name = row.get('report', row.get('browser_report',
            f"reports/{key[0]}-{key[1]}-rep{key[2]}.json"))
        digest = row.get('report_sha256', row.get('browser_report_sha256'))
        if not digest or inventory.get(name) != digest:
            raise ValueError('report must be bound by row and receipt')
        report = json.loads(_packet_file(packet, name).read_text())
        category = classify(report)
        if category != row['category']:
            raise ValueError('classification mismatch')
        if 'generated_html_sha256' in row and report.get('app_sha256') != row['generated_html_sha256']:
            raise ValueError('generated artifact identity mismatch')
        counts[key[0]][key[1]][category] += 1
        by_pair[(key[0], key[2])][key[1]] = category
    if seen != expected or summary['planned_slots'] != 18 or summary['attempted_calls'] != 18:
        raise ValueError('incomplete or unexpected completed schedule')
    if json.loads(json.dumps(counts)) != summary['counts']:
        raise ValueError('arm counts mismatch')
    contrasts = Counter()
    for arms in by_pair.values():
        if any(arms[arm] not in EVALUABLE for arm in ('A', 'B', 'C')):
            contrasts['unknown'] += 1
        elif arms['A'] == arms['B'] == 'pass':
            contrasts['C_target_failure_with_AB_pass' if arms['C'] == 'target_only_failure'
                      else 'all_pass'] += 1
        else:
            contrasts['AB_not_both_pass'] += 1
    return {'rows_verified': len(rows), 'public_files_verified': len(inventory),
            'counts': counts, 'nested_triplets': dict(contrasts)}


def audit_recent(root=ROOT):
    packets = {}
    for relative, fixture in RECENT_PACKETS:
        qualifier = root / 'eval/fixtures' / fixture / 'qualify.py'
        spec = importlib.util.spec_from_file_location('offline_qualifier', qualifier)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = audit_recent_packet(root / relative, module.classify)
        result['classifier_sha256'] = hashlib.sha256(qualifier.read_bytes()).hexdigest()
        packets[relative] = result
    return {'schema_version': 'e2e-recent-public-audit/v1',
            'scope': 'Six completed public lots; classifications replayed from stored reports. No new browser or provider execution; private custody unverified.',
            'confirmatory_eligible': False, 'packets': packets}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recent', action='store_true', help='Audit the six completed October 1 lots separately')
    args = parser.parse_args()
    print(json.dumps(audit_recent() if args.recent else audit(), indent=2, sort_keys=True))
