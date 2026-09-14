import json
import os
import sys

import pytest

from agents.providers import ProviderRequest


def cli(tmp_path, *, auth='Logged in using ChatGPT', event=None, exit_code=0, delay=0):
    path = tmp_path / 'codex-fixture'
    events = event if event is not None else [
        {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': '{"answer":42}'}},
        {'type': 'turn.completed', 'usage': {'input_tokens': 10, 'output_tokens': 4, 'cached_input_tokens': 0}},
    ]
    path.write_text(f'''#!{sys.executable}
import json, os, sys, time
if sys.argv[1:] == ['login', 'status']:
    print({auth!r})
    sys.exit(0)
assert not any(k in os.environ for k in ('OPENAI_API_KEY', 'CODEX_API_KEY', 'ANTHROPIC_API_KEY'))
assert os.listdir('.') == []
assert sys.stdin.read() == 'public prompt only'
assert 'forced_login_method="chatgpt"' in sys.argv
time.sleep({delay})
for event in {events!r}: print(json.dumps(event))
sys.exit({exit_code})
''')
    path.chmod(0o700)
    return str(path)


def request():
    return ProviderRequest('public prompt only', {'oracle': 'secret hidden test'}, 'smelly', 'codegen')


def test_subscription_completion_isolated_and_reports_observed_usage(tmp_path, monkeypatch):
    from agents.codex_cli import CodexCLIProvider
    monkeypatch.setenv('OPENAI_API_KEY', 'must-not-inherit')
    monkeypatch.setenv('CODEX_API_KEY', 'must-not-inherit')
    provider = CodexCLIProvider(executable=cli(tmp_path), model='test-model')
    assert provider.complete(request()) == '{"answer":42}'
    assert provider.last_call_metadata['usage']['output_tokens'] == 4
    assert provider.last_call_metadata['billing_mode'] == 'chatgpt_subscription'
    assert provider.last_call_metadata['estimated_cost_usd'] is None


def test_api_auth_is_rejected_before_generation(tmp_path):
    from agents.codex_cli import CodexCLIProvider
    with pytest.raises(RuntimeError, match='ChatGPT'):
        CodexCLIProvider(executable=cli(tmp_path, auth='Logged in using an API key'), model='test').complete(request())


@pytest.mark.parametrize('event,code', [
    ([{'type': 'turn.failed', 'error': {'message': 'failed'}}], 0),
    ([{'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'partial'}}], 0),
    ([{'type': 'turn.completed', 'usage': {'input_tokens': 1, 'output_tokens': 2}}], 0),
    ([{'type': 'item.completed', 'item': {'type': 'command_execution'}}], 0),
    ([], 1),
])
def test_incomplete_or_tool_using_completion_fails_closed(tmp_path, event, code):
    from agents.codex_cli import CodexCLIProvider
    with pytest.raises(RuntimeError):
        CodexCLIProvider(executable=cli(tmp_path, event=event, exit_code=code), model='test').complete(request())


def test_timeout_is_not_retried(tmp_path):
    from agents.codex_cli import CodexCLIProvider
    with pytest.raises(TimeoutError):
        CodexCLIProvider(executable=cli(tmp_path, delay=2), model='test', timeout_seconds=0.05).complete(request())


def test_strict_api_token_cap_is_not_silently_ignored(tmp_path):
    from agents.codex_cli import CodexCLIProvider
    with pytest.raises(ValueError, match='token'):
        CodexCLIProvider(executable=cli(tmp_path), model='test').complete(
            ProviderRequest('public prompt only', {}, 'clean', 'codegen', max_output_tokens=10))


def test_cancellation_reaps_detached_cli(tmp_path, monkeypatch):
    import subprocess
    from agents.codex_cli import CodexCLIProvider
    communicate = subprocess.Popen.communicate
    children = []
    def interrupt(child, *args, **kwargs):
        if 'exec' in child.args:
            children.append(child)
            raise KeyboardInterrupt()
        return communicate(child, *args, **kwargs)
    monkeypatch.setattr(subprocess.Popen, 'communicate', interrupt)
    try:
        with pytest.raises(KeyboardInterrupt):
            CodexCLIProvider(executable=cli(tmp_path, delay=30), model='test').complete(request())
        assert children[0].poll() is not None
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.wait()
