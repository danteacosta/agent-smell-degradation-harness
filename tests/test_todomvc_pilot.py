"""Observable contracts for the exploratory requirement-completion pilot."""
import hashlib
import json
from xml.etree import ElementTree as ET

import pytest

from eval import todomvc_pilot as pilot


FROZEN_COMPONENT = b'<script setup>\nimport { ref, nextTick } from \'vue\'\n\nconst props = defineProps([\'todo\']);\nconst emit = defineEmits([\'delete-todo\', \'edit-todo\', \'toggle-todo\']);\n\nconst editing = ref(false);\nconst editInput = ref(null);\nconst draft = ref(\'\');\n\nfunction onToggle(event) {\n    emit(\'toggle-todo\', props.todo, event.target.checked);\n}\n\nfunction startEdit() {\n    draft.value = props.todo.title;\n    editing.value = true;\n    nextTick(() => editInput.value?.focus());\n}\n\nfunction commitEdit() {\n    if (!editing.value) return;\n    editing.value = false;\n    const text = draft.value.trim();\n    if (text.length === 0) emit(\'delete-todo\', props.todo);\n    else emit(\'edit-todo\', props.todo, text);\n}\n\nfunction cancelEdit() {\n    editing.value = false;\n    draft.value = props.todo.title;\n}\n\nfunction deleteTodo() {\n    emit(\'delete-todo\', props.todo);\n}\n</script>\n\n<template>\n    <li :class="{ completed: todo.completed, editing }">\n        <div class="view">\n            <input type="checkbox" class="toggle" :checked="todo.completed" @change="onToggle" />\n            <label @dblclick="startEdit">{{ todo.title }}</label>\n            <button class="destroy" @click.prevent="deleteTodo"></button>\n        </div>\n        <input\n            v-if="editing"\n            ref="editInput"\n            type="text"\n            class="edit"\n            aria-label="Edit todo"\n            v-model="draft"\n            @keyup.enter="commitEdit"\n            @keyup.escape="cancelEdit"\n            @blur="commitEdit"\n        />\n    </li>\n</template>\n'


@pytest.fixture
def scaffold():
    return pilot.make_scaffold(FROZEN_COMPONENT)

def test_prompts_only_differ_in_requirement(scaffold):
    prompts = [pilot.build_prompt(scaffold, arm) for arm in pilot.REQUIREMENTS]
    normalized = [p.replace(pilot.REQUIREMENTS[a], '<requirement>')
                  for a, p in zip(pilot.REQUIREMENTS, prompts)]
    assert len(set(normalized)) == 1
    assert 'cancelEdit' not in scaffold
    assert 'Cypress' not in prompts[0]
    assert all(p.count(pilot.PLACEHOLDER) == 1 for p in prompts)


def test_rejects_source_drift():
    with pytest.raises(ValueError, match='frozen'):
        pilot.make_scaffold(b'<script>changed</script>')


def test_schedule_preserves_all_nine_slots():
    slots = pilot.planned_slots()
    assert slots == pilot.planned_slots()
    assert len({s['slot_id'] for s in slots}) == 9
    assert {(s['arm'], s['repetition']) for s in slots} == {
        (a, r) for a in pilot.REQUIREMENTS for r in (1, 2, 3)}


def test_assembly_changes_only_placeholder(scaffold):
    body = 'editing.value = false;'
    result = pilot.assemble_response(scaffold, json.dumps({'handler_body': body}))
    assert result.decode() == scaffold.replace(pilot.PLACEHOLDER, body)


@pytest.mark.parametrize('response', [
    '```json\n{"handler_body":"x"}\n```', '{}',
    '{"handler_body":12}', '{"handler_body":""}',
    '{"handler_body":"x","extra":true}',
    '{"handler_body":"x","handler_body":"y"}',
    '{"handler_body":"</script><script>alert(1)</script>"}',
])
def test_rejects_invalid_completion(response):
    with pytest.raises(ValueError):
        pilot.assemble_response('function handleEscape() {\n' + pilot.PLACEHOLDER + '\n}', response)


def report(names, *, failure=None, skipped=None):
    root = ET.Element('testsuites')
    suite = ET.SubElement(root, 'testsuite')
    for name in names:
        case = ET.SubElement(suite, 'testcase', name=name)
        if name == failure:
            ET.SubElement(case, 'failure', type='AssertionError', message="expected '<li>' to contain 'feed the cat'")
        if name == skipped:
            ET.SubElement(case, 'skipped')
    return ET.tostring(root)


@pytest.fixture
def inventory(monkeypatch):
    names = [pilot.ESCAPE_TEST] + [f'test {n}' for n in range(27)]
    monkeypatch.setattr(pilot, 'INVENTORY_SHA256', hashlib.sha256(json.dumps(sorted(names)).encode()).hexdigest())
    return names


def test_pass_requires_complete_inventory_and_success(inventory):
    assert pilot.classify_junit(report(inventory), 0)['category'] == 'pass'
    for data, code in [(None, 0), (b'bad', 1), (report(inventory[:-1]), 0),
                       (report(inventory + [inventory[0]]), 0),
                       (report(inventory, skipped=inventory[1]), 0),
                       (report(inventory), 1)]:
        assert pilot.classify_junit(data, code)['category'] == 'build_or_executor_error'


def test_target_failure_is_distinct_from_other_failures(inventory):
    assert pilot.classify_junit(report(inventory, failure=pilot.ESCAPE_TEST), 1)['category'] == 'targeted_escape_defect'
    assert pilot.classify_junit(report(inventory, failure=inventory[1]), 1)['category'] == 'other_test_failure'
    assert pilot.classify_junit(report(inventory, failure=pilot.ESCAPE_TEST), 0)['category'] == 'build_or_executor_error'


def test_freeze_is_fresh_and_hash_binds_every_prompt(tmp_path, scaffold):
    output = tmp_path / 'frozen'
    manifest = pilot.freeze_manifest(output, scaffold, {'runtime_image_id': 'sha256:example'})
    assert len(manifest['slots']) == 9
    for arm, artifact in manifest['prompts'].items():
        assert hashlib.sha256((output / artifact['path']).read_bytes()).hexdigest() == artifact['sha256']
    assert manifest['bindings']['runtime_image_id'] == 'sha256:example'
    with pytest.raises(FileExistsError):
        pilot.freeze_manifest(output, scaffold, {})


def test_same_size_wrong_inventory_is_not_a_pass(inventory):
    changed = inventory.copy()
    changed[-1] = 'different test'
    assert pilot.classify_junit(report(changed), 0)['category'] == 'build_or_executor_error'


def test_escape_failure_at_another_assertion_is_not_targeted(inventory):
    data = report(inventory, failure=pilot.ESCAPE_TEST).replace(
        b"to contain 'feed the cat'", b"not to have class 'editing'")
    assert pilot.classify_junit(data, 1)['category'] == 'other_test_failure'


def test_executor_termination_is_not_a_test_defect(inventory):
    data = report(inventory, failure=pilot.ESCAPE_TEST)
    assert pilot.classify_junit(data, -15)['category'] == 'build_or_executor_error'


def test_assembly_requires_one_placeholder():
    for scaffold in ('none', pilot.PLACEHOLDER * 2):
        with pytest.raises(ValueError, match='exactly one'):
            pilot.assemble_response(scaffold, '{"handler_body":"return;"}')
