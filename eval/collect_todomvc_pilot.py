"""Collect one immutable, nine-call exploratory run; never resumes or retries."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from agents.codex_cli import CodexCLIProvider
from agents.providers import ProviderRequest
from eval.todomvc_pilot import assemble_response, classify_junit, freeze_manifest, make_scaffold, sha256
from eval.todomvc_pilot_executor import execute


def inventory(directory: Path) -> dict:
    return {str(p.relative_to(directory)): {'sha256': sha256(p.read_bytes()), 'bytes': p.stat().st_size}
            for p in sorted(directory.rglob('*')) if p.is_file() and not p.is_symlink()}


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def has_native_media(output: Path) -> bool:
    screenshots = list(output.glob('screenshots/**/escape-after-interaction.png'))
    videos = list(output.glob('videos/**/*.mp4'))
    return bool(screenshots and videos
                and all(p.read_bytes().startswith(b'\x89PNG\r\n\x1a\n') for p in screenshots)
                and all(p.read_bytes()[4:8] == b'ftyp' for p in videos))


def collect(destination: Path, original: Path, qualification: Path, image: str,
            executable: Path, model: str) -> dict:
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
    destination.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
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
        run.mkdir(parents=True)
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
        (run / 'response.json').write_text(raw)
        write_json(run / 'provider-metadata.json', provider.last_call_metadata)
        try:
            component = assemble_response(scaffold, raw)
        except ValueError as exc:
            slot.update(category='generation_error', error=str(exc))
            write_json(results_path, outcomes)
            continue
        inputs = run / 'input'
        inputs.mkdir()
        (inputs / 'TodoItem.vue').write_bytes(component)
        (inputs / 'response.json').write_text(raw)
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
