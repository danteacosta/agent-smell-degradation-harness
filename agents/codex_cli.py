"""Local subscription completions through the official Codex CLI.

This separate adapter is exploratory, not a qualified API runtime. It cannot
enforce API output-token caps, and never supplies fabricated USD prices.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

from agents.providers import ProviderRequest


class CodexCLIProvider:
    name = 'codex_cli'

    def __init__(self, *, executable: str, model: str, timeout_seconds: float = 120,
                 evidence_directory: Path | str | None = None):
        if not model.strip() or model.startswith('-'):
            raise ValueError('explicit model required')
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError('positive finite timeout required')
        self.executable = str(Path(executable).resolve(strict=True))
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.last_call_metadata = {}
        self.evidence_directory = Path(evidence_directory) if evidence_directory is not None else None

    @staticmethod
    def _environment():
        # Only OS/auth-location variables; never forward provider keys, proxy
        # credentials, repository settings, or caller-supplied API endpoints.
        return {k: os.environ[k] for k in ('HOME', 'PATH', 'TMPDIR', 'LANG', 'CODEX_HOME') if k in os.environ}

    def _capture_evidence(self, stdout, stderr, returncode: int) -> None:
        if self.evidence_directory is None:
            return
        metadata = {'returncode': returncode, 'capture_limit_bytes': 2_000_000}
        for name, stream, filename in (
                ('stdout', stdout, 'stdout.jsonl'), ('stderr', stderr, 'stderr.log')):
            size = os.fstat(stream.fileno()).st_size
            position = stream.tell()
            stream.seek(0)
            data = stream.read(2_000_000)
            stream.seek(position)
            self._write_private_evidence(filename, data)
            metadata[name] = {'total_bytes': size, 'captured_bytes': len(data),
                              'truncated': size > len(data)}
        self._write_private_evidence('capture.json',
                                     (json.dumps(metadata, sort_keys=True) + '\n').encode())

    def _write_private_evidence(self, filename: str, data: bytes) -> None:
        descriptor = os.open(self.evidence_directory / filename,
                             os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)

    def complete(self, request: ProviderRequest) -> str:
        self.last_call_metadata = {}
        if request.max_output_tokens is not None:
            raise ValueError('Codex CLI does not support the strict API output-token cap')
        if not isinstance(request.prompt, str) or not request.prompt.strip() or len(request.prompt.encode()) > 100_000:
            raise ValueError('bounded nonempty prompt required')
        env = self._environment()
        auth = subprocess.run([self.executable, 'login', 'status'], env=env,
                              capture_output=True, text=True, timeout=15)
        if auth.returncode or 'Logged in using ChatGPT' not in auth.stdout + auth.stderr:
            raise RuntimeError('Codex requires saved ChatGPT authentication; no API fallback')
        command = [self.executable, 'exec', '--ignore-user-config', '--ephemeral',
                   '--skip-git-repo-check', '--sandbox', 'read-only', '--json',
                   '--color', 'never', '--model', self.model]
        settings = {
            'forced_login_method': 'chatgpt', 'approval_policy': 'never',
            'project_doc_max_bytes': 0, 'web_search': 'disabled',
            'hide_agent_reasoning': True, 'model_reasoning_effort': 'low',
            'features.shell_tool': False, 'features.unified_exec': False,
            'features.apps': False, 'features.browser_use': False,
            'features.computer_use': False, 'features.hooks': False,
            'features.remote_plugin': False, 'features.skill_search': False,
            'features.skip_host_skill_discovery': True,
            'suppress_unstable_features_warning': True,
            'features.multi_agent': False, 'features.view_image': False,
            'features.unbounded_connection_retries': False,
            'mcp_servers': {},
        }
        for key, value in settings.items():
            command += ['-c', key + '=' + json.dumps(value)]
        command.append('-')
        # A fresh private directory prevents overwriting a prior attempt.
        # Authentication diagnostics and environment variables are never captured.
        if self.evidence_directory is not None:
            self.evidence_directory.mkdir(mode=0o700, exist_ok=False)
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix='codex-completion-') as directory:
            # Anonymous files avoid unbounded in-memory capture and leave no
            # rollout or prompt in the repository. No oracle files enter cwd.
            with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
                child = subprocess.Popen(command, cwd=directory, env=env,
                                         stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                                         start_new_session=True)
                try:
                    child.communicate(request.prompt.encode(), timeout=self.timeout_seconds)
                except subprocess.TimeoutExpired:
                    raise TimeoutError('Codex completion timed out; remote outcome may be ambiguous') from None
                finally:
                    # The CLI has its own process group. Cancellation must not
                    # leave it (or descendants) consuming quota in the background.
                    try:
                        os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    child.wait()
                    self._capture_evidence(stdout, stderr, child.returncode)
                if child.returncode:
                    raise RuntimeError(f'Codex exited {child.returncode}; no automatic retry')
                if stdout.tell() > 2_000_000:
                    raise RuntimeError('Codex response exceeds capture limit')
                stdout.seek(0)
                raw = stdout.read().decode('utf-8')
        answer, usage, completed = None, None, 0
        try:
            for line in raw.splitlines():
                event = json.loads(line)
                kind = event.get('type')
                if kind in {'turn.failed', 'error'}:
                    raise RuntimeError('Codex reported failed or ambiguous completion')
                if kind in {'item.started', 'item.completed', 'item.updated'}:
                    item = event.get('item', {})
                    if item.get('type') not in {'agent_message', 'reasoning'}:
                        raise RuntimeError('Non-message item is not admissible: ' + str(item.get('type')))
                    if kind == 'item.completed' and item.get('type') == 'agent_message':
                        answer = item.get('text')
                if kind == 'turn.completed':
                    completed += 1
                    usage = event.get('usage')
        except (ValueError, TypeError, AttributeError):
            raise RuntimeError('Invalid Codex event stream') from None
        if completed != 1 or not isinstance(answer, str) or not answer.strip() or not isinstance(usage, dict):
            raise RuntimeError('Incomplete Codex answer or missing usage')
        if any(type(usage.get(k)) is not int or usage[k] < 0 for k in ('input_tokens', 'output_tokens')):
            raise RuntimeError('Invalid Codex usage')
        self.last_call_metadata = {
            'provider': self.name, 'requested_model': self.model,
            'response_model': None, 'model_snapshot_status': 'not_exposed_by_cli',
            'billing_mode': 'chatgpt_subscription', 'estimated_cost_usd': None,
            'usage': usage, 'latency_seconds': time.monotonic() - started,
            'confirmatory_eligible': False,
        }
        return answer
