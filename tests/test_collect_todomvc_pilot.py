import json
import os
from pathlib import Path
import stat
from types import SimpleNamespace

import pytest

from eval import collect_todomvc_pilot as collector
from tests.test_todomvc_pilot import FROZEN_COMPONENT


@pytest.mark.parametrize('failure', ['provider', 'executor', 'missing_media'])
def test_all_nine_slots_survive_collection_failures(tmp_path, monkeypatch, failure):
    original = tmp_path / 'source.vue'
    original.write_bytes(FROZEN_COMPONENT)
    executable = tmp_path / 'codex'
    executable.write_bytes(b'fake executable')
    qualification = tmp_path / 'qualification'
    for arm in ('gold', 'mutant'):
        output = qualification / arm / 'output'
        output.mkdir(parents=True)
        (output / 'executor.json').write_text(json.dumps({'image': 'frozen-image', 'timed_out': False,
                                                         'returncode': 0 if arm == 'gold' else 1}))
        (output / 'todomvc-qualification-junit.xml').write_bytes(arm.encode())
        (output / 'body-validation.log').write_text('')
        for kind, name in [('screenshots', 'escape-after-interaction.png'), ('videos', 'run.mp4')]:
            (output / kind).mkdir()
            (output / kind / name).write_bytes(b'\x89PNG\r\n\x1a\n' if kind == 'screenshots' else b'\x00\x00\x00\x20ftyp')
    monkeypatch.setattr(collector, 'classify_junit', lambda report, rc: {
        'category': 'pass' if report == b'gold' else 'targeted_escape_defect'})
    monkeypatch.setattr(collector.subprocess, 'run', lambda *a, **k: SimpleNamespace(stdout='test-cli'))
    calls = []

    class Provider:
        last_call_metadata = {'usage': {'input_tokens': 1, 'output_tokens': 1}}

        def __init__(self, **kwargs):
            pass

        def complete(self, request):
            calls.append(request.prompt)
            if failure == 'provider':
                raise TimeoutError('ambiguous remote outcome')
            return '{"handler_body":"editing.value = false;"}'

    def execute(image, inputs, output):
        if failure == 'missing_media':
            output.mkdir()
            (output / 'todomvc-qualification-junit.xml').write_bytes(b'gold')
            return {'returncode': 0}
        raise RuntimeError('container unavailable')

    monkeypatch.setattr(collector, 'CodexCLIProvider', Provider)
    monkeypatch.setattr(collector, 'execute', execute)
    destination = tmp_path / 'collection'
    receipt = collector.collect(destination, original, qualification, 'frozen-image', executable, 'model')
    outcomes = receipt['outcomes']
    assert len(outcomes) == 9
    assert len({r['slot_id'] for r in outcomes}) == 9
    assert stat.S_IMODE(destination.stat().st_mode) == 0o700
    private_json = [destination / 'outcomes.json', destination / 'receipt.json']
    private_json.extend(destination.glob('runs/*/response.json'))
    private_json.extend(destination.glob('runs/*/provider-metadata.json'))
    assert private_json
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in private_json)
    if failure == 'provider':
        assert len(calls) == 1
        assert outcomes[0]['category'] == 'generation_error'
        assert all(r['category'] == 'not_attempted' for r in outcomes[1:])
    else:
        assert len(calls) == 9
        assert all(r['category'] == 'build_or_executor_error' for r in outcomes)
        assert len(list(destination.glob('runs/*/response.json'))) == 9
        if failure == 'missing_media':
            assert all(r['e2e_result']['category'] == 'pass' for r in outcomes)
            assert all(r['native_media_present'] is False for r in outcomes)
    with pytest.raises(FileExistsError):
        collector.collect(destination, original, qualification, 'frozen-image', executable, 'model')


def test_private_destination_rejects_relative_repository_and_symlink_parent(tmp_path):
    repository = Path(collector.__file__).resolve().parents[1]
    with pytest.raises(ValueError, match='absolute private path'):
        collector._validate_private_destination(Path('relative'), repository)
    with pytest.raises(ValueError, match='outside the repository'):
        collector._validate_private_destination(repository / 'private-run', repository)
    parent_link = tmp_path / 'linked-parent'
    parent_link.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match='existing real directory'):
        collector._validate_private_destination(parent_link / 'run', repository)


@pytest.mark.parametrize('kind', ['symlink', 'fifo'])
def test_inventory_fails_closed_for_non_regular_entries(tmp_path, kind):
    evidence = tmp_path / 'evidence'
    evidence.mkdir()
    (evidence / 'regular').write_text('evidence')
    special = evidence / kind
    if kind == 'symlink':
        special.symlink_to(evidence / 'regular')
    else:
        os.mkfifo(special)
    with pytest.raises(ValueError, match='regular files and directories'):
        collector.inventory(evidence)


def test_json_write_is_atomic_private_and_refuses_symlink(tmp_path, monkeypatch):
    path = tmp_path / 'outcomes.json'
    collector.write_json(path, {'state': 'before'})
    assert json.loads(path.read_text()) == {'state': 'before'}
    assert stat.S_IMODE(path.stat().st_mode) == 0o600

    original_replace = collector.os.replace

    def interrupt(source, destination):
        raise OSError('simulated interruption before publication')

    monkeypatch.setattr(collector.os, 'replace', interrupt)
    with pytest.raises(OSError, match='simulated interruption'):
        collector.write_json(path, {'state': 'after'})
    assert json.loads(path.read_text()) == {'state': 'before'}
    assert not list(tmp_path.glob('.*.tmp'))
    monkeypatch.setattr(collector.os, 'replace', original_replace)

    target = tmp_path / 'target.json'
    target.write_text('{}')
    link = tmp_path / 'link.json'
    link.symlink_to(target)
    with pytest.raises(ValueError, match='regular file'):
        collector.write_json(link, {'state': 'forbidden'})


def test_root_collector_stops_before_qualification_or_provider(tmp_path, monkeypatch):
    monkeypatch.setattr(os, 'getuid', lambda: 0)
    with pytest.raises(ValueError, match='non-root'):
        collector.collect(tmp_path / 'new-run', tmp_path / 'absent-source',
                          tmp_path / 'absent-qualification', 'frozen-image',
                          tmp_path / 'absent-cli', 'model')
    assert not (tmp_path / 'new-run').exists()
