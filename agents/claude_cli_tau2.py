"""Isolated tau2 structured transport; frozen text adapter remains unchanged."""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time
from agents.providers import ProviderRequest
from agents.claude_cli_v2 import validate_stream

ENVELOPE_SCHEMA = {
    'type':'object', 'additionalProperties':False,
    'required':['content','tool_calls'],
    'properties':{
        'content':{'type':['string','null']},
        'tool_calls':{'type':'array','items':{
            'type':'object','additionalProperties':False,
            'required':['name','arguments'],
            'properties':{'name':{'type':'string'},'arguments':{'type':'object'}}}},
    },
}


def validate_structured_stream(raw, model):
    """Accept only one assistant generation and its matching local validation."""
    try:
        events = [json.loads(line) for line in raw.splitlines() if line.strip()]
        initial = [e for e in events if e.get('type')=='system' and e.get('subtype')=='init']
        assistants = [e for e in events if e.get('type')=='assistant']
        users = [e for e in events if e.get('type')=='user']
        results = [e for e in events if e.get('type')=='result']
        if len(initial)!=1 or not assistants or len(users)!=1 or len(results)!=1:
            raise ValueError('one generation and one validation required')
        if initial[0].get('tools') != ['StructuredOutput']:
            raise ValueError('unexpected native capability')
        identities={(e['message'].get('id'),e.get('request_id')) for e in assistants}
        if len(identities)!=1 or any(not isinstance(v,str) or not v for pair in identities for v in pair):
            raise ValueError('one verifiable message/request identity required')
        if any(e['message'].get('model')!=model for e in assistants):
            raise ValueError('model switch')
        blocks = [block for e in assistants for block in e['message']['content']]
        calls = [b for b in blocks if b.get('type')=='tool_use']
        if (len(calls)!=1 or calls[0].get('name')!='StructuredOutput'
            or any(b.get('type') not in {'text','thinking','tool_use'} for b in blocks)):
            raise ValueError('only local formatting action allowed')
        call = calls[0]
        if not isinstance(call.get('id'),str) or not call['id']:
            raise ValueError('formatting action ID required')
        validation = users[0]['message']
        output = validation['content']
        if (validation.get('role')!='user' or len(output)!=1
            or output[0].get('type')!='tool_result'
            or output[0].get('tool_use_id')!=call['id']
            or output[0].get('is_error',False) is not False
            or output[0].get('content')!='Structured output provided successfully'):
            raise ValueError('successful matching format validation required')
        result = results[0]
        payload = result['structured_output']
        if (not isinstance(payload,dict) or payload!=call.get('input')
            or json.loads(result['result'])!=payload
            or result.get('num_turns')!=2):
            raise ValueError('unverifiable structured result')
        assistant_positions=[i for i,e in enumerate(events) if e.get('type')=='assistant']
        init_position=next(i for i,e in enumerate(events) if e is initial[0])
        validation_position=next(i for i,e in enumerate(events) if e is users[0])
        result_position=next(i for i,e in enumerate(events) if e is result)
        if not init_position < assistant_positions[0] <= assistant_positions[-1] < validation_position < result_position:
            raise ValueError('invalid generation/validation order')
        # The frozen validator checks model, errors, telemetry and usage. Its
        # text-only representation excludes only the verified local formatter.
        initial[0]['tools']=[]
        assistants[0]['message']['content']=[{'type':'text','text':json.dumps(payload,allow_nan=False)}]
        result['num_turns']=1
        result['result']=json.dumps(payload,allow_nan=False)
        normalized='\n'.join(json.dumps(e,allow_nan=False) for e in events
            if e is not users[0] and (e.get('type')!='assistant' or e is assistants[0]))
        return validate_stream(normalized,model)
    except (ValueError,TypeError,KeyError,AttributeError,IndexError) as exc:
        raise RuntimeError('Claude structured stream rejected: '+str(exc)) from None


