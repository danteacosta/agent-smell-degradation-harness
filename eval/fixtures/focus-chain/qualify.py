"""Run the bounded, authored instrument controls; no model calls."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from eval.focus_chain_executor import execute

EXPECTED = {
    'reference-autofocus': 'pass',
    'reference-imperative': 'pass',
    'mutant-no-focus': 'target_only_failure',
    'mutant-no-clear': 'non_target_only_failure',
    'control-page-tamper': 'target_only_failure',
    'reference-formatted-labels': 'pass',
    'mutant-hidden-labels': 'non_target_only_failure',
    'mutant-no-trim': 'non_target_only_failure',
    'control-interface-missing-label': 'interface_error',
}

EXPECTED_FAILURES = {
    'reference-autofocus': [], 'reference-imperative': [], 'reference-formatted-labels': [],
    'mutant-no-focus': ['initial_focus'], 'control-page-tamper': ['initial_focus'],
    'mutant-no-clear': ['input_cleared'],
    'mutant-hidden-labels': ['enter_append', 'trimmed_title'],
    'mutant-no-trim': ['trimmed_title', 'whitespace_rejected'],
    'control-interface-missing-label': [],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False, mode=0o700)
    fixture_dir = Path(__file__).resolve().parent
    cases = []
    for name, expected in EXPECTED.items():
        inputs = args.output/name/'inputs'
        inputs.mkdir(parents=True)
        shutil.copyfile(fixture_dir/f'{name}.html', inputs/'app.html')
        output = args.output/name/'output'
        receipt = execute(args.image, inputs, output)
        observed_failures = [case['id'] for case in json.loads((output/'report.json').read_text())['cases'] if case['status'] == 'failed']
        cases.append({'expected_failures':EXPECTED_FAILURES[name], 'observed_failures':observed_failures, 'id':name, 'expected':expected, 'observed':receipt['category'],
                      'evidence_dir':str(output.resolve()),
                      'receipt_sha256':hashlib.sha256((output/'executor.json').read_bytes()).hexdigest(),
                      'report_sha256':hashlib.sha256((output/'report.json').read_bytes()).hexdigest()})
    paths = sorted(path for path in fixture_dir.iterdir() if path.is_file())
    paths.append(ROOT/'eval/focus_chain_executor.py')
    report = {'schema_version':'focus-chain-qualification/v1',
              'qualified':all(case['expected'] == case['observed'] and case['expected_failures'] == case['observed_failures'] for case in cases),
              'image_id':args.image, 'cases':cases,
              'files':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
              'limitations':'Authored instrument controls, not LLM outcomes or proof against hostile browser exploits. Chromium sandbox disabled; Docker is the containment boundary.'}
    (args.output/'qualification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'qualified':report['qualified'],'path':str(args.output/'qualification.json')}))
    return 0 if report['qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
