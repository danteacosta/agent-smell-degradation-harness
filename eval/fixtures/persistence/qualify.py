"""Qualify TodoMVC persistence controls in an immutable offline browser image."""
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
from eval.persistence_executor import execute

EXPECTED = {
    'omit-edit-state': ('pass', []),
    'store-false-flag': ('pass', []),
    'encoded-value': ('pass', []),
    'restore-edit': ('target_only_failure', ['editing_not_restored']),
    'no-edit': ('target_not_evaluable', []),
    'no-edit-button': ('target_not_evaluable', []),
    'no-reload': ('target_not_evaluable', ['todo_survives_reload', 'completed_survives_reload']),
    'drop-completed': ('non_target_only_failure', ['completed_survives_reload']),
}
MODES = {'omit-edit-state': 'omit', 'store-false-flag': 'false-flag',
         'encoded-value': 'encoded-value',
         'restore-edit': 'restore-edit', 'no-edit': 'no-edit',
         'no-edit-button': 'no-edit-button', 'no-reload': 'no-reload',
         'drop-completed': 'drop-completed'}


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
        (inputs / 'app.html').write_text(template.replace('MODE', MODES[name]))
        output = args.output / name / 'output'
        receipt = execute(args.image, inputs, output)
        raw = json.loads((output / 'report.json').read_text())
        failures = [case['id'] for case in raw.get('cases', []) if case['status'] == 'failed']
        target = next((case for case in raw.get('cases', [])
                       if case['id'] == 'editing_not_restored'), {})
        rows.append({'id': name, 'expected_category': expected_category,
                     'observed_category': receipt['category'],
                     'expected_failures': expected_failures, 'observed_failures': failures,
                     'expected_target_reason': ('todo_missing_after_reload' if name == 'no-reload'
                                                else 'edit_interface_unavailable' if name in {'no-edit', 'no-edit-button'}
                                                else None),
                     'observed_target_reason': target.get('reason'),
                     'receipt_sha256': digest(output / 'executor.json'),
                     'report_sha256': digest(output / 'report.json'),
                     'screenshot_sha256': {filename: digest(output / filename)
                         for filename in ('before-edit.png', 'editing.png', 'after-reload.png')
                         if (output / filename).is_file()}})
    paths = sorted(path for path in fixture_dir.iterdir() if path.is_file())
    paths.append(ROOT / 'eval/persistence_executor.py')
    qualified = all(row['expected_category'] == row['observed_category']
                    and row['expected_failures'] == row['observed_failures']
                    and row['expected_target_reason'] == row['observed_target_reason']
                    for row in rows)
    report = {'schema_version': 'persistence-qualification/v1', 'qualified': qualified,
              'image_id': args.image, 'cases': rows,
              'files': {str(path.relative_to(ROOT)): digest(path) for path in paths},
              'limitations': 'Authored controls qualify browser-visible restoration, not serialized-byte absence or a model-smell effect.'}
    (args.output / 'qualification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'qualified': qualified, 'path': str(args.output / 'qualification.json')}))
    return 0 if qualified else 1


if __name__ == '__main__':
    raise SystemExit(main())
