"""Original auxiliary construction oracles; no natural-requirement validation."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from label_plane.judge_controls import fingerprint


def contracts():
    specs = [
        ('numeric_limit', 'amount', 'lte', 100, 'lt', 100, [(99, True), (100, True), (101, False), (0, True)]),
        ('permission', 'role', 'eq', 'admin', 'ne', 'admin', [('admin', True), ('guest', False), ('editor', False), ('viewer', False)]),
        ('state', 'status', 'eq', 'approved', 'eq', 'pending', [('approved', True), ('pending', False), ('rejected', False), ('closed', False)]),
        ('precondition', 'authenticated', 'eq', True, 'eq', False, [(True, True), (False, False), (True, True), (False, False)]),
    ]
    return [{'id': name, 'contract': {'field': field, 'operator': op, 'value': value},
             'mutant': {'field': field, 'operator': mutant_op, 'value': mutant_value},
             'vectors': [{'inputs': {field: x}, 'expected': expected} for x, expected in vectors]}
            for name, field, op, value, mutant_op, mutant_value, vectors in specs]


def evaluate(contract, inputs):
    if not isinstance(contract, dict) or set(contract) != {'field', 'operator', 'value'}:
        raise ValueError('contract must contain only field, operator and value')
    field, op, expected = contract['field'], contract['operator'], contract['value']
    if not isinstance(field, str) or not isinstance(inputs, dict) or field not in inputs:
        raise ValueError('contract input is missing')
    actual = inputs[field]
    if op in {'lt', 'lte'}:
        if any(type(v) not in {int, float} or not math.isfinite(v) for v in (actual, expected)):
            raise ValueError('numeric comparison requires finite numbers, excluding booleans')
        return actual < expected if op == 'lt' else actual <= expected
    if op in {'eq', 'ne'}:
        if type(expected) not in {str, bool} or type(actual) is not type(expected):
            raise ValueError('categorical equality requires matching string or boolean types')
        return actual == expected if op == 'eq' else actual != expected
    raise ValueError('unsupported contract operator')


def audit_contracts():
    pack = contracts()
    rows = []
    for case in pack:
        correct = [evaluate(case['contract'], v['inputs']) == v['expected'] for v in case['vectors']]
        mutations = [evaluate(case['mutant'], v['inputs']) != v['expected'] for v in case['vectors']]
        rows.append({'id': case['id'], 'passed': sum(correct), 'total': len(correct),
                     'mutant_killed': any(mutations), 'mutant_detecting_vectors': sum(mutations)})
    return {'schema_version': 'executable-controls/v1', 'pack_sha256': fingerprint(pack),
            'scope': 'original_synthetic_contracts', 'natural_language_validated': False,
            'confirmatory_eligible': False, 'contracts': len(rows),
            'vectors_total': sum(r['total'] for r in rows),
            'vectors_passed': sum(r['passed'] for r in rows),
            'mutants_killed': sum(r['mutant_killed'] for r in rows), 'results': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = audit_contracts()
    rendered = json.dumps(report, indent=2, sort_keys=True) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as handle:
            handle.write(rendered)
    print(rendered, end='')