class ClaudeStructuredCLIProvider:
    """Use saved Pro/Max OAuth for one generation with local JSON validation."""
    name = 'claude_cli_structured'

    def __init__(self, *, executable: str, model: str, timeout_seconds: float = 120,
                 evidence_directory: Path | str | None = None):
        if not re.fullmatch(r'claude-(sonnet|opus)-[0-9]+-[0-9]+(?:-[0-9]{8})?', model):
            raise ValueError('explicit Sonnet/Opus model ID required')
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError('positive finite timeout required')
        self.executable = str(Path(executable).resolve(strict=True))
        self.model, self.timeout_seconds = model, timeout_seconds
        self.evidence_directory = Path(evidence_directory) if evidence_directory is not None else None
        self.last_call_metadata = {}

    @staticmethod
    def _environment():
        env = {k: os.environ[k] for k in ('HOME', 'PATH', 'TMPDIR', 'LANG', 'USER', 'LOGNAME') if k in os.environ}
        env.update(MAX_STRUCTURED_OUTPUT_RETRIES='1', CLAUDE_CODE_MAX_RETRIES='0', CLAUDE_CODE_NONSTREAMING_TIMEOUT_RETRIES='0',
                   CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK='1', CLAUDE_CODE_RESUME_INTERRUPTED_TURN='0',
                   CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1',
                   CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL='1',
                   CLAUDE_CODE_SKIP_PROMPT_HISTORY='1', FALLBACK_FOR_ALL_PRIMARY_MODELS='1')
        return env

    def _save(self, name, data):
        if self.evidence_directory is not None:
            fd = os.open(self.evidence_directory / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as f:
                f.write(data if isinstance(data, bytes) else (json.dumps(data, sort_keys=True)+'\n').encode())

    def complete(self, request: ProviderRequest) -> str:
        self.last_call_metadata = {}
        if request.max_output_tokens is not None:
            raise ValueError('strict API output cap not supported')
        if not isinstance(request.prompt, str) or not request.prompt.strip() or len(request.prompt.encode()) > 100_000:
            raise ValueError('bounded nonempty prompt required')
        # Managed policy can override CLI settings. Refuse rather than assume isolation.
        for name in ('managed-settings.json', 'managed-mcp.json'):
            if (Path('/Library/Application Support/ClaudeCode') / name).exists():
                raise RuntimeError('managed Claude policy requires independent qualification')
        env = self._environment()
        auth = subprocess.run([self.executable, 'auth', 'status'], env=env, capture_output=True, text=True, timeout=15)
        try:
            status = json.loads(auth.stdout)
            if not isinstance(status,dict):
                raise ValueError('authentication object required')
        except ValueError:
            raise RuntimeError('Claude authentication status unavailable') from None
        if auth.returncode or status.get('loggedIn') is not True or status.get('authMethod') != 'claude.ai' or status.get('apiProvider') != 'firstParty' or status.get('subscriptionType') not in {'pro', 'max'}:
            raise RuntimeError('saved Claude Pro/Max subscription required; no API fallback')
        if self.evidence_directory is not None:
            self.evidence_directory.mkdir(mode=0o700, exist_ok=False)
        fingerprint = hashlib.sha256(Path(self.executable).read_bytes()).hexdigest()
        command = [self.executable, '--print', '--verbose', '--output-format', 'stream-json',
                   '--model', self.model, '--tools', '', '--allowedTools', 'StructuredOutput',
                   '--json-schema', json.dumps(ENVELOPE_SCHEMA),
                   '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
                   '--safe-mode', '--setting-sources', '', '--settings',
                   '{"disableAllHooks":true,"forceLoginMethod":"claudeai"}',
                   '--no-session-persistence', '--disable-slash-commands', '--max-turns', '1',
                   '--effort', 'low', '--system-prompt', 'Respond only to the supplied text. No tools or external context.']
        self._save('attempt.json', {'model':self.model,'executable_sha256':fingerprint,'adapter_attempts':1})
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix='claude-text-') as directory:
            with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
                child = subprocess.Popen(command, cwd=directory, env=env, stdin=subprocess.PIPE,
                                         stdout=stdout, stderr=stderr, start_new_session=True)
                try:
                    child.communicate(request.prompt.encode(), timeout=self.timeout_seconds)
                except subprocess.TimeoutExpired:
                    raise TimeoutError('Claude timeout; remote outcome ambiguous; no retry') from None
                finally:
                    try: os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError: pass
                    child.wait()
                    for stream, filename in ((stdout,'stdout.jsonl'),(stderr,'stderr.log')):
                        stream.seek(0)
                        self._save(filename, stream.read(2_000_000))
                if child.returncode:
                    raise RuntimeError(f'Claude exited {child.returncode}; no retry')
                if os.fstat(stdout.fileno()).st_size > 2_000_000:
                    raise RuntimeError('response exceeds capture limit')
                stdout.seek(0)
                raw = stdout.read().decode('utf-8')
        if hashlib.sha256(Path(self.executable).read_bytes()).hexdigest() != fingerprint:
            raise RuntimeError('CLI changed during attempt')
        answer, usage = validate_structured_stream(raw, self.model)
        self.last_call_metadata = {'provider':self.name,'parser_version':'tau2-structured/v2','observed_assistant_messages':1,'format_validation_turns':1,'requested_model':self.model,'response_model':self.model,
                                  'billing_mode':'claude_subscription','estimated_cost_usd':None,'usage':usage,
                                  'executable_sha256':fingerprint,'latency_seconds':time.monotonic()-started,
                                  'confirmatory_eligible':False}
        self._save('metadata.json',self.last_call_metadata)
        return answer

