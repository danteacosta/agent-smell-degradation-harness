"""Fail-closed text-only adapter for official Antigravity account authentication.

CLI 1.3.0 exposes tools even for tools: []; its live smoke is therefore NOT
qualified for research. This adapter refuses that stream, rather than hiding it.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

from agents.providers import ProviderRequest


AGENT = '''---
name: research-text
description: Text-only completion without external context.
mainAgent: true
subagent: false
tools: []
mcpServers: []
skills: []
plugins: []
commandExecutionPolicy: off
---
Return only the requested text. Do not use tools, memory, skills or subagents.
'''


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_stream(raw: str, model: str) -> tuple[str, dict]:
    """Accept a single successful, tool-free completion from the CLI-declared model."""
    try:
        events = [json.loads(line) for line in raw.splitlines() if line.strip()]
        initial = [e['init'] for e in events if e.get('event') == 'init']
        terminal = [e['result'] for e in events if e.get('event') == 'result']
        if len(initial) != 1 or len(terminal) != 1 or events[-1].get('event') != 'result':
            raise ValueError('incomplete stream')
        init, result = initial[0], terminal[0]
        if init.get('model') != model or init.get('agent') != 'research-text':
            raise ValueError('model or agent mismatch')
        if init.get('tools') != []:
            raise ValueError('CLI exposes tools; not qualified')
        for event in events:
            if event.get('event') not in {'init', 'step_update', 'result'}:
                raise ValueError('unknown event')
            step = event.get('step_update', {})
            if step.get('step_type') not in {None, 'user_input', 'agent_response', 'checkpoint'}:
                raise ValueError('non-text step')
            if step.get('tool_info') or step.get('subagent_info'):
                raise ValueError('external action')
        usage = result['usage']
        if any(type(usage.get(k)) is not int or usage[k] < 0 for k in ('input_tokens', 'output_tokens')):
            raise ValueError('invalid usage')
        answer = result['response']
        if result.get('status') != 'SUCCESS' or result.get('num_turns') != 1:
            raise ValueError('failed or multi-turn completion')
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError('empty response')
        return answer, usage
    except (KeyError, ValueError, TypeError, AttributeError, IndexError):
        raise RuntimeError('Antigravity stream refused: tools, model change, error or incomplete evidence') from None


class AntigravityCLIProvider:
    """One attempt, account-only authentication, no acceptance of tool capability."""

    name = 'antigravity_cli'

    def __init__(self, *, executable: str, model: str, timeout_seconds: float = 120,
                 qualification_path: Path | None = None, evidence_directory: Path | None = None):
        if not model.startswith('gemini-') or any(c.isspace() for c in model):
            raise ValueError('explicit Gemini model slug required')
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError('positive finite timeout required')
        self.executable = Path(executable).resolve(strict=True)
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.qualification_path = qualification_path
        self.evidence_directory = evidence_directory
        self.last_call_metadata = {}

    def complete(self, request: ProviderRequest) -> str:
        """Run exactly once; preserve an ambiguous timeout without retry."""
        self.last_call_metadata = {}
        if request.max_output_tokens is not None:
            raise ValueError('CLI cannot enforce a strict API output-token cap')
        if not isinstance(request.prompt, str) or not request.prompt.strip() or len(request.prompt.encode()) > 100_000:
            raise ValueError('bounded nonempty prompt required')
        settings_path = Path.home() / '.gemini/antigravity-cli/settings.json'
        if settings_path.exists():
            config = json.loads(settings_path.read_text())
            if config.get('modelProvider') is not None:
                raise RuntimeError('account authentication required; API configuration refused')
        env = {k: os.environ[k] for k in ('HOME', 'PATH', 'TMPDIR', 'LANG') if k in os.environ}
        executable_hash = _digest(self.executable)
        if self.qualification_path is None:
            raise RuntimeError('tool-free qualification required before sending any research prompt')
        qualification = json.loads(self.qualification_path.read_text())
        if qualification.get('executable_sha256') != executable_hash:
            raise RuntimeError('qualification does not match executable')
        validate_stream(qualification.get('stream', ''), self.model)
        evidence = self.evidence_directory
        if evidence is not None:
            evidence.mkdir(mode=0o700, exist_ok=False)
            self._save('attempt.json', json.dumps({'model': self.model, 'executable_sha256': executable_hash}).encode())
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix='antigravity-completion-') as directory:
            profile = Path(directory) / '.agents/agents/research-text.md'
            profile.parent.mkdir(parents=True)
            profile.write_text(AGENT)
            command = [str(self.executable), '--model', self.model, '--agent', 'research-text',
                       '--disable-slash-commands', '--output-format', 'stream-json',
                       '--print-timeout', f'{self.timeout_seconds}s', '--print']
            with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
                child = subprocess.Popen(command, cwd=directory, env=env, stdin=subprocess.PIPE,
                                         stdout=stdout, stderr=stderr, start_new_session=True)
                try:
                    child.communicate(request.prompt.encode(), timeout=self.timeout_seconds)
                except subprocess.TimeoutExpired:
                    raise TimeoutError('Antigravity timeout; remote outcome ambiguous, no retry') from None
                finally:
                    try:
                        os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    child.wait()
                    stdout.seek(0)
                    stderr.seek(0)
                    raw = stdout.read(2_000_001)
                    diagnostic = stderr.read(2_000_001)
                    self._save('stdout.jsonl', raw[:2_000_000])
                    self._save('stderr.log', diagnostic[:2_000_000])
                if child.returncode or len(raw) > 2_000_000 or len(diagnostic) > 2_000_000:
                    raise RuntimeError('Antigravity failed or capture truncated; no retry')
        if _digest(self.executable) != executable_hash:
            raise RuntimeError('CLI executable changed during attempt')
        answer, usage = validate_stream(raw.decode('utf-8'), self.model)
        self.last_call_metadata = {'provider': self.name, 'requested_model': self.model,
                                  'response_model': None, 'cli_declared_model': self.model, 'model_snapshot_status': 'not_exposed_by_cli',
                                  'billing_mode': 'google_account_quota_or_credits_unverified',
                                  'estimated_cost_usd': None, 'usage': usage,
                                  'latency_seconds': time.monotonic() - started,
                                  'executable_sha256': executable_hash, 'confirmatory_eligible': False}
        self._save('metadata.json', json.dumps(self.last_call_metadata).encode())
        return answer

    def _save(self, filename: str, data: bytes) -> None:
        if self.evidence_directory is not None:
            descriptor = os.open(self.evidence_directory / filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(data)
