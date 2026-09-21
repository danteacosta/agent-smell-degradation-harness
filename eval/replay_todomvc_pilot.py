"""Supplementary offline replay after the pilot's Acorn infrastructure failure.

No generation occurs here. The original nine failed executions remain unchanged;
this explicitly non-preregistered amendment executes all existing inputs once.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import stat

from eval.todomvc_pilot import assemble_response, classify_junit, planned_slots, sha256
from eval.todomvc_pilot_executor import execute


# Keep these small evidence operations local: importing the collection command
# would import a provider into an intentionally provider-free replay command.
def inventory(directory: Path) -> dict:
    files = {}
    if directory.is_symlink():
        raise ValueError('evidence directory cannot be a symlink')
    for path in sorted(directory.rglob('*')):
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise ValueError('evidence must contain only regular files and directories')
        if path.is_file():
            data = path.read_bytes()
            files[path.relative_to(directory).as_posix()] = {'sha256': sha256(data), 'bytes': len(data)}
    return files


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def has_native_media(output: Path) -> bool:
    screenshots = list(output.glob('screenshots/**/escape-after-interaction.png'))
    videos = list(output.glob('videos/**/*.mp4'))
    return bool(screenshots and videos
                and all(p.read_bytes().startswith(b'\x89PNG\r\n\x1a\n') for p in screenshots)
                and all(p.read_bytes()[4:8] == b'ftyp' for p in videos))


def _validate_original(source: Path) -> tuple[dict, dict]:
    actual = inventory(source)
    receipt = json.loads((source / 'receipt.json').read_text())
    actual.pop('receipt.json', None)
    if actual != receipt.get('files'):
        raise ValueError('original collection inventory changed')
    manifest = json.loads((source / 'frozen/manifest.json').read_text())
    outcomes = json.loads((source / 'outcomes.json').read_text())
    slots = planned_slots()
    if (manifest.get('slots') != slots or outcomes != receipt.get('outcomes')
            or len(outcomes) != 9 or receipt.get('confirmatory') is not False):
        raise ValueError('original collection must contain the complete nine-slot protocol')
    scaffold = (source / 'frozen/scaffold.vue').read_text()
    for slot, outcome in zip(slots, outcomes):
        if (any(outcome.get(key) != value for key, value in slot.items())
                or outcome.get('category') != 'build_or_executor_error'):
            raise ValueError('every original outcome must be its planned infrastructure error')
        run = source / 'runs' / slot['slot_id']
        output = run / 'output'
        log = output / 'body-validation.log'
        if not log.is_file() or "Cannot find module 'acorn'" not in log.read_text():
            raise ValueError('original failure is not the Acorn infrastructure failure')
        if any(p.name == 'build.log' or 'junit' in p.name.lower() for p in output.rglob('*')):
            raise ValueError('original execution already reached build or E2E')
        response = (run / 'response.json').read_bytes()
        if (response != (run / 'input/response.json').read_bytes()
                or assemble_response(scaffold, response.decode()) != (run / 'input/TodoItem.vue').read_bytes()):
            raise ValueError('original generated response and component are not bound')
        if set(inventory(run / 'input')) != {'TodoItem.vue', 'response.json'}:
            raise ValueError('unexpected original execution input')
    return receipt, manifest


def _validate_qualification(qualification: Path, image: str) -> dict:
    qualified = {}
    inventory(qualification)
    for arm, expected in [('gold', 'pass'), ('mutant', 'targeted_escape_defect')]:
        run = qualification / arm
        output = run / 'output'
        required = [run / 'input/response.json', run / 'input/TodoItem.vue',
                    output / 'body-validation.log', output / 'executed-TodoItem.vue',
                    output / 'todomvc-qualification-junit.xml', output / 'executor.json']
        if not all(path.is_file() for path in required):
            raise ValueError('qualification must exercise the generated-response validation path')
        if (run / 'input/TodoItem.vue').read_bytes() != (output / 'executed-TodoItem.vue').read_bytes():
            raise ValueError('qualification executed a different component')
        execution = json.loads((output / 'executor.json').read_text())
        result = classify_junit((output / 'todomvc-qualification-junit.xml').read_bytes(), execution['returncode'])
        if (execution['image'] != image or execution['timed_out']
                or result['category'] != expected or not has_native_media(output)):
            raise ValueError('corrected image lacks qualified reference/mutant evidence and media')
        qualified[arm] = {'result': result, 'files': inventory(run)}
    return qualified


def replay(source: Path, destination: Path, qualification: Path, image: str) -> dict:
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', image):
        raise ValueError('immutable Docker image ID required')
    if destination.exists():
        raise FileExistsError(destination)
    if destination.resolve().is_relative_to(source.resolve()):
        raise ValueError('supplementary replay must be outside the original collection')
    original_receipt, manifest = _validate_original(source)
    if image == manifest.get('bindings', {}).get('image'):
        raise ValueError('replay requires the corrected image, not the failed original image')
    qualified = _validate_qualification(qualification, image)
    original_inventory = inventory(source)
    root = Path(__file__).resolve().parents[1]
    code = ['eval/replay_todomvc_pilot.py', 'eval/todomvc_pilot.py',
            'eval/todomvc_pilot_executor.py', 'eval/fixtures/todomvc-pilot-run.sh',
            'eval/fixtures/todomvc-pilot.Dockerfile']
    inputs = {}
    for slot in manifest['slots']:
        inputs[slot['slot_id']] = inventory(source / 'runs' / slot['slot_id'] / 'input')
    amendment = {
        'schema_version': 'todomvc-supplementary-replay-v1', 'confirmatory': False,
        'preregistered': False, 'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
        'reason': 'All nine original executions failed resolving Acorn before build/E2E. Replay existing outputs once under a corrected, requalified executor; preserve the original run.',
        'original_receipt_sha256': sha256((source / 'receipt.json').read_bytes()),
        'original_outcomes': original_receipt['outcomes'],
        'original_image': manifest['bindings']['image'], 'corrected_image': image,
        'slots': manifest['slots'], 'inputs': inputs, 'qualification': qualified,
        'code_sha256': {path: sha256((root / path).read_bytes()) for path in code},
        'provider_calls': 0, 'retries': 0,
    }
    destination.mkdir(parents=True, exist_ok=False)
    write_json(destination / 'amendment.json', amendment)
    outcomes = [{**slot, 'category': 'not_attempted'} for slot in manifest['slots']]
    write_json(destination / 'outcomes.json', outcomes)
    for slot in outcomes:
        run = destination / 'runs' / slot['slot_id']
        run_inputs = run / 'input'
        run_inputs.mkdir(parents=True)
        original_inputs = source / 'runs' / slot['slot_id'] / 'input'
        for name, expected in inputs[slot['slot_id']].items():
            data = (original_inputs / name).read_bytes()
            if {'sha256': sha256(data), 'bytes': len(data)} != expected:
                raise ValueError('original input changed after amendment freeze')
            (run_inputs / name).write_bytes(data)
        slot.update(category='execution_in_progress', started_at_utc=datetime.now(timezone.utc).isoformat())
        write_json(destination / 'outcomes.json', outcomes)
        try:
            execution = execute(image, run_inputs, run / 'output')
            report = run / 'output/todomvc-qualification-junit.xml'
            result = classify_junit(report.read_bytes() if report.is_file() else None, execution['returncode'])
            slot.update(result)
            slot['native_media_present'] = has_native_media(run / 'output')
            if execution.get('timed_out') or execution.get('image') != image:
                slot.update(category='build_or_executor_error', e2e_result=result,
                            error='executor image mismatch or timeout')
            elif result['category'] in {'pass', 'targeted_escape_defect', 'other_test_failure'} and not slot['native_media_present']:
                slot.update(category='build_or_executor_error', e2e_result=result,
                            error='native screenshot/video evidence missing or invalid')
        except Exception as exc:
            slot.update(category='build_or_executor_error', error=f'{type(exc).__name__}: {exc}')
        slot['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
        write_json(destination / 'outcomes.json', outcomes)
        print(slot['slot_id'], slot['category'], flush=True)
    if inventory(source) != original_inventory:
        raise ValueError('original collection changed during supplementary replay')
    receipt = {'confirmatory': False, 'preregistered': False, 'provider_calls': 0,
               'amendment_sha256': sha256((destination / 'amendment.json').read_bytes()),
               'original_receipt_sha256': amendment['original_receipt_sha256'],
               'outcomes': outcomes, 'files': inventory(destination)}
    write_json(destination / 'receipt.json', receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'destination', 'qualification'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--image', required=True)
    replay(**vars(parser.parse_args()))
