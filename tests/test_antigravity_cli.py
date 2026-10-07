"""Acceptance checks for the subscription adapter, without network inference."""
import json
import hashlib
import sys

import pytest
from pathlib import Path
from agents.providers import ProviderRequest
from agents.antigravity_cli import AntigravityCLIProvider


def fixture(tmp_path, *, tools=None, model='gemini-3.1-pro-low', status='SUCCESS', delay=0):
    path = tmp_path / 'agy-fake'
    events = [
        {'event': 'init', 'init': {'model': model, 'agent': 'research-text', 'tools': tools or []}},
        {'event': 'result', 'result': {'status': status, 'response': 'answer', 'num_turns': 1,
                                     'usage': {'input_tokens': 10, 'output_tokens': 3}}},
    ]
    path.write_text(f'''#!{sys.executable}
import json, os, sys, time
assert not any(k in os.environ for k in ('GEMINI_API_KEY', 'GOOGLE_API_KEY', 'OPENAI_API_KEY'))
assert '--disable-slash-commands' in sys.argv
assert '--conversation' not in sys.argv and '--continue' not in sys.argv
assert sys.stdin.read() == 'public prompt'
time.sleep({delay})
for event in {events!r}: print(json.dumps(event))
''')
    path.chmod(0o700)
    return str(path)


def provider(tmp_path, **kwargs):
    executable = fixture(tmp_path, **kwargs)
    stream = [
        {'event': 'init', 'init': {'model': 'gemini-3.1-pro-low', 'agent': 'research-text', 'tools': []}},
        {'event': 'result', 'result': {'status': 'SUCCESS', 'response': 'SETUP_OK', 'num_turns': 1,
                                     'usage': {'input_tokens': 10, 'output_tokens': 3}}},
    ]
    qualification = tmp_path / 'qualification.json'
    qualification.write_text(json.dumps({'executable_sha256': hashlib.sha256(Path(executable).read_bytes()).hexdigest(),
                                         'stream': '\n'.join(json.dumps(e) for e in stream)}))
    return AntigravityCLIProvider(executable=executable, model='gemini-3.1-pro-low',
                                 qualification_path=qualification, evidence_directory=tmp_path / 'capture')


def request():
    return ProviderRequest('public prompt', {'oracle': 'never forward'}, 'opaque', 'code')


def test_accepts_only_tool_free_text_and_records_usage(tmp_path, monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'do-not-forward')
    p = provider(tmp_path)
    assert p.complete(request()) == 'answer'
    assert p.last_call_metadata['confirmatory_eligible'] is False
    assert p.last_call_metadata['estimated_cost_usd'] is None
    assert json.loads((tmp_path / 'capture/metadata.json').read_text())['usage']['input_tokens'] == 10
    with pytest.raises(FileExistsError):
        p.complete(request())


@pytest.mark.parametrize('kwargs', [
    {'tools': ['search_web']}, {'model': 'gemini-3.8-flash-low'}, {'status': 'ERROR'},
])
def test_rejects_tools_fallback_or_failed_completion(tmp_path, kwargs):
    with pytest.raises(RuntimeError):
        provider(tmp_path, **kwargs).complete(request())


def test_api_settings_are_rejected_before_launch(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    config = tmp_path / '.gemini/antigravity-cli/settings.json'
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps({'modelProvider': 'gemini'}))
    p = provider(tmp_path)
    with pytest.raises(RuntimeError, match='account'):
        p.complete(request())


def test_non_gemini_model_is_refused(tmp_path):
    with pytest.raises(ValueError):
        AntigravityCLIProvider(executable=fixture(tmp_path), model='claude-sonnet-4-6')


def test_timeout_preserves_failed_attempt_without_retry(tmp_path):
    p = provider(tmp_path, delay=2)
    p.timeout_seconds = 0.1
    with pytest.raises(TimeoutError):
        p.complete(request())
    assert (tmp_path / 'capture/attempt.json').exists()


def test_unqualified_cli_never_receives_a_private_prompt(tmp_path):
    p = AntigravityCLIProvider(executable=fixture(tmp_path), model='gemini-3.1-pro-low',
                              evidence_directory=tmp_path / 'capture')
    with pytest.raises(RuntimeError, match='qualification'):
        p.complete(request())
    assert not (tmp_path / 'capture').exists()


def test_failed_qualification_never_starts_generation(tmp_path):
    p = provider(tmp_path)
    qualification = json.loads(p.qualification_path.read_text())
    events = [json.loads(line) for line in qualification['stream'].splitlines()]
    events[0]['init']['tools'] = ['view_file']
    qualification['stream'] = '\n'.join(json.dumps(e) for e in events)
    p.qualification_path.write_text(json.dumps(qualification))
    with pytest.raises(RuntimeError):
        p.complete(request())
    assert not (tmp_path / 'capture').exists()


def test_changed_binary_invalidates_qualification(tmp_path):
    p = provider(tmp_path)
    p.executable.write_text(p.executable.read_text() + '\n# changed\n')
    with pytest.raises(RuntimeError, match='qualification'):
        p.complete(request())
    assert not (tmp_path / 'capture').exists()
