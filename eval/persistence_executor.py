"""Trusted browser report adapter for the TodoMVC persistence contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import uuid

from eval.focus_chain_executor import container_command

ASSERTION_IDS = ('todo_survives_reload', 'completed_survives_reload',
                 'local_storage_used', 'editing_not_restored')
UNKNOWN_REASONS = {'todo_missing_after_reload', 'todo_not_visible_after_reload'}


def _unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON field')
        result[key] = value
    return result


def classify_report(raw: bytes | None, returncode: int) -> dict:
    invalid = {'category': 'browser_error', 'reason': 'incomplete or inconsistent trusted report'}
    try:
        value = json.loads(raw, object_pairs_hook=_unique_fields) if raw and len(raw) <= 100000 else None
    except (ValueError, TypeError):
        return invalid
    if not isinstance(value, dict) or value.get('schema_version') != 'persistence-browser/v1':
        return invalid
    if not isinstance(value.get('app_sha256'), str) or not re.fullmatch(r'[0-9a-f]{64}', value['app_sha256']):
        return invalid
    if value.get('status') in ('interface_error', 'browser_error'):
        return {'category': value['status'], 'reason': str(value.get('error', ''))[:1500]} if returncode == 2 else invalid
    cases = value.get('cases')
    if (value.get('status') != 'complete' or not isinstance(cases, list)
            or len(cases) != len(ASSERTION_IDS) or any(not isinstance(c, dict) for c in cases)):
        return invalid
    if any(not isinstance(c.get('id'), str) for c in cases):
        return invalid
    indexed = {c['id']: c for c in cases}
    if len(indexed) != len(ASSERTION_IDS) or set(indexed) != set(ASSERTION_IDS):
        return invalid
    target = indexed['editing_not_restored']
    for name in ASSERTION_IDS[:-1]:
        if indexed[name].get('status') not in ('passed', 'failed') or 'reason' in indexed[name]:
            return invalid
    if target.get('status') == 'not_evaluable':
        if target.get('reason') not in UNKNOWN_REASONS:
            return invalid
    elif target.get('status') not in ('passed', 'failed') or 'reason' in target:
        return invalid
    failures = [name for name in ASSERTION_IDS[:-1] if indexed[name]['status'] == 'failed']
    if target['status'] == 'failed':
        failures.append('editing_not_restored')
    if returncode != (1 if failures or target['status'] == 'not_evaluable' else 0):
        return invalid
    non_target = [name for name in failures if name != 'editing_not_restored']
    if target['status'] == 'not_evaluable':
        return {'category': 'target_not_evaluable', 'target_failed': None,
                'non_target_failed': non_target}
    failed = target['status'] == 'failed'
    return {'category': ('mixed_failure' if failed and non_target else
                         'target_only_failure' if failed else
                         'non_target_only_failure' if non_target else 'pass'),
            'target_failed': failed, 'non_target_failed': non_target}


def execute(image: str, inputs: Path, output: Path, timeout: int = 90) -> dict:
    """Run one bounded offline HTML artifact and retain the report and screenshots."""
    output.mkdir(parents=True, exist_ok=False)
    name = 'persistence-' + uuid.uuid4().hex
    command = container_command(image, inputs, output, name)
    app_hash = hashlib.sha256((inputs / 'app.html').read_bytes()).hexdigest()
    (output / 'container-command.json').write_text(json.dumps(command, indent=2))
    try:
        with (output / 'container.log').open('wb') as log:
            try:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                        timeout=timeout, check=False)
                returncode = result.returncode
            except subprocess.TimeoutExpired:
                returncode = 124
    finally:
        subprocess.run(['docker', 'rm', '--force', name], capture_output=True,
                       timeout=30, check=False)
    report_path = output / 'report.json'
    raw = report_path.read_bytes() if report_path.is_file() and not report_path.is_symlink() else None
    outcome = {'category': 'timeout'} if returncode == 124 else classify_report(raw, returncode)
    if raw and returncode != 124:
        try:
            if json.loads(raw).get('app_sha256') != app_hash:
                outcome = {'category': 'browser_error', 'reason': 'executed app hash mismatch'}
        except (ValueError, AttributeError):
            outcome = {'category': 'browser_error', 'reason': 'invalid trusted report'}
    if outcome['category'] in {'pass', 'target_only_failure', 'non_target_only_failure',
                               'mixed_failure', 'target_not_evaluable'}:
        screenshots = [output / name for name in ('before-edit.png', 'editing.png', 'after-reload.png')]
        if any(path.is_symlink() or not path.is_file() or path.stat().st_size > 4000000
               or not path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n') for path in screenshots):
            outcome = {'category': 'browser_error', 'reason': 'missing bounded screenshot'}
        else:
            observation = json.loads(raw).get('target_observation')
            if (not isinstance(observation, dict)
                    or not isinstance(observation.get('storage_keys'), list)
                    or not isinstance(observation.get('console_errors'), list)):
                outcome = {'category': 'browser_error', 'reason': 'missing target observation'}
    receipt = {'image': image, 'app_sha256': app_hash, 'returncode': returncode, **outcome}
    (output / 'executor.json').write_text(json.dumps(receipt, indent=2))
    return receipt
