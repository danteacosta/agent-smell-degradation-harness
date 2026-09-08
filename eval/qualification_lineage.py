"""Read a completed predecessor through its unchanged runtime, without credentials."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

from eval import scoped_judge_study as historical
from eval.addressed_comparison_custody import claim_path, file_hash
from eval.addressed_comparison_plan import ComparisonError, read_json, safe_path
from eval.pilot_preparation import digest
from label_plane.evidence_json import load_json

MAX_REPORT_BYTES = 512_000


def verify_files(files):
    if any(file_hash(path) != expected for path, expected in files.items()):
        raise ComparisonError('custody_changed')


def verify_runtime(root, expected):
    root = safe_path(root)
    required = {'eval/addressed_comparison_live.py', 'eval/addressed_comparison_custody.py',
                'label_plane/addressed_judge.py', 'label_plane/scoped_judge.py'}
    if not isinstance(expected, dict) or not required <= expected.keys():
        raise ComparisonError('frozen_runtime_changed')
    actual = {str(p.relative_to(root)): file_hash(p) for folder in historical.SOURCE_DIRS
              for p in sorted((root / folder).rglob('*.py'))}
    if actual != expected:
        raise ComparisonError('frozen_runtime_changed')


def _report(directory, runtime):
    # Match module execution with the verified project on the import path,
    # including editable-install metadata. Never inherit the caller's path.
    env = {'PATH': os.defpath, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8',
           'PYTHONPATH': str(runtime)}
    command = [sys.executable, '-m', 'eval.addressed_comparison_live', 'report', '--directory', str(directory)]
    try:
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
            result = subprocess.run(command, cwd=runtime, env=env, stdout=output, stderr=errors, timeout=20)
            output.seek(0)
            raw = output.read(MAX_REPORT_BYTES + 1)
        if result.returncode or len(raw) > MAX_REPORT_BYTES:
            raise ValueError
        report = load_json(raw.decode('utf-8'))
        if not isinstance(report, dict) or report.get('schema_version') != 'addressed-comparison-live-report/v1':
            raise ValueError
        return report
    except (OSError, ValueError, TypeError, RecursionError, subprocess.TimeoutExpired) as exc:
        raise ComparisonError('invalid_predecessor_report') from exc


def predecessor_snapshot(directory, runtime):
    directory, runtime = safe_path(directory), safe_path(runtime)
    manifest = read_json(directory / 'manifest.json')
    plan = manifest['plan']
    verify_runtime(runtime, plan['source_sha256'])
    parent = safe_path(plan['parent']['directory'])
    grandparent = safe_path(plan['predecessor_directory'])
    paths = list(plan['custody_sha256']) + [str(directory / name) for name in
            ('manifest.json', 'manifest-integrity.json', 'closure.json', 'ledger.jsonl', 'ledger.jsonl.lock')]
    paths += [str(claim_path(plan)), str(parent / 'ledger.jsonl.lock'), str(grandparent / 'ledger.jsonl.lock')]
    files = {path: file_hash(path) for path in paths}
    report = _report(directory, runtime)
    verify_files(files)
    verify_runtime(runtime, plan['source_sha256'])
    accounting = report['accounting']
    if (accounting['state'] != 'ready' or accounting['pending_attempts']
            or accounting['reconciled_completions'] != 48 or accounting['observed_provider_outcomes'] != 48
            or accounting['reserved_attempts'] != 48 or accounting['unattempted_calls'] != 96
            or report['phases'] != {'development': 'pause', 'evaluation': 'pause'}
            or report['main_collection_released'] is not False):
        raise ComparisonError('predecessor_not_closable')
    return {'lineage': {'directory': str(directory), 'runtime': str(runtime),
                        'ancestors': [str(parent), str(grandparent)], 'custody_sha256': files,
                        'source_sha256': plan['source_sha256'], 'report_sha256': digest(report)},
            'report': report, 'providers': plan['providers'],
            'seeds': read_json(grandparent / 'manifest.json')['seeds'],
            'old_cases': plan['cases']}
