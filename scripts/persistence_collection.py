"""Single-attempt collection for the admitted PR72 persistence UI endpoint."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from agents.codex_cli import CodexCLIProvider
from agents.providers import ProviderRequest
from eval.collect_todomvc_pilot import write_private, _fsync_directory as sync_directory
from eval.persistence_executor import execute
from scripts.behavioral_expansion import summarize

PARENT_RECEIPT = '98018df19b329ea2f10e3aa66f4443048a14eb8974cdcbc8f7bd05ca1e3110ce'
ENDPOINT_FILES = ('eval/persistence_executor.py', 'eval/focus_chain_executor.py',
                  'scripts/behavioral_expansion.py',
                  'eval/fixtures/persistence/runner.cjs', 'eval/fixtures/persistence/Dockerfile',
                  'eval/fixtures/persistence/package.json', 'eval/fixtures/persistence/package-lock.json',
                  'eval/fixtures/persistence/control.html', 'eval/fixtures/persistence/qualify.py')
FLAGS = {'confirmatory_eligible': False, 'human_approvals': 0,
         'label_source': 'independent_behavioral_oracle'}


def now():
    return datetime.now(timezone.utc).isoformat()


def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def private_mkdir(directory):
    missing = []
    cursor = directory
    while not cursor.exists():
        if cursor.is_symlink():
            raise ValueError('symlink directory forbidden')
        missing.append(cursor)
        cursor = cursor.parent
    if cursor.is_symlink() or not cursor.is_dir():
        raise ValueError('real parent directory required')
    for path in reversed(missing):
        path.mkdir(mode=0o700)
        sync_directory(path.parent)
        sync_directory(path)


def put(path, value):
    private_mkdir(path.parent)
    data = value if isinstance(value, bytes) else (json.dumps(value, indent=2)+'\n').encode()
    write_private(path, data)


def hash_inventory(directory):
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError('real packet directory required')
    result = {}
    for path in sorted(directory.rglob('*')):
        mode = path.lstat().st_mode
        if stat.S_ISREG(mode):
            result[str(path.relative_to(directory))] = hash_file(path)
        elif not stat.S_ISDIR(mode):
            raise ValueError('only regular evidence files and directories allowed')
    return result


def verify_inventory(directory, expected=None):
    actual = hash_inventory(directory)
    receipt_hash = actual.pop('receipt.json', None)
    if expected is not None and receipt_hash != expected:
        raise ValueError('source receipt drift')
    if actual != json.loads((directory/'receipt.json').read_text())['files']:
        raise ValueError('receipt inventory drift')


def runtime_hashes():
    # Python package initializers import additional runtime modules. Bind their
    # bytes too, rather than claiming only the directly named adapter can vary.
    paths = set(ROOT/name for name in ENDPOINT_FILES)
    for folder in ('agents', 'protocol', 'eval', 'scripts'):
        paths.update((ROOT/folder).rglob('*.py'))
    return {str(p.relative_to(ROOT)): hash_file(p) for p in sorted(paths)}


def html_bytes(raw):
    if not isinstance(raw, str):
        raise ValueError('HTML text required')
    data = raw.encode('utf-8')
    if (len(data) > 200000 or not re.match(r'(?is)^\s*(?:<!doctype\s+html\b[^>]*>\s*)?<html\b', raw)
            or not re.search(r'(?is)</html>\s*$', raw)):
        raise ValueError('bounded standalone raw HTML required; no output repair')
    return data


def validate_preflight(preflight):
    required = ('ordinary_usage_allowed', 'chatgpt_auth', 'required_cli_flags',
                'image_verified', 'isolation_verified')
    if any(preflight.get(key) is not True for key in required):
        raise ValueError('preflight incomplete')
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(preflight['checked_at_utc'])).total_seconds()
    if not 0 <= age <= 3600:
        raise ValueError('preflight stale; refresh capacity and runtime checks')


def prepare(parent, destination, executable, preflight):
    validate_preflight(preflight)
    verify_inventory(parent, PARENT_RECEIPT)
    for name in ENDPOINT_FILES:
        if hash_file(ROOT/name) != hash_file(parent/'frozen/runtime'/name):
            raise ValueError('admitted endpoint runtime drift: '+name)
    source = json.loads((parent/'frozen/manifest.json').read_text())
    slots = json.loads((parent/'frozen/schedule.json').read_text())
    if len(slots) != 18:
        raise ValueError('exact 18-slot design required')
    summarize(slots, [])  # Validate balanced design and unique identities.
    for slot in slots:
        if not re.fullmatch(r'behavior-[0-9a-f]{20}', slot['slot_id']):
            raise ValueError('invalid slot identifier')
    if not destination.is_absolute() or destination.parent.is_symlink():
        raise ValueError('absolute private destination required')
    if destination.resolve().is_relative_to(ROOT):
        raise ValueError('private destination must be outside the repository')
    executable = executable.resolve(strict=True)
    version = subprocess.run([str(executable), '--version'], capture_output=True,
                             text=True, check=True, timeout=15).stdout.strip()
    destination.mkdir(mode=0o700, exist_ok=False)
    sync_directory(destination.parent)
    sync_directory(destination)
    frozen = destination/'frozen'
    put(frozen/'parent-receipt.json', (parent/'receipt.json').read_bytes())
    put(frozen/'schedule.json', slots)
    for slot in slots:
        relative = Path('requests')/(slot['slot_id']+'.json')
        request = json.loads((parent/'frozen'/relative).read_text())
        if set(request) != {'prompt'} or not isinstance(request['prompt'], str):
            raise ValueError('prompt-only request required')
        put(frozen/relative, (parent/'frozen'/relative).read_bytes())
    hashes = runtime_hashes()
    for name in hashes:
        put(frozen/'runtime'/name, (ROOT/name).read_bytes())
    manifest = {**FLAGS, 'schema_version': 'persistence-collection/v1',
        'frozen_at_utc': now(), 'parent': str(parent.resolve()), 'parent_receipt_sha256': PARENT_RECEIPT,
        'executable': str(executable), 'executable_sha256': hash_file(executable),
        'cli_version': version, 'runtime_hashes': hashes, 'preflight': preflight,
        'image_id': source['image_id'], 'scope': source['scope'], 'max_calls': 18,
        'concurrency': 1, 'reasoning_effort': 'low', 'timeout_seconds': 180,
        'retry_policy': 'no_retry_no_resume_no_repair', 'billing_mode': 'chatgpt_subscription',
        'internal_transport_retries': 'not_observable', 'model_snapshot_status': 'not_exposed_by_cli',
        'capture_limit_bytes_per_stream': 2000000, 'artifact_limit_bytes': 200000,
        'output_admission': 'raw HTML document; no fence removal or JSON extraction',
        'output_token_cap': None, 'api_key_fallback': False}
    put(frozen/'manifest.json', manifest)
    put(frozen/'receipt.json', {'files': hash_inventory(frozen)})
    return manifest


def verify_execution(packet):
    if packet.is_symlink() or packet.stat().st_mode & 0o077:
        raise ValueError('private real packet required')
    frozen = packet/'frozen'
    verify_inventory(frozen)
    manifest = json.loads((frozen/'manifest.json').read_text())
    validate_preflight(manifest['preflight'])
    if hash_file(Path(manifest['executable'])) != manifest['executable_sha256']:
        raise ValueError('executable drift')
    if runtime_hashes() != manifest['runtime_hashes']:
        raise ValueError('runtime drift')
    verify_inventory(Path(manifest['parent']), manifest['parent_receipt_sha256'])
    slots = json.loads((frozen/'schedule.json').read_text())
    if len(slots) != 18 or manifest['max_calls'] != 18:
        raise ValueError('schedule drift')
    summarize(slots, [])
    return manifest, slots


def run(packet, provider_factory=CodexCLIProvider, executor=execute):
    manifest, slots = verify_execution(packet)
    put(packet/'run-started.json', {'started_at_utc': now(), 'policy': 'no_resume', **FLAGS})
    rows = [{**s, 'category': 'not_attempted', 'target_failed': None} for s in slots]
    put(packet/'initial-observations.json', rows)
    state = {**FLAGS, 'calls_attempted': 0, 'stop_reason': None, 'rows': rows}
    for row in rows:
        if state['stop_reason']:
            break
        slot_id = row['slot_id']
        call = packet/'calls'/slot_id
        request = json.loads((packet/'frozen/requests'/(slot_id+'.json')).read_text())
        put(call/'attempt.json', {'slot_id': slot_id, 'started_at_utc': now(),
                                 'model': row['model'], 'request_sha256': hash_file(packet/'frozen/requests'/(slot_id+'.json'))})
        state['calls_attempted'] += 1
        try:
            provider = provider_factory(executable=manifest['executable'], model=row['model'],
                timeout_seconds=manifest['timeout_seconds'], evidence_directory=call/'capture')
            raw = provider.complete(ProviderRequest(request['prompt'], {}, 'opaque', 'code'))
        except Exception as error:
            row.update(category='provider_error', error_type=type(error).__name__)
            state['stop_reason'] = 'provider_infrastructure_error'
        else:
            put(call/'response.txt', raw.encode('utf-8', errors='backslashreplace'))
            put(call/'provider-metadata.json', provider.last_call_metadata)
            try:
                html = html_bytes(raw)
            except (ValueError, UnicodeError):
                row['category'] = 'invalid_output'
            else:
                put(packet/'artifacts'/slot_id/'app.html', html)
                row['generation_valid'] = True
        put(call/'generation-result.json', row)
        print(json.dumps({'completed_calls': state['calls_attempted'], 'phase': 'generation'}), flush=True)
    # No generated behavior or target result is observed while generation remains.
    put(packet/'collection.json', state)
    for row in rows:
        if not row.get('generation_valid'):
            continue
        try:
            outcome = executor(image=manifest['image_id'], inputs=packet/'artifacts'/row['slot_id'],
                               output=packet/'execution'/row['slot_id'])
            observation = {'slot_id': row['slot_id'], 'category': outcome['category'],
                           'target_failed': outcome.get('target_failed')}
            summarize(slots, [observation])
        except Exception as error:
            outcome = {'category': 'browser_error', 'target_failed': None, 'error_type': type(error).__name__}
        row.update(category=outcome['category'], target_failed=outcome.get('target_failed'), execution=outcome)
    put(packet/'results.json', state)
    analysis = summarize(slots, rows)
    analysis.update(**FLAGS, calls_attempted=state['calls_attempted'], stop_reason=state['stop_reason'], scope=manifest['scope'])
    put(packet/'analysis.json', analysis)
    put(packet/'receipt.json', {'files': hash_inventory(packet)})
    return analysis


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    for name in ('parent', 'destination', 'executable', 'preflight'):
        prep.add_argument('--'+name, type=Path, required=True)
    sub.add_parser('run').add_argument('--packet', type=Path, required=True)
    args = parser.parse_args()
    result = (prepare(args.parent, args.destination, args.executable, json.loads(args.preflight.read_text()))
              if args.command == 'prepare' else run(args.packet))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
