import json
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
