"""Behavior of subscription completions with a fake official CLI process."""
import json
import sys
import pytest
from agents.providers import ProviderRequest
from agents.claude_cli import ClaudeCLIProvider

MODEL = 'claude-sonnet-4-6'


def cli(tmp_path, *, auth='claude.ai', tools=None, model=MODEL, tool_call=False, delay=0, telemetry=False):
    path = tmp_path / 'claude-fake'
    events = [
        {'type': 'system', 'subtype': 'init', 'model': model, 'tools': tools or [], 'mcp_servers': []},
        {'type': 'assistant', 'message': {'model': model, 'content': [{'type': 'text', 'text': 'answer'}]}},
        {'type': 'result', 'subtype': 'success', 'is_error': False, 'result': 'answer', 'num_turns': 1,
         'usage': {'input_tokens': 10, 'output_tokens': 3}, 'modelUsage': {model: {}}},
    ]
    if telemetry:
        events.insert(1,{'type':'system','subtype':'thinking_tokens','estimated_tokens':50,'estimated_tokens_delta':50})
    if tool_call:
        events[1]['message']['content'] = [{'type': 'tool_use', 'name': 'Read'}]
    path.write_text(f'''#!{sys.executable}
import json, os, sys, time
assert not any(k in os.environ for k in ('ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','CLAUDE_CODE_OAUTH_TOKEN','CLAUDE_CODE_USE_VERTEX'))
assert os.environ.get('CLAUDE_CODE_MAX_RETRIES') == '0'
if sys.argv[1:] == ['auth','status']:
    print(json.dumps({{'loggedIn': True, 'authMethod': {auth!r}, 'apiProvider': 'firstParty', 'subscriptionType':'max'}}))
    sys.exit(0)
assert '--tools' in sys.argv and sys.argv[sys.argv.index('--tools')+1] == ''
assert '--strict-mcp-config' in sys.argv
assert '--safe-mode' in sys.argv and '--no-session-persistence' in sys.argv
assert '--setting-sources' in sys.argv and sys.argv[sys.argv.index('--setting-sources')+1] == ''
assert '--fallback-model' not in sys.argv and '--bare' not in sys.argv
assert sys.stdin.read() in ('public prompt', 'Return exactly SETUP_OK.')
time.sleep({delay})
for event in {events!r}: print(json.dumps(event))
''')
    path.chmod(0o700)
    return str(path)


def req():
    return ProviderRequest('public prompt', {'oracle':'never forward'}, 'opaque','code')


def test_account_completion_disables_tools_and_keeps_private_receipt(tmp_path, monkeypatch):
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'must-not-forward')
    p = ClaudeCLIProvider(executable=cli(tmp_path), model=MODEL, evidence_directory=tmp_path/'capture')
    assert p.complete(req()) == 'answer'
    assert p.last_call_metadata['response_model'] == MODEL
    assert p.last_call_metadata['estimated_cost_usd'] is None
    assert (tmp_path/'capture/metadata.json').exists()
    with pytest.raises(FileExistsError):p.complete(req())


@pytest.mark.parametrize('kwargs', [
    {'auth':'api_key'}, {'tools':['Read']}, {'tool_call':True}, {'model':'claude-opus-4-6'},
])
def test_rejects_api_tools_or_model_switch(tmp_path, kwargs):
    with pytest.raises(RuntimeError):
        ClaudeCLIProvider(executable=cli(tmp_path,**kwargs), model=MODEL).complete(req())


def test_timeout_records_single_failed_attempt(tmp_path):
    p = ClaudeCLIProvider(executable=cli(tmp_path,delay=2),model=MODEL,timeout_seconds=.1,evidence_directory=tmp_path/'capture')
    with pytest.raises(TimeoutError):p.complete(req())
    assert (tmp_path/'capture/attempt.json').exists()


def test_technical_checker_completes_offline_without_research_data(tmp_path):
    import subprocess
    from pathlib import Path
    executable = cli(tmp_path)
    checker = Path(__file__).resolve().parents[1] / 'scripts/claude_subscription_check.py'
    result = subprocess.run([sys.executable, str(checker), '--executable', executable,
                             '--model', MODEL, '--evidence-directory', str(tmp_path/'check')],
                            capture_output=True, text=True, timeout=10)
    # Fake returns "answer", so the call is recorded but literal qualification fails.
    assert result.returncode == 2
    summary = json.loads(result.stdout)
    assert summary['scientific_calls'] == 0
    assert summary['technical_qualified'] is False
    assert (tmp_path/'check/metadata.json').is_file()
