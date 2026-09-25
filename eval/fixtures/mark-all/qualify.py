"""Qualify authored TodoMVC Mark all controls in a pinned offline browser image."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from eval.mark_all_executor import execute

EXPECTED = {
    'reference-explicit': ('pass', []),
    'reference-derived': ('pass', []),
    'reference-hidden-clear': ('pass', []),
    'reference-nested-reversed': ('pass', []),
    'reference-extra-checkbox': ('pass', []),
    'reference-hidden-master': ('pass', []),
    'mutant-hidden-stale-master': ('target_only_failure', ['clear_master_after_clear_completed']),
    'control-ambiguous-master': ('pass', []),
    'control-duplicate-master': ('target_not_evaluable', []),
    'mutant-stale-master': ('target_only_failure', ['clear_master_after_clear_completed']),
    'mutant-replacement-stale-master': ('target_only_failure', ['clear_master_after_clear_completed']),
    'mutant-no-individual-sync': ('non_target_only_failure', ['master_tracks_individuals']),
    'mutant-no-bulk': ('target_not_evaluable', ['master_sets_items']),
    'mutant-no-clear': ('target_not_evaluable', ['clear_completed_removes_items']),
    'mutant-interface-missing-master': ('interface_error', []),
}
EXPECTED_REASONS = {'mutant-no-bulk': 'bulk_selection_failed',
                    'mutant-no-clear': 'clear_failed',
                    'control-duplicate-master': 'master_identity_ambiguous'}
EXPECTED_CLEAR_REASONS = {'mutant-no-bulk': 'bulk_selection_failed'}


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
    rows = []
    for name, (expected_category, expected_failures) in EXPECTED.items():
        inputs = args.output / name / 'input'
        inputs.mkdir(parents=True)
        shutil.copyfile(fixture_dir / f'{name}.html', inputs / 'app.html')
        output = args.output / name / 'output'
        receipt = execute(args.image, inputs, output)
        raw = json.loads((output / 'report.json').read_text())
        failures = [case['id'] for case in raw.get('cases', []) if case['status'] == 'failed']
        target = next((case for case in raw.get('cases', [])
                       if case['id'] == 'clear_master_after_clear_completed'), {})
        clear_case = next((case for case in raw.get('cases', [])
                           if case['id'] == 'clear_completed_removes_items'), {})
        rows.append({'id': name, 'expected_category': expected_category,
                     'observed_category': receipt['category'],
                     'expected_failures': expected_failures, 'observed_failures': failures,
                     'expected_target_reason': EXPECTED_REASONS.get(name),
                     'observed_target_reason': target.get('reason'),
                     'expected_clear_reason': EXPECTED_CLEAR_REASONS.get(name),
                     'observed_clear_reason': clear_case.get('reason'),
                     'receipt_sha256': digest(output / 'executor.json'),
                     'report_sha256': digest(output / 'report.json'),
                     'screenshot_sha256': {filename: digest(output / filename)
                         for filename in ('after-clear.png', 'before-target.png', 'after-target.png')
                         if (output / filename).is_file()}})
    paths = sorted(path for path in fixture_dir.iterdir() if path.is_file())
    paths.append(ROOT / 'eval/mark_all_executor.py')
    qualified = all(row['expected_category'] == row['observed_category']
                    and row['expected_failures'] == row['observed_failures']
                    and row['expected_target_reason'] == row['observed_target_reason']
                    and row['expected_clear_reason'] == row['observed_clear_reason']
                    for row in rows)
    report = {'schema_version': 'mark-all-qualification/v3', 'qualified': qualified,
              'image_id': args.image, 'cases': rows,
              'files': {str(path.relative_to(ROOT)): digest(path) for path in paths},
              'limitations': 'Authored controls qualify this bounded oracle, not a source-smell effect or universal browser escape safety.'}
    (args.output / 'qualification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'qualified': qualified, 'path': str(args.output / 'qualification.json')}))
    return 0 if qualified else 1


if __name__ == '__main__':
    raise SystemExit(main())
