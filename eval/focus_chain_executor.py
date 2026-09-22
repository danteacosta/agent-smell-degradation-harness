"""Offline browser adapter; incomplete execution is never a requirement defect."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import uuid

ASSERTION_IDS = ('initial_focus', 'input_above_list', 'enter_append', 'input_cleared',
                 'trimmed_title', 'empty_rejected', 'whitespace_rejected')


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
        report = json.loads(raw, object_pairs_hook=_unique_fields) if raw and len(raw) <= 100000 else None
    except (ValueError, TypeError):
        return invalid
    if not isinstance(report, dict) or report.get('schema_version') != 'focus-chain-browser/v1':
        return invalid
    if not isinstance(report.get('app_sha256'), str) or not re.fullmatch(r'[0-9a-f]{64}', report['app_sha256']):
        return invalid
    if report.get('status') in {'interface_error', 'browser_error'}:
        return {'category': report['status'], 'reason': report.get('error', '')} if returncode == 2 else invalid
    cases = report.get('cases', [])
    if (report.get('status') != 'complete' or not isinstance(cases, list)
            or len(cases) != len(ASSERTION_IDS) or any(not isinstance(case, dict) for case in cases)):
        return invalid
    if sorted(case.get('id', '') for case in cases) != sorted(ASSERTION_IDS):
        return invalid
    if any(case.get('status') not in {'passed', 'failed'} for case in cases):
        return invalid
    failed = [case['id'] for case in cases if case['status'] == 'failed']
    if returncode != (1 if failed else 0):
        return invalid
    target = 'initial_focus' in failed
    unrelated = [name for name in failed if name != 'initial_focus']
    category = ('mixed_failure' if target and unrelated else 'target_only_failure' if target
                else 'non_target_only_failure' if unrelated else 'pass')
    return {'category': category, 'target_failed': target, 'non_target_failed': unrelated}


def container_command(image: str, inputs: Path, output: Path, name: str) -> list[str]:
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', image):
        raise ValueError('immutable Docker image ID required')
    if os.getuid() == 0 or os.getgid() == 0:
        raise ValueError('non-root collector required')
    for directory in (inputs, output):
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError('real input/output directories required')
    if set(path.name for path in inputs.iterdir()) != {'app.html'}:
        raise ValueError('only app.html may be exposed to the container')
    app = inputs/'app.html'
    if app.is_symlink() or not app.is_file() or app.stat().st_size > 200000:
        raise ValueError('bounded regular app.html required')
    return ['docker', 'run', '--rm', '--init', '--name', name, '--network', 'none',
            '--user', f'{os.getuid()}:{os.getgid()}', '--read-only', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--pids-limit', '256', '--memory', '1g',
            '--cpus', '2', '--shm-size', '256m', '--tmpfs', '/tmp:rw,nosuid,size=256m',
            '--env', 'HOME=/tmp', '--mount', f'type=bind,src={inputs.resolve()},dst=/input,readonly',
            '--mount', f'type=bind,src={output.resolve()},dst=/output', image]


def execute(image: str, inputs: Path, output: Path, timeout: int = 90) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    name = 'focus-chain-' + uuid.uuid4().hex
    command = container_command(image, inputs, output, name)
    app_hash = hashlib.sha256((inputs/'app.html').read_bytes()).hexdigest()
    (output/'container-command.json').write_text(json.dumps(command, indent=2))
    timed_out = False
    try:
        with (output/'container.log').open('wb') as log:
            try:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                        timeout=timeout, check=False)
                returncode = result.returncode
            except subprocess.TimeoutExpired:
                returncode = 124
                timed_out = True
    finally:
        subprocess.run(['docker','rm','--force',name], capture_output=True, timeout=30, check=False)
    report_file = output/'report.json'
    raw = report_file.read_bytes() if report_file.is_file() and not report_file.is_symlink() else None
    outcome = {'category': 'timeout'} if timed_out else classify_report(raw, returncode)
    if raw and not timed_out:
        try:
            if json.loads(raw).get('app_sha256') != app_hash:
                outcome = {'category': 'browser_error', 'reason': 'executed app hash mismatch'}
        except (ValueError, AttributeError):
            outcome = {'category': 'browser_error', 'reason': 'invalid trusted report'}
    if outcome['category'] in {'pass', 'target_only_failure', 'non_target_only_failure', 'mixed_failure'}:
        screenshot = output/'initial-focus.png'
        if (screenshot.is_symlink() or not screenshot.is_file() or screenshot.stat().st_size > 4000000
                or not screenshot.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')):
            outcome = {'category': 'browser_error', 'reason': 'missing or invalid bounded screenshot'}
    receipt = {'image':image, 'app_sha256':app_hash, 'returncode':returncode,
               'timed_out':timed_out, **outcome}
    (output/'executor.json').write_text(json.dumps(receipt, indent=2))
    return receipt
