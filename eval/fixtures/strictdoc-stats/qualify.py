"""Qualify authored StrictDoc statistics screens in the pinned offline browser."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from eval.strictdoc_stats_executor import execute

EXPECTED = {
    'iso': ('pass', []),
    'portuguese': ('pass', []),
    'french': ('pass', []),
    'short-month': ('pass', []),
    'iso-timestamp': ('pass', []),
    'below-fold': ('pass', []),
    'pointer-events-none': ('pass', []),
    'aria-hidden': ('pass', []),
    'callable-date': ('pass', []),
    'omit-date': ('target_only_failure', ['generation_date_visible']),
    'wrong-date': ('target_only_failure', ['generation_date_visible']),
    'hidden-date': ('target_only_failure', ['generation_date_visible']),
    'transparent': ('target_only_failure', ['generation_date_visible']),
    'clipped': ('target_only_failure', ['generation_date_visible']),
    'covered': ('target_only_failure', ['generation_date_visible']),
    'partially-clipped': ('target_only_failure', ['generation_date_visible']),
    'transparent-neutral': ('interface_error', []),
    'hardcoded-first': ('target_only_failure', ['generation_date_visible']),
    'wrong-revision': ('non_target_only_failure', ['project_identity']),
    'wrong-count': ('non_target_only_failure', ['totals']),
    'missing-handle': ('interface_error', []),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', args.image):
        raise ValueError('immutable Docker image ID required')
    found = subprocess.run(['docker', 'image', 'inspect', '--format', '{{.Id}}', args.image],
                           check=True, capture_output=True, text=True, timeout=30).stdout.strip()
    if found != args.image:
        raise ValueError('image identity mismatch')
    args.output.mkdir(parents=True, exist_ok=False, mode=0o700)
    fixture_dir = Path(__file__).resolve().parent
    template = (fixture_dir / 'control.html').read_text()
    rows = []
    for name, (expected_category, expected_failures) in EXPECTED.items():
        inputs = args.output / name / 'input'
        inputs.mkdir(parents=True)
        (inputs / 'app.html').write_text(template.replace('MODE', name))
        output = args.output / name / 'output'
        receipt = execute(args.image, inputs, output)
        report_path = output / 'report.json'
        raw = json.loads(report_path.read_text()) if report_path.exists() else {}
        failures = [case.get('id') for case in raw.get('cases', [])
                    if case.get('status') == 'failed']
        clock_dates = [item.get('date_visible') for item in raw.get('observations', [])]
        rows.append({'id': name, 'expected_category': expected_category,
                     'observed_category': receipt['category'],
                     'expected_failures': expected_failures, 'observed_failures': failures,
                     'clock_dates': clock_dates,
                     'receipt_sha256': digest(output / 'executor.json'),
                     'report_sha256': digest(report_path) if report_path.exists() else None,
                     'screenshot_sha256': {filename: digest(output / filename)
                         for filename in ('clock-one.png', 'clock-two.png')
                         if (output / filename).is_file()}})
    paths = sorted(path for path in fixture_dir.iterdir() if path.is_file())
    paths.append(ROOT / 'eval/strictdoc_stats_executor.py')
    qualified = all(row['expected_category'] == row['observed_category']
                    and row['expected_failures'] == row['observed_failures']
                    and (row['clock_dates'] == [True, False] if row['id'] == 'hardcoded-first'
                         else True)
                    for row in rows)
    report = {'schema_version': 'strictdoc-stats-qualification/v1',
              'qualified': qualified, 'image_id': args.image, 'cases': rows,
              'files': {str(path.relative_to(ROOT)): digest(path) for path in paths},
              'limitations': 'Authored screen controls qualify only a bounded browser oracle; no generated code or H1/H2 result.'}
    (args.output / 'qualification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'qualified': qualified, 'path': str(args.output / 'qualification.json')}))
    return 0 if qualified else 1


if __name__ == '__main__':
    raise SystemExit(main())
