"""Trusted TodoMVC Mark all browser report adapter.

Generated HTML is never imported or executed by this Python process. The browser
controller runs it as an offline page only after generation collection ends.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import uuid

from eval.focus_chain_executor import container_command

ASSERTION_IDS = ('master_sets_items', 'master_tracks_individuals',
                 'clear_completed_removes_items', 'clear_master_after_clear_completed')


def _unique_fields(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('duplicate JSON field')
        value[key] = item
    return value


def classify_report(raw: bytes | None, returncode: int) -> dict:
    invalid = {'category': 'browser_error', 'reason': 'incomplete or inconsistent trusted report'}
    try:
        value = json.loads(raw, object_pairs_hook=_unique_fields) if raw and len(raw) <= 100000 else None
    except (ValueError, TypeError):
        return invalid
    if not isinstance(value, dict) or value.get('schema_version') != 'mark-all-browser/v1':
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
    indexed = {c['id']: c.get('status') for c in cases}
    if len(indexed) != len(ASSERTION_IDS) or set(indexed) != set(ASSERTION_IDS):
        return invalid
    target = indexed['clear_master_after_clear_completed']
    if target not in ('passed', 'failed', 'not_evaluable'):
        return invalid
    if any(indexed[name] not in ('passed', 'failed') for name in ASSERTION_IDS[:2]):
        return invalid
    clear_case = next(c for c in cases if c['id'] == 'clear_completed_removes_items')
    clear_status = indexed['clear_completed_removes_items']
    if clear_status == 'not_evaluable':
        if clear_case.get('reason') != 'bulk_selection_failed' or target != 'not_evaluable':
            return invalid
    elif clear_status not in ('passed', 'failed') or 'reason' in clear_case:
        return invalid
    target_case = next(c for c in cases if c['id'] == 'clear_master_after_clear_completed')
    if target == 'not_evaluable':
        if target_case.get('reason') not in {'bulk_selection_failed', 'clear_unavailable',
                                             'clear_failed', 'master_identity_ambiguous'}:
            return invalid
    elif 'reason' in target_case:
        return invalid
    failed = [name for name in ASSERTION_IDS[:-1] if indexed[name] == 'failed']
    if target == 'failed':
        failed.append('clear_master_after_clear_completed')
    if returncode != (1 if failed or target == 'not_evaluable'
                      or clear_status == 'not_evaluable' else 0):
        return invalid
    non_target = [name for name in failed if name != 'clear_master_after_clear_completed']
    if target == 'not_evaluable':
        return {'category': 'target_not_evaluable', 'target_failed': None,
                'non_target_failed': non_target}
    target_failed = target == 'failed'
    category = ('mixed_failure' if target_failed and non_target else
                'target_only_failure' if target_failed else
                'non_target_only_failure' if non_target else 'pass')
    return {'category': category, 'target_failed': target_failed,
            'non_target_failed': non_target}


def execute(image: str, inputs: Path, output: Path, timeout: int = 90) -> dict:
    """Execute one HTML artifact using the bounded offline container contract."""
    output.mkdir(parents=True, exist_ok=False)
    name = 'mark-all-' + uuid.uuid4().hex
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
        screenshots = [output / name for name in
                       ('after-clear.png', 'before-target.png', 'after-target.png')]
        if any(image.is_symlink() or not image.is_file() or image.stat().st_size > 4000000
               or not image.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
               for image in screenshots):
            outcome = {'category': 'browser_error', 'reason': 'missing bounded screenshot'}
        else:
            observation = json.loads(raw).get('target_observation')
            if (not isinstance(observation, dict)
                    or not all(isinstance(observation.get(key), dict) for key in ('before', 'after'))
                    or not isinstance(observation.get('console_errors'), list)):
                outcome = {'category': 'browser_error', 'reason': 'missing target observation'}
    receipt = {'image': image, 'app_sha256': app_hash, 'returncode': returncode, **outcome}
    (output / 'executor.json').write_text(json.dumps(receipt, indent=2))
    return receipt
