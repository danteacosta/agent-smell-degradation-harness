"""Collect the frozen synthetic controls using the existing provider/cost gates.

The inherited ledger conservatively reserves the full pre-pilot envelope. Only
the 72 judge calls in this manifest are issued; no generation calls or retries.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from agents.providers import ProviderRequest
from eval.exploratory_cost import CostLedger, CostLedgerError, budgeted_provider
from eval.provider_runtime_config import load_exploratory_runtime_config, build_provider_from_slot
from label_plane.exploratory_judge import build_judge_prompt, JUDGE_PROMPT_TEMPLATE
from label_plane.judge_controls import build_controls, fingerprint, score_controls
from label_plane.private_env import load_private_env

ROOT = Path(__file__).resolve().parents[1]


def _write(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())


def _append(path, value):
    with path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(value, sort_keys=True, allow_nan=False) + '\n')
        handle.flush()
        os.fsync(handle.fileno())


def _provider(slot, env):
    from openai import OpenAI
    # Disable hidden SDK retries: one planned occurrence is one API attempt.
    client = OpenAI(api_key=env[slot.api_key_env], base_url=slot.base_url,
                    max_retries=0, timeout=45)
    return build_provider_from_slot(slot, environ=env, client=client)[0]


def run_controls(config_path, output_dir, *, live=False, environ=None, provider_factory=None):
    config = load_exploratory_runtime_config(config_path)
    pack = build_controls()
    budget = config.cost_configuration()
    preflight = budget.preflight()
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    configurations = {}
    for slot in config.providers:
        record = {'provider': slot.public_metadata(), 'source_revision': revision,
                  'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'prompt_template': JUDGE_PROMPT_TEMPLATE,
                  'rubric_sha256': hashlib.sha256((ROOT/'tasks/acceptance_criteria_llm_judge_rubric.json').read_bytes()).hexdigest(),
                  'pack_sha256': pack['pack_sha256'], 'repetitions': 3,
                  'max_output_tokens': config.token_bounds['judge'].output_tokens,
                  'sdk_retries': 0, 'application_attempts': 1,
                  'identity_evidence': 'requested_model_and_response_model; not independently verified immutable vendor weights'}
        configurations[slot.id] = {'sha256': fingerprint(record), 'record': record}
    report = {'schema_version': 'live-judge-controls/v1', 'state': 'preflight_ready',
              'evidence_scope': 'synthetic_diagnostic', 'confirmatory_eligible': False,
              'planned_control_calls': 72, 'actual_calls': 0,
              'budget_scope': 'conservative_full_prepilot_envelope_for_72_call_subset',
              'budget': preflight.to_dict(), 'configurations': configurations,
              'source_revision': revision, 'pack_sha256': pack['pack_sha256']}
    if not preflight.passed:
        report['state'] = 'preflight_blocked'
        return report
    if not live:
        return report
    output = Path(output_dir).resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError('live outputs must be outside the repository')
    output.mkdir(parents=True, exist_ok=False)
    output.chmod(0o700)
    _write(output/'manifest.json', report)
    ledger = CostLedger(output/'cost-ledger.jsonl', budget)
    rows = []
    env = dict(os.environ if environ is None else environ)
    factory = provider_factory or _provider
    try:
        adapters = {slot.id: budgeted_provider(factory(slot, env), ledger) for slot in config.providers}
        for rep in range(3):
            # Alternate provider order; do not change or select cases after outcomes.
            slots = config.providers if rep % 2 == 0 else tuple(reversed(config.providers))
            for case in pack['cases']:
                request = case['request']
                prompt = build_judge_prompt(request)
                for slot in slots:
                    raw = None
                    error = None
                    started = time.monotonic()
                    report['actual_calls'] += 1
                    try:
                        raw = adapters[slot.id].complete(
                            ProviderRequest(prompt, {'task_family': 'judge', 'output_keys': []},
                                            'opaque', 'judge', config.token_bounds['judge'].output_tokens),
                            call_id=f'control:{rep}:{request["occurrence_id"]}:{slot.id}',
                            phase='judge', attempt=1)
                    except Exception as exc:
                        error = type(exc).__name__
                        raise
                    finally:
                        row = {'pack_sha256': pack['pack_sha256'],
                               'configuration_sha256': configurations[slot.id]['sha256'],
                               'replication_id': rep, 'occurrence_id': request['occurrence_id'],
                               'raw_response': raw}
                        rows.append(row)
                        _append(output/'responses.jsonl', row)
                        _append(output/'calls.jsonl', {'configuration_sha256': row['configuration_sha256'],
                                'replication_id': rep, 'occurrence_id': request['occurrence_id'],
                                'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                                'latency_ms': round((time.monotonic()-started)*1000, 3), 'error_class': error})
        report['state'] = 'completed'
    except Exception as exc:
        report['state'] = ledger.status if ledger.status != 'ready' else 'stopped_provider_error'
        report['error_class'] = type(exc).__name__
    report['budget'] = ledger.report()
    report['scores'] = score_controls(rows, [c['sha256'] for c in configurations.values()], 3)
    _write(output/'report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT/'tasks/exploratory_llm_judged_prepilot.example.json')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--env-file', type=Path)
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    if args.env_file:
        load_private_env(args.env_file)
    result = run_controls(args.config, args.output_dir, live=args.live)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['state'] in {'preflight_ready', 'completed'} else 2


if __name__ == '__main__':
    raise SystemExit(main())
