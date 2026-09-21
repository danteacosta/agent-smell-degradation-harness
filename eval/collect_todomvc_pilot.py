"""Collect one immutable, nine-call exploratory run; never resumes or retries."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import stat
import subprocess

from agents.codex_cli import CodexCLIProvider
from agents.providers import ProviderRequest
from eval.todomvc_pilot import assemble_response, classify_junit, freeze_manifest, make_scaffold, sha256
from eval.todomvc_pilot_executor import collector_identity, execute


def inventory(directory: Path) -> dict:
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError('evidence directory must be a real directory')
    files = {}
    for path in sorted(directory.rglob('*')):
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise ValueError('evidence must contain only regular files and directories')
        if stat.S_ISREG(mode):
            data = path.read_bytes()
            files[path.relative_to(directory).as_posix()] = {
                'sha256': sha256(data), 'bytes': len(data)}
    return files


def _fsync_directory(directory: Path) -> None:
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_json(path: Path, value: object) -> None:
    """Atomically replace a private JSON record and durably publish its name."""
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError('JSON evidence path must be a regular file')
    data = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode('utf-8')
    temporary = path.parent / f'.{path.name}.{os.getpid()}.{secrets.token_hex(8)}.tmp'
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, 'wb', closefd=False) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(fd)
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        os.close(fd)
        temporary.unlink(missing_ok=True)


def write_private(path: Path, data: bytes) -> None:
    """Create immutable private evidence without following an existing link."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, 'wb', closefd=False) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_directory(path.parent)


def _validate_private_destination(destination: Path, repository_root: Path) -> Path:
    if not destination.is_absolute():
        raise ValueError('destination must be an absolute private path')
    resolved = destination.resolve()
    try:
        resolved.relative_to(repository_root.resolve())
    except ValueError:
        pass
    else:
        raise ValueError('destination must be outside the repository')
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    if not destination.parent.is_dir() or destination.parent.is_symlink():
        raise ValueError('destination parent must be an existing real directory')
    return destination


def has_native_media(output: Path) -> bool:
    screenshots = list(output.glob('screenshots/**/escape-after-interaction.png'))
    videos = list(output.glob('videos/**/*.mp4'))
    return bool(screenshots and videos
                and all(p.read_bytes().startswith(b'\x89PNG\r\n\x1a\n') for p in screenshots)
                and all(p.read_bytes()[4:8] == b'ftyp' for p in videos))


def collect(destination: Path, original: Path, qualification: Path, image: str,
            executable: Path, model: str) -> dict:
    collector_identity()
    root = Path(__file__).resolve().parents[1]
    destination = _validate_private_destination(destination, root)
    # Validate qualification in the exact image before any provider dispatch.
    qualified = {}
    for arm, expected in [('gold', 'pass'), ('mutant', 'targeted_escape_defect')]:
        output = qualification / arm / 'output'
        receipt = json.loads((output / 'executor.json').read_text())
        result = classify_junit((output / 'todomvc-qualification-junit.xml').read_bytes(), receipt['returncode'])
        if receipt['image'] != image or receipt['timed_out'] or result['category'] != expected:
            raise ValueError('reference/mutant executor not qualified')
        if not (output / 'body-validation.log').is_file():
            raise ValueError('qualification must exercise response body validation')
        if not has_native_media(output):
            raise ValueError('qualification lacks native media')
        qualified[arm] = {'result': result, 'files': inventory(output)}
    os.mkdir(destination, 0o700)
    _fsync_directory(destination.parent)
    code = ['agents/codex_cli.py', 'eval/todomvc_pilot.py', 'eval/todomvc_pilot_executor.py',
            'eval/collect_todomvc_pilot.py', 'eval/fixtures/todomvc-pilot-run.sh',
            'eval/fixtures/todomvc-pilot.Dockerfile', 'eval/fixtures/todomvc-escape-oracle.patch',
            'eval/fixtures/todomvc-visual-support.js']
    bindings = {'frozen_at_utc': datetime.now(timezone.utc).isoformat(), 'model': model,
                'reasoning_effort': 'low', 'image': image, 'qualification': qualified,
                'codex_binary_sha256': sha256(executable.read_bytes()),
                'codex_version': subprocess.run([str(executable), '--version'], capture_output=True,
                                                text=True, check=True, timeout=15).stdout.strip(),
                'source_sha256': sha256(original.read_bytes()),
                'code_sha256': {p: sha256((root / p).read_bytes()) for p in code},
                'no_retries': True, 'api_key_fallback': False}
    scaffold = make_scaffold(original.read_bytes())
    manifest = freeze_manifest(destination / 'frozen', scaffold, bindings)
    outcomes = [{**slot, 'category': 'not_attempted'} for slot in manifest['slots']]
    results_path = destination / 'outcomes.json'
    write_json(results_path, outcomes)
    for slot in outcomes:
        run = destination / 'runs' / slot['slot_id']
        run.mkdir(parents=True, mode=0o700)
        provider = CodexCLIProvider(executable=str(executable), model=model, timeout_seconds=120,
                                    evidence_directory=run / 'cli-capture')
        prompt_entry = manifest['prompts'][slot['arm']]
        prompt = (destination / 'frozen' / prompt_entry['path']).read_bytes()
        if sha256(prompt) != prompt_entry['sha256']:
            raise ValueError('frozen prompt changed')
        slot['started_at_utc'] = datetime.now(timezone.utc).isoformat()
        slot['category'] = 'generation_in_progress'
        write_json(results_path, outcomes)
        try:
            raw = provider.complete(ProviderRequest(prompt.decode(), {}, slot['arm'], 'todomvc_escape'))
        except Exception as exc:
            write_json(run / 'provider-metadata.json', provider.last_call_metadata)
            slot.update(category='generation_error', error=f'{type(exc).__name__}: {exc}',
                        remaining_dispatch_stopped=True)
            write_json(results_path, outcomes)
            break
        write_private(run / 'response.json', raw.encode('utf-8'))
        write_json(run / 'provider-metadata.json', provider.last_call_metadata)
        try:
            component = assemble_response(scaffold, raw)
        except ValueError as exc:
            slot.update(category='generation_error', error=str(exc))
            write_json(results_path, outcomes)
            continue
        inputs = run / 'input'
        inputs.mkdir(mode=0o700)
        write_private(inputs / 'TodoItem.vue', component)
        write_private(inputs / 'response.json', raw.encode('utf-8'))
        slot['category'] = 'execution_in_progress'
        write_json(results_path, outcomes)
        try:
            execution = execute(image, inputs, run / 'output')
            report = run / 'output' / 'todomvc-qualification-junit.xml'
            result = classify_junit(report.read_bytes() if report.exists() else None,
                                    execution['returncode'])
            slot.update(result)
            slot['native_media_present'] = has_native_media(run / 'output')
            if result['category'] in {'pass', 'targeted_escape_defect', 'other_test_failure'} and not slot['native_media_present']:
                slot.update(category='build_or_executor_error', e2e_result=result,
                            error='native screenshot/video evidence missing or invalid')
        except Exception as exc:
            slot.update(category='build_or_executor_error', error=f'{type(exc).__name__}: {exc}')
        slot['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
        write_json(results_path, outcomes)
        print(slot['slot_id'], slot['category'], flush=True)
    receipt = {'confirmatory': False, 'outcomes': outcomes, 'files': inventory(destination)}
    write_json(destination / 'receipt.json', receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ('destination', 'original', 'qualification', 'executable'):
        parser.add_argument('--' + option, type=Path, required=True)
    parser.add_argument('--image', required=True)
    parser.add_argument('--model', required=True)
    collect(**vars(parser.parse_args()))
