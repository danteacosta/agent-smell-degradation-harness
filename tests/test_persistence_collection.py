import json
from pathlib import Path

import pytest

from scripts import persistence_collection as c
from scripts.behavioral_expansion import plan_slots

HTML = '<!DOCTYPE html><html><body>test</body></html>'


@pytest.fixture
def packet(tmp_path, monkeypatch):
    parent = tmp_path / 'parent'
    parent.mkdir(mode=0o700)
    record = {'id': 'todomvc-persistence', 'project_id': 'todomvc', 'status': 'qualified',
              'variants': {'A': 'full', 'B': 'rewrite', 'C': 'omission'}}
    slots = plan_slots([record], seed=20260923)
    c.put(parent / 'frozen/schedule.json', slots)
    c.put(parent / 'frozen/manifest.json', {'image_id': 'sha256:' + 'a'*64,
        'scope': 'second same-origin page visible edit mode'})
    for s in slots:
        c.put(parent / 'frozen/requests' / (s['slot_id']+'.json'), {'prompt': record['variants'][s['variant']]})
    for name in c.ENDPOINT_FILES:
        c.put(parent / 'frozen/runtime' / name, (c.ROOT/name).read_bytes())
    c.put(parent / 'receipt.json', {'files': c.hash_inventory(parent)})
    monkeypatch.setattr(c, 'PARENT_RECEIPT', c.hash_file(parent/'receipt.json'))
    exe = tmp_path / 'cli'
    exe.write_text('#!/bin/sh\necho test\n')
    exe.chmod(0o700)
    dest = tmp_path/'collection'
    preflight = {'ordinary_usage_allowed': True, 'checked_at_utc': c.now(),
                 'chatgpt_auth': True, 'required_cli_flags': True, 'image_verified': True,
                 'isolation_verified': True}
    c.prepare(parent, dest, exe, preflight)
    return dest, slots, exe


def provider_factory(calls, error_at=None, invalid_at=None):
    class Provider:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.last_call_metadata = {'billing_mode': 'chatgpt_subscription'}
        def complete(self, request):
            calls.append(request.prompt)
            if len(calls) == error_at:
                raise RuntimeError('provider unavailable')
            return '```html\n'+HTML+'\n```' if len(calls) == invalid_at else HTML
    return Provider


def test_exact_prompts_once_then_browser_and_no_resume(packet):
    dest, slots, _ = packet
    calls = []
    executed = []
    def executor(**kwargs):
        assert len(calls) == 18
        assert (kwargs['inputs']/'app.html').read_text() == HTML
        executed.append(kwargs)
        return {'category': 'pass', 'target_failed': False, 'non_target_failed': []}
    report = c.run(dest, provider_factory(calls), executor)
    assert calls == [json.loads((dest/'frozen/requests'/(s['slot_id']+'.json')).read_text())['prompt'] for s in slots]
    assert len(executed) == 18
    assert report['unknown'] == 0
    with pytest.raises(FileExistsError):
        c.run(dest, provider_factory(calls), executor)
    assert len(calls) == 18


def test_invalid_output_and_provider_failure_preserve_fixed_denominator(packet):
    dest, slots, _ = packet
    calls = []
    report = c.run(dest, provider_factory(calls, error_at=3, invalid_at=2),
                   lambda **kwargs: {'category': 'target_not_evaluable', 'target_failed': None, 'non_target_failed': []})
    rows = json.loads((dest/'results.json').read_text())['rows']
    assert [r['category'] for r in rows[:4]] == ['target_not_evaluable','invalid_output','provider_error','not_attempted']
    assert report['planned'] == report['unknown'] == 18
    assert len(calls) == 3
    assert (dest/'calls'/slots[1]['slot_id']/'response.txt').read_text().startswith('```')


@pytest.mark.parametrize('drift', ['prompt', 'executable', 'source'])
def test_drift_rejects_before_provider(packet, drift, monkeypatch):
    dest, slots, exe = packet
    if drift == 'prompt':
        (dest/'frozen/requests'/(slots[0]['slot_id']+'.json')).write_text('{}')
    elif drift == 'executable':
        exe.write_text('changed')
    else:
        monkeypatch.setattr(c, 'runtime_hashes', lambda: {})
    calls = []
    with pytest.raises(ValueError, match='drift|inventory'):
        c.run(dest, provider_factory(calls), lambda **kw: {})
    assert calls == []


def test_interruption_has_attempt_marker_and_cannot_resume(packet):
    dest, slots, _ = packet
    class Interrupted:
        def __init__(self, **kwargs): pass
        def complete(self, request): raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt): c.run(dest, Interrupted, lambda **kw: {})
    assert (dest/'calls'/slots[0]['slot_id']/'attempt.json').is_file()
    with pytest.raises(FileExistsError): c.run(dest, Interrupted, lambda **kw: {})


@pytest.mark.parametrize('raw', ['```html\n'+HTML+'\n```', json.dumps({'html':HTML}), 'explanation\n'+HTML, HTML+'trailer', '<html>'+(' '*200000)+'</html>'])
def test_output_rule_rejects_without_repair(raw):
    with pytest.raises(ValueError): c.html_bytes(raw)


def test_output_rule_preserves_exact_bytes():
    raw = '\n '+HTML+'\n'
    assert c.html_bytes(raw) == raw.encode()


def test_failed_directory_flush_prevents_provider_dispatch(packet, monkeypatch):
    dest, _, _ = packet
    original = c.sync_directory
    def fail_calls(path):
        if path.name == 'calls':
            raise OSError('durability unavailable')
        original(path)
    monkeypatch.setattr(c, 'sync_directory', fail_calls)
    calls = []
    with pytest.raises(OSError): c.run(dest, provider_factory(calls), lambda **kw: {})
    assert calls == []
