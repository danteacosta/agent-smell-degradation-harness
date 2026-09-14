"""Small original-contract demonstration; separate from quarantined discovery.

Generate with ChatGPT-authenticated Codex locally; execute only in a Linux
container with no network, no capabilities, bounded resources and read-only FS.
These original illustrative policies are NOT source-corpus or H1/H2 evidence.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import subprocess

from agents.codex_cli import CodexCLIProvider
from agents.providers import ProviderRequest
from label_plane.behavior_pairs import analyze

IMAGE = 'python@sha256:3949e4271b0a3ff82afac7306764c313dcc8edeeb89c0376a3c2ac6007c66b1d'


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    with path.open('xb') as stream:
        stream.write(encoded(value))
    path.chmod(0o600)


def cases():
    scaffold = ("\nImplement exactly one pure Python function with the following interface: {interface}. "
                "No imports, I/O, annotations, classes or nested functions. "
                "Return only a JSON object with the single key source_code containing Python source. "
                "Do not use tools.\n")
    return [
        {'id': 'access', 'clean': 'Allow authorized users. Deny unauthorized users.',
         'defective': 'Allow authorized users.',
         'scaffold': scaffold.format(interface="evaluate(authorized), Boolean input; return 'allow' or 'deny'"),
         'tests': [{'kwargs': {'authorized': True}, 'expected': 'allow'},
                   {'kwargs': {'authorized': False}, 'expected': 'deny'}]},
        {'id': 'discount', 'clean': 'For a nonnegative purchase total, return a discount equal to 10% of the total. Cap the discount at 7.',
         'defective': 'For a nonnegative purchase total, return a discount equal to 10% of the total.',
         'scaffold': scaffold.format(interface='evaluate(total); return a number'),
         'tests': [{'args': [0], 'expected': 0}, {'args': [50], 'expected': 5},
                   {'args': [70], 'expected': 7}, {'args': [100], 'expected': 7}]},
        {'id': 'token', 'clean': 'A token is valid when its nonnegative age in minutes is strictly less than 15. A previously used token must be invalid.',
         'defective': 'A token is valid when its nonnegative age in minutes is strictly less than 15.',
         'scaffold': scaffold.format(interface='evaluate(age, used), used is Boolean; return Boolean validity'),
         'tests': [{'args': [0, False], 'expected': True}, {'args': [14, False], 'expected': True},
                   {'args': [15, False], 'expected': False}, {'args': [20, False], 'expected': False},
                   {'args': [0, True], 'expected': False}, {'args': [14, True], 'expected': False}]},
    ]


def prepare(output: Path, *, model: str, replications: int):
    if type(replications) is not int or not 1 <= replications <= 5:
        raise ValueError('replications must be an integer in 1..5')
    if not model.strip():
        raise ValueError('explicit model required')
    inventory = cases()
    schedule = [{'case': c['id'], 'replication': str(r), 'variant': v}
                for c in inventory for r in range(1, replications + 1) for v in ('clean', 'defective')]
    random.Random(20260914).shuffle(schedule)
    manifest = {'schema_version': 'codex-original-demo/v1', 'scope': 'original_contract_demonstration',
                'confirmatory_eligible': False, 'model': model, 'replications': replications,
                'created_at': datetime.now(timezone.utc).isoformat(), 'cases': inventory,
                'schedule': schedule, 'seed': 20260914, 'container_image': IMAGE,
                'container_platform': 'linux/arm64',
                'billing_mode': 'chatgpt_subscription', 'usd_cost': None,
                'limitations': ['Original constructed policies, not natural source requirements.',
                                'One requested model alias; snapshot is not exposed by CLI.',
                                'Repetitions are not independent intents or projects.',
                                'No T1–T3 observability measurement or H1/H2 inference.'],
                'code_hashes': {str(p.relative_to(Path(__file__).resolve().parents[1])): sha(p.read_bytes())
                               for p in (Path(__file__).resolve(), Path(__file__).with_name('codegen_sandbox.py'),
                                         Path(__file__).resolve().parents[1] / 'agents/codex_cli.py')}}
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    write(output / 'manifest.json', manifest)
    return manifest


def container_command():
    root = Path(__file__).resolve().parent
    return ['docker', 'run', '--rm', '-i', '--platform', 'linux/arm64', '--network', 'none',
            '--read-only', '--user', '65534:65534', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--memory', '512m', '--cpus', '1',
            '--pids-limit', '64', '--tmpfs', '/tmp:rw,noexec,nosuid,size=64m',
            '-v', f'{root / "codegen_sandbox.py"}:/app/eval/codegen_sandbox.py:ro',
            '-v', f'{root / "behavior_runtime_smoke.py"}:/app/eval/behavior_runtime_smoke.py:ro',
            '-w', '/app', IMAGE, 'python']


def execute(source, tests):
    command = container_command() + ['-c',
        'import json,sys; from eval.codegen_sandbox import evaluate; '
        'v=json.load(sys.stdin); print(json.dumps(evaluate(v["source"], v["tests"])))']
    result = subprocess.run(command, input=json.dumps({'source': source, 'tests': tests}),
                            capture_output=True, text=True, timeout=30, check=True)
    return json.loads(result.stdout)


def run(output: Path, *, model: str, executable: str, replications: int):
    manifest = prepare(output, model=model, replications=replications)
    # Qualify BEFORE the first provider call; a failed smoke leaves a frozen
    # manifest and does not spend subscription quota on unexecutable artifacts.
    smoke = subprocess.run(container_command() + ['-m', 'eval.behavior_runtime_smoke'],
                           capture_output=True, text=True, timeout=30)
    try:
        smoke_report = json.loads(smoke.stdout)
    except ValueError:
        smoke_report = {'status': 'launch_failed', 'exit_code': smoke.returncode,
                        'diagnostic': smoke.stderr[:2000]}
    write(output / 'executor-smoke.json', smoke_report)
    if smoke.returncode or smoke_report.get('status') != 'smoke_passed':
        raise RuntimeError('Linux executor smoke failed; generation not started')
    provider = CodexCLIProvider(executable=executable, model=model)
    version = subprocess.run([executable, '--version'], capture_output=True, text=True, check=True)
    write(output / 'runtime.json', {'cli_version': version.stdout.strip(),
                                  'executable_sha256': sha(Path(executable).read_bytes())})
    configuration = sha(encoded(manifest))
    inventory = {c['id']: c for c in manifest['cases']}
    plan = [{'run_id': output.name, 'replication_id': str(r), 'project_id': 'original-demo',
             'intent_id': c['id'], 'constraint_id': 'policy-' + c['id'],
             'oracle_sha256': sha(encoded(c['tests'])), 'configuration_sha256': configuration}
            for c in manifest['cases'] for r in range(1, replications + 1)]
    write(output / 'plan.json', plan)
    outcomes = []
    for index, item in enumerate(manifest['schedule']):
        case, variant = inventory[item['case']], item['variant']
        pair = next(p for p in plan if p['intent_id'] == case['id'] and p['replication_id'] == item['replication'])
        directory = output / f'episode-{index + 1:03}'
        directory.mkdir(mode=0o700)
        prompt = case[variant] + case['scaffold']
        write(directory / 'request.json', {'prompt': prompt, 'sha256': sha(prompt.encode())})
        record = {**pair, 'variant': variant, 'status': 'not_executed', 'episode_path': directory.name}
        try:
            answer = provider.complete(ProviderRequest(prompt, {}, variant, 'behavior_codegen'))
            write(directory / 'response.json', {'text': answer, 'metadata': provider.last_call_metadata})
            response = json.loads(answer)
            if not isinstance(response, dict) or set(response) != {'source_code'} or not isinstance(response['source_code'], str):
                raise ValueError('expected only source_code')
            report = execute(response['source_code'], case['tests'])
            write(directory / 'execution.json', report)
            status = report['status']
            record['status'] = status if status in {'passed', 'failed', 'runtime_error', 'timeout', 'rejected', 'worker_error'} else 'not_executed'
            record['executor_status'] = status
        except (RuntimeError, ValueError, TimeoutError, subprocess.SubprocessError) as exc:
            # No opportunistic retry or repair. Errors stay in the denominator.
            write(directory / 'failure.json', {'type': type(exc).__name__, 'message': str(exc)[:500]})
        write(directory / 'outcome.json', record)
        outcomes.append(record)
        print(f'{index + 1}/{len(manifest["schedule"])} {case["id"]} {variant}: {record["status"]}', flush=True)
    report = analyze(plan, outcomes)
    write(output / 'outcomes.json', outcomes)
    write(output / 'analysis.json', report)
    write(output / 'receipt.json', {'scope': manifest['scope'], 'confirmatory_eligible': False,
                                  'files': {str(p.relative_to(output)): sha(p.read_bytes())
                                            for p in sorted(output.rglob('*.json'))}})
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--codex-bin', required=True)
    parser.add_argument('--replications', type=int, default=3)
    args = parser.parse_args()
    print(json.dumps(run(args.output, model=args.model, executable=args.codex_bin,
                         replications=args.replications), indent=2))
