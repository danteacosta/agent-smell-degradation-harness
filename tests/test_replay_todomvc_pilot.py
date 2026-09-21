"""Supplementary replay preserves original failures and never generates again."""
import hashlib
import json
from xml.etree import ElementTree as ET

import pytest

from eval import replay_todomvc_pilot as replay_module
from eval import todomvc_pilot as pilot

IMAGE = 'sha256:' + 'b' * 64


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value if isinstance(value, bytes) else value.encode())


def junit(names, fail=False):
    root = ET.Element('testsuite')
    for name in names:
        test = ET.SubElement(root, 'testcase', name=name)
        if fail and name == pilot.ESCAPE_TEST:
            ET.SubElement(test, 'failure', type='AssertionError', message="expected '<li>' to contain 'feed the cat'")
    return ET.tostring(root)


def media(output):
    put(output / 'screenshots/spec.cy.js/escape-after-interaction.png', b'\x89PNG\r\n\x1a\nx')
    put(output / 'videos/spec.cy.js.mp4', b'\x00\x00\x00\x20ftypx')


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    source = tmp_path / 'original'
    qualification = tmp_path / 'qualification'
    scaffold = 'function handleEscape() {\n' + pilot.PLACEHOLDER + '\n}'
    manifest = pilot.freeze_manifest(source / 'frozen', scaffold, {'image': 'sha256:' + 'a' * 64})
    outcomes = [{**slot, 'category': 'build_or_executor_error'} for slot in manifest['slots']]
    replay_module.write_json(source / 'outcomes.json', outcomes)
    response = '{"handler_body":"return;"}'
    component = pilot.assemble_response(scaffold, response)
    for slot in outcomes:
        run = source / 'runs' / slot['slot_id']
        put(run / 'response.json', response)
        put(run / 'input/response.json', response)
        put(run / 'input/TodoItem.vue', component)
        put(run / 'output/body-validation.log', "Error: Cannot find module 'acorn'")
    replay_module.write_json(source / 'receipt.json', {'confirmatory': False, 'outcomes': outcomes, 'files': replay_module.inventory(source)})
    names = [pilot.ESCAPE_TEST] + [f'test {i}' for i in range(27)]
    monkeypatch.setattr(pilot, 'INVENTORY_SHA256', hashlib.sha256(json.dumps(sorted(names)).encode()).hexdigest())
    for arm in ('gold', 'mutant'):
        run = qualification / arm
        put(run / 'input/response.json', response)
        put(run / 'input/TodoItem.vue', component)
        put(run / 'output/body-validation.log', '')
        put(run / 'output/executed-TodoItem.vue', component)
        put(run / 'output/todomvc-qualification-junit.xml', junit(names, arm == 'mutant'))
        replay_module.write_json(run / 'output/executor.json', {'returncode': int(arm == 'mutant'), 'timed_out': False, 'image': IMAGE})
        media(run / 'output')
    return source, qualification, names


def test_replay_freezes_amendment_then_executes_all_nine_once(bundle, tmp_path, monkeypatch):
    source, qualification, names = bundle
    before = replay_module.inventory(source)
    destination = tmp_path / 'replay'
    calls = []
    def execute(image, inputs, output):
        amendment = json.loads((destination / 'amendment.json').read_text())
        assert amendment['preregistered'] is False
        assert image == IMAGE
        assert (inputs / 'response.json').read_bytes() == (source / 'runs' / inputs.parent.name / 'input/response.json').read_bytes()
        calls.append(inputs.parent.name)
        if len(calls) == 2:
            raise RuntimeError('executor crashed')
        output.mkdir()
        put(output / 'todomvc-qualification-junit.xml', junit(names))
        if len(calls) != 3:
            media(output)
        return {'returncode': 0, 'timed_out': False, 'image': image}
    monkeypatch.setattr(replay_module, 'execute', execute)
    receipt = replay_module.replay(source, destination, qualification, IMAGE)
    assert calls == [slot['slot_id'] for slot in pilot.planned_slots()]
    assert len(receipt['outcomes']) == 9
    assert receipt['outcomes'][1]['category'] == 'build_or_executor_error'
    assert receipt['outcomes'][2]['e2e_result']['category'] == 'pass'
    assert replay_module.inventory(source) == before
    with pytest.raises(FileExistsError):
        replay_module.replay(source, destination, qualification, IMAGE)
    assert len(calls) == 9


@pytest.mark.parametrize('change', ['tamper', 'incomplete', 'wrong_error', 'old_e2e', 'symlink'])
def test_refuses_unqualified_original_before_any_execution(bundle, tmp_path, monkeypatch, change):
    source, qualification, _ = bundle
    slot = pilot.planned_slots()[0]['slot_id']
    if change == 'tamper':
        put(source / 'runs' / slot / 'input/TodoItem.vue', 'changed')
    elif change == 'symlink':
        (source / 'unexpected').symlink_to(source / 'outcomes.json')
    else:
        if change == 'incomplete':
            outcomes = json.loads((source / 'outcomes.json').read_text())[:-1]
            replay_module.write_json(source / 'outcomes.json', outcomes)
        elif change == 'wrong_error':
            put(source / 'runs' / slot / 'output/body-validation.log', 'different failure')
        else:
            put(source / 'runs' / slot / 'output/build.log', 'already built')
        receipt = json.loads((source / 'receipt.json').read_text())
        receipt['files'] = {k: v for k, v in replay_module.inventory(source).items() if k != 'receipt.json'}
        replay_module.write_json(source / 'receipt.json', receipt)
    monkeypatch.setattr(replay_module, 'execute', lambda *args: pytest.fail('must not execute'))
    with pytest.raises(ValueError):
        replay_module.replay(source, tmp_path / 'replay', qualification, IMAGE)


def test_qualification_must_exercise_response_validation(bundle, tmp_path, monkeypatch):
    source, qualification, _ = bundle
    (qualification / 'gold/output/body-validation.log').unlink()
    monkeypatch.setattr(replay_module, 'execute', lambda *args: pytest.fail('must not execute'))
    with pytest.raises(ValueError):
        replay_module.replay(source, tmp_path / 'replay', qualification, IMAGE)


@pytest.mark.parametrize('change', ['image', 'media', 'executed_component'])
def test_replay_refuses_wrong_corrected_qualification(bundle, tmp_path, monkeypatch, change):
    source, qualification, _ = bundle
    output = qualification / 'mutant/output'
    if change == 'image':
        execution = json.loads((output / 'executor.json').read_text())
        execution['image'] = 'sha256:' + 'c' * 64
        replay_module.write_json(output / 'executor.json', execution)
    elif change == 'media':
        (output / 'videos/spec.cy.js.mp4').unlink()
    else:
        put(output / 'executed-TodoItem.vue', 'different')
    monkeypatch.setattr(replay_module, 'execute', lambda *args: pytest.fail('must not execute'))
    with pytest.raises(ValueError):
        replay_module.replay(source, tmp_path / 'replay', qualification, IMAGE)


def test_missing_junit_is_retained_for_every_slot(bundle, tmp_path, monkeypatch):
    source, qualification, _ = bundle
    calls = []
    def execute(image, inputs, output):
        calls.append(inputs.parent.name)
        output.mkdir()
        return {'returncode': 0, 'image': image, 'timed_out': False}
    monkeypatch.setattr(replay_module, 'execute', execute)
    receipt = replay_module.replay(source, tmp_path / 'replay', qualification, IMAGE)
    assert len(calls) == 9
    assert all(slot['category'] == 'build_or_executor_error' for slot in receipt['outcomes'])
