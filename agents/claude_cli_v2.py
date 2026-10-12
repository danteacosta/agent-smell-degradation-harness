"""Versioned Claude subscription adapter accepting bounded thinking-token telemetry."""
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


def validate_stream(raw: str, model: str):
    """Validate one tool-free turn and its declared model before returning text."""
    try:
        events = [json.loads(line) for line in raw.splitlines() if line.strip()]
        init = [e for e in events if e.get('type') == 'system' and e.get('subtype') == 'init']
        results = [e for e in events if e.get('type') == 'result']
        if len(init) != 1 or len(results) != 1 or events[-1] != results[0]:
            raise ValueError('incomplete stream')
        if init[0].get('model') != model or init[0].get('tools') != [] or init[0].get('mcp_servers') != []:
            raise ValueError('model or capability mismatch')
        seen_models = []
        thinking_count = 0
        for event in events:
            if event.get('type') == 'assistant':
                message = event['message']
                seen_models.append(message['model'])
                if any(c.get('type') not in {'text', 'thinking'} for c in message['content']):
                    raise ValueError('non-text action')
            elif event.get('type') not in {'system', 'result', 'rate_limit_event'}:
                raise ValueError('unexpected event')
            elif event.get('type') == 'system' and event.get('subtype') == 'thinking_tokens':
                if not set(event) <= {'type','subtype','estimated_tokens','estimated_tokens_delta','session_id','uuid'}:
                    raise ValueError('unexpected telemetry payload')
                total, delta = event.get('estimated_tokens'), event.get('estimated_tokens_delta')
                if type(total) is not int or type(delta) is not int or not 0 <= total <= 10_000_000 or delta < 0 or total != thinking_count + delta:
                    raise ValueError('invalid thinking-token telemetry')
                thinking_count = total
            elif event.get('type') == 'system' and event.get('subtype') != 'init':
                raise ValueError('unexpected system activity')
        result = results[0]
        if not seen_models or any(m != model for m in seen_models) or set(result['modelUsage']) != {model}:
            raise ValueError('model switch')
        if result.get('subtype') != 'success' or result.get('is_error') is not False or result.get('num_turns') != 1:
            raise ValueError('unsuccessful turn')
        answer, usage = result['result'], result['usage']
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError('empty answer')
        if any(type(usage.get(k)) is not int or usage[k] < 0 for k in ('input_tokens', 'output_tokens')):
            raise ValueError('invalid usage')
        return answer, usage
    except (ValueError, TypeError, KeyError, AttributeError, IndexError) as exc:
        raise RuntimeError('Claude stream rejected: ' + str(exc)) from None


class ClaudeCLIProvider:
    """Use saved Pro/Max OAuth for a single isolated text completion."""
    name = 'claude_cli'

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
        env.update(CLAUDE_CODE_MAX_RETRIES='0', CLAUDE_CODE_NONSTREAMING_TIMEOUT_RETRIES='0',
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
        except ValueError:
            raise RuntimeError('Claude authentication status unavailable') from None
        if auth.returncode or status.get('loggedIn') is not True or status.get('authMethod') != 'claude.ai' or status.get('apiProvider') != 'firstParty' or status.get('subscriptionType') not in {'pro', 'max'}:
            raise RuntimeError('saved Claude Pro/Max subscription required; no API fallback')
        if self.evidence_directory is not None:
            self.evidence_directory.mkdir(mode=0o700, exist_ok=False)
        fingerprint = hashlib.sha256(Path(self.executable).read_bytes()).hexdigest()
        command = [self.executable, '--print', '--verbose', '--output-format', 'stream-json',
                   '--model', self.model, '--tools', '', '--disallowedTools', '*',
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
        answer, usage = validate_stream(raw, self.model)
        self.last_call_metadata = {'provider':self.name,'parser_version':'thinking-telemetry/v2','requested_model':self.model,'response_model':self.model,
                                  'billing_mode':'claude_subscription','estimated_cost_usd':None,'usage':usage,
                                  'executable_sha256':fingerprint,'latency_seconds':time.monotonic()-started,
                                  'confirmatory_eligible':False}
        self._save('metadata.json',self.last_call_metadata)
        return answer
