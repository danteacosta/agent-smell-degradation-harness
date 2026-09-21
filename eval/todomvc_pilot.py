"""Frozen, descriptive protocol for the nine-slot exploratory TodoMVC pilot.

These helpers perform no provider calls and execute no generated JavaScript.
The trusted offline executor must additionally parse the returned body as exactly
one function declaration before building the assembled component.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import re
from xml.etree import ElementTree

from eval.todomvc_escape_qualification import ESCAPE_TEST

SEED = 20260921
PLACEHOLDER = '/* PILOT_HANDLER_BODY */'
SOURCE_BLOB = '3ca0eb4233e2fee3fddea3d198c58617844eb045'
INVENTORY_SHA256 = '4cab322b79ed8d48bdd335d3d70deaeaf6ae68ec524ea10b19f49bbd7b4be734'
REQUIREMENTS = {
    'complete': 'If escape is pressed during the edit, the edit state should be left and any changes be discarded.',
    'rewrite': 'Pressing Escape while editing must exit edit mode without saving the draft.',
    'missing_condition': 'If escape is pressed during the edit, the edit state should be left.',
}
_ORIGINAL_HANDLER = '''function cancelEdit() {
    editing.value = false;
    draft.value = props.todo.title;
}'''


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_scaffold(original: bytes) -> str:
    """Accept only the immutable upstream component, remove its Escape answer."""
    blob = hashlib.sha1(f'blob {len(original)}\0'.encode() + original,
                        usedforsecurity=False).hexdigest()
    if blob != SOURCE_BLOB:
        raise ValueError('component differs from frozen upstream source')
    text = original.decode('utf-8')
    return text.replace(_ORIGINAL_HANDLER,
                        'function handleEscape() {\n' + PLACEHOLDER + '\n}').replace(
                            '@keyup.escape="cancelEdit"', '@keyup.escape="handleEscape"')


def build_prompt(scaffold: str, arm: str) -> str:
    if scaffold.count(PLACEHOLDER) != 1:
        raise ValueError('scaffold must contain exactly one placeholder')
    requirement = REQUIREMENTS[arm]
    return (
        'Complete the handleEscape function body in this Vue component to satisfy '
        'the requirement below. Use the state and helpers already present. '
        'Return only a JSON object with exactly one string field, "handler_body". '
        'The string must contain only JavaScript statements for that function body; '
        'do not return a function declaration, other component edits, or Markdown.\n\n'
        f'Requirement:\n{requirement}\n\nComponent:\n{scaffold}'
    )


def planned_slots(seed: int = SEED) -> list[dict]:
    """Three fresh calls per requirement, randomized before observing outcomes."""
    slots = [{'slot_id': f'{arm}-{repetition}', 'arm': arm, 'repetition': repetition}
             for arm in REQUIREMENTS for repetition in (1, 2, 3)]
    random.Random(seed).shuffle(slots)
    return slots


def _unique_object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON field')
        result[key] = value
    return result


def parse_response(raw: str) -> str:
    """No extraction, repair, fences or alternate answer candidates are allowed."""
    try:
        value = json.loads(raw, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError('completion must be a JSON object') from exc
    if not isinstance(value, dict) or set(value) != {'handler_body'}:
        raise ValueError('completion requires exactly handler_body')
    body = value['handler_body']
    if not isinstance(body, str) or not body.strip() or len(body.encode('utf-8')) > 32768:
        raise ValueError('handler_body must be a nonempty string of at most 32768 bytes')
    if re.search(r'</script\b', body, re.IGNORECASE) or '\x00' in body:
        raise ValueError('handler_body cannot terminate the component script')
    return body


def assemble_response(scaffold: str, raw: str) -> bytes:
    if scaffold.count(PLACEHOLDER) != 1:
        raise ValueError('scaffold must contain exactly one placeholder')
    return scaffold.replace(PLACEHOLDER, parse_response(raw)).encode('utf-8')


def classify_junit(report: bytes | None, returncode: int) -> dict:
    """Fail closed on partial suites, duplicate tests or inconsistent exit status.

    Only the known title-discard assertion alone is a targeted Escape defect.
    Other complete-suite assertion failures remain visible as other_test_failure.
    """
    invalid = {'category': 'build_or_executor_error', 'reason': 'missing or invalid complete JUnit evidence'}
    if not report:
        return invalid
    try:
        root = ElementTree.fromstring(report)
    except ElementTree.ParseError:
        return invalid
    if root.tag not in {'testsuite', 'testsuites'}:
        return invalid
    cases = list(root.iter('testcase'))
    names = [case.get('name') for case in cases]
    if len(cases) != 28 or any(not name for name in names) or len(set(names)) != 28:
        return invalid
    inventory = sha256(json.dumps(sorted(names)).encode())
    if inventory != INVENTORY_SHA256:
        return invalid
    failed = []
    targeted = False
    for case in cases:
        failures = case.findall('failure')
        if case.findall('skipped') or case.findall('error') or len(failures) > 1:
            return invalid
        if failures:
            failure = failures[0]
            failed.append(case.get('name'))
            targeted = (case.get('name') == ESCAPE_TEST
                        and failure.get('type') == 'AssertionError'
                        and re.fullmatch(
                            r"(?:Timed out retrying(?: after [0-9]+ms)?: )?expected '<li>' to contain 'feed the cat'",
                            failure.get('message', '')) is not None)
    if (not failed and returncode != 0) or (failed and returncode != 1):
        return {**invalid, 'reason': 'JUnit and executor exit status disagree'}
    category = ('pass' if not failed else
                'targeted_escape_defect' if failed == [ESCAPE_TEST] and targeted
                else 'other_test_failure')
    return {'category': category, 'tests': 28, 'passed': 28 - len(failed),
            'failed_tests': failed, 'test_inventory_sha256': inventory,
            'junit_sha256': sha256(report)}


def freeze_manifest(output: Path, scaffold: str, bindings: dict) -> dict:
    """Create a fresh protocol directory; caller supplies qualified runtime hashes.

    The returned manifest includes every planned slot. Result collection must not
    rewrite these files; write observed outcomes separately, including errors and
    not-attempted slots. Bindings are provenance, not an admission assertion.
    """
    prompts = {arm: build_prompt(scaffold, arm) for arm in REQUIREMENTS}
    serialized_bindings = json.loads(json.dumps(bindings, allow_nan=False))
    output.mkdir(parents=True, exist_ok=False)
    (output / 'scaffold.vue').write_bytes(scaffold.encode())
    prompt_entries = {}
    for arm, prompt in prompts.items():
        path = f'prompt-{arm}.txt'
        data = prompt.encode()
        (output / path).write_bytes(data)
        prompt_entries[arm] = {'path': path, 'sha256': sha256(data)}
    manifest = {
        'schema_version': 'todomvc-exploratory-pilot-v1',
        'confirmatory': False, 'independent_reviews': 'pending',
        'seed': SEED, 'slots': planned_slots(), 'requirements': dict(REQUIREMENTS),
        'scaffold': {'path': 'scaffold.vue', 'sha256': sha256(scaffold.encode())},
        'prompts': prompt_entries, 'bindings': serialized_bindings,
    }
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return manifest
