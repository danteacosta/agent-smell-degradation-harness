"""Trusted browser report adapter for the StrictDoc statistics-screen contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import uuid
import unicodedata

from eval.focus_chain_executor import container_command

ASSERTION_IDS = ('project_identity', 'totals', 'status_breakdown',
                 'tbd_tbc_total', 'generation_date_visible')
CONTRACT = json.loads((Path(__file__).parent / 'fixtures/strictdoc-stats/contract.json').read_text())


def _normalize(text: str) -> str:
    text = re.sub(r'(\d)t(?=\d)', r'\1 ', text, flags=re.I)
    text = re.sub(r'(\d+)(st|nd|rd|th)\b', r'\1', text, flags=re.I)
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if not '\u0300' <= c <= '\u036f')
    return ' '.join(''.join(c if c.isalnum() else ' ' for c in text.lower()).split())


def _observations_agree(value: dict, indexed: dict) -> bool:
    observations = value.get('observations')
    if not isinstance(observations, list) or len(observations) != 2:
        return False
    for clock, item in zip(('clock-one', 'clock-two'), observations):
        if not isinstance(item, dict) or item.get('clock_id') != clock:
            return False
        observed = item.get('observed')
        text = item.get('visible_text')
        errors = item.get('console_errors')
        scrolls = item.get('scroll_positions')
        if (not isinstance(observed, dict) or set(observed) != set(CONTRACT['expected'])
                or any(not isinstance(v, str) for v in observed.values())
                or type(item.get('date_visible')) is not bool
                or not isinstance(text, str) or len(text) > 20000
                or item.get('visible_text_sha256') != hashlib.sha256(text.encode()).hexdigest()
                or not isinstance(errors, list) or len(errors) > 20
                or any(not isinstance(error, str) or len(error) > 500 for error in errors)
                or not isinstance(scrolls, list) or not 1 <= len(scrolls) <= 15
                or any(type(y) is not int or not 0 <= y <= 8000 for y in scrolls)
                or scrolls != sorted(set(scrolls)) or scrolls[0] != 0
                or item.get('screenshot') != clock + '.png'):
            return False
        matched = item.get('matched_date')
        if item['date_visible']:
            if (not isinstance(matched, str) or matched not in CONTRACT['accepted_dates'][clock]
                    or ' ' + matched + ' ' not in ' ' + _normalize(text) + ' '):
                return False
        elif matched is not None:
            return False
        if not item['date_visible'] and any(' ' + date + ' ' in ' ' + _normalize(text) + ' '
                                           for date in CONTRACT['accepted_dates'][clock]):
            return False
    for group, keys in CONTRACT['groups'].items():
        passed = all(all(item['observed'][key] == CONTRACT['expected'][key] for key in keys)
                     for item in observations)
        if indexed[group]['status'] != ('passed' if passed else 'failed'):
            return False
    passed = all(item['date_visible'] for item in observations)
    return indexed['generation_date_visible']['status'] == ('passed' if passed else 'failed')


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
    if not isinstance(value, dict) or value.get('schema_version') != 'strictdoc-stats-browser/v1':
        return invalid
    if not isinstance(value.get('app_sha256'), str) or not re.fullmatch(r'[0-9a-f]{64}', value['app_sha256']):
        return invalid
    if value.get('status') in ('interface_error', 'browser_error'):
        return {'category': value['status'], 'reason': str(value.get('error', ''))[:1500]} if returncode == 2 else invalid
    cases = value.get('cases')
    if (value.get('status') != 'complete' or not isinstance(cases, list)
            or len(cases) != len(ASSERTION_IDS) or any(not isinstance(c, dict) for c in cases)
            or any(not isinstance(c.get('id'), str) for c in cases)):
        return invalid
    indexed = {c['id']: c for c in cases}
    if len(indexed) != len(ASSERTION_IDS) or set(indexed) != set(ASSERTION_IDS):
        return invalid
    if any(c.get('status') not in ('passed', 'failed') or 'reason' in c for c in cases):
        return invalid
    if not _observations_agree(value, indexed):
        return invalid
    failed = [key for key in ASSERTION_IDS if indexed[key]['status'] == 'failed']
    if returncode != (1 if failed else 0):
        return invalid
    target_failed = 'generation_date_visible' in failed
    non_target = [key for key in failed if key != 'generation_date_visible']
    category = ('mixed_failure' if target_failed and non_target else
                'target_only_failure' if target_failed else
                'non_target_only_failure' if non_target else 'pass')
    return {'category': category, 'target_failed': target_failed,
            'non_target_failed': non_target}


def execute(image: str, inputs: Path, output: Path, timeout: int = 90) -> dict:
    """Execute one standalone HTML artifact in the bounded offline browser."""
    output.mkdir(parents=True, exist_ok=False)
    name = 'strictdoc-stats-' + uuid.uuid4().hex
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
                               'mixed_failure'}:
        screenshots = [output / 'clock-one.png', output / 'clock-two.png']
        if any(path.is_symlink() or not path.is_file() or path.stat().st_size > 4000000
               or not path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n') for path in screenshots):
            outcome = {'category': 'browser_error', 'reason': 'missing bounded screenshot'}
        else:
            observations = json.loads(raw).get('observations')
            if (not isinstance(observations, list) or len(observations) != 2
                    or any(not isinstance(item, dict) for item in observations)):
                outcome = {'category': 'browser_error', 'reason': 'missing clock observations'}
    receipt = {'image': image, 'app_sha256': app_hash, 'returncode': returncode, **outcome}
    (output / 'executor.json').write_text(json.dumps(receipt, indent=2))
    return receipt
