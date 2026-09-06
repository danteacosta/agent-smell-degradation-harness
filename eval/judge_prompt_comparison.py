"""Run one frozen auxiliary comparison; never launch the natural-corpus pre-pilot."""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import time

from agents.providers import ProviderRequest
from eval.exploratory_cost import CostLedger, TokenBounds, budgeted_provider
from eval.live_judge_controls import ROOT, _append, _provider, _write, prepare_private_output
from eval.provider_runtime_config import load_exploratory_runtime_config
from label_plane.exploratory_judge import JUDGE_PROMPT_TEMPLATE
from label_plane.judge_controls import fingerprint
from label_plane.judge_prompt_comparison import (
    ARMS, EVIDENCE_PROMPT, EVIDENCE_PROMPT_V2, build_comparison_pack,
    build_schema_smoke_pack, comparison_prompt, score_comparison,
)
from label_plane.private_env import load_private_env

REPETITIONS = 2
ORDER_SEED = 20260906
OUTPUT_TOKENS = 96


def run_comparison(config_path, output_dir, *, live=False, environ=None,
                   provider_factory=None, progress=None, study='comparison_v1'):
    if study not in {'comparison_v1', 'schema_smoke_v2'}:
        raise ValueError('unknown study')
    original = load_exploratory_runtime_config(config_path)
    # This config is auxiliary and cannot generate any episodes. The fixed ledger
    # still over-reserves unused slots; the primary pre-pilot config is untouched.
    bounds = {phase: TokenBounds(1, 1) for phase in original.token_bounds}
    bounds['judge'] = TokenBounds(512, OUTPUT_TOKENS)
    config = replace(original, token_bounds=bounds)
    budget = config.cost_configuration()
    preflight = budget.preflight()
    pack = build_comparison_pack() if study == 'comparison_v1' else build_schema_smoke_pack()
    arms = ARMS if study == 'comparison_v1' else ('evidence_v2',)
    templates = {'historical': JUDGE_PROMPT_TEMPLATE, 'evidence': EVIDENCE_PROMPT,
                 'evidence_v2': EVIDENCE_PROMPT_V2}
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    files = ['eval/judge_prompt_comparison.py', 'eval/live_judge_controls.py',
             'eval/exploratory_cost.py', 'eval/provider_runtime_config.py', 'agents/providers.py',
             'label_plane/judge_prompt_comparison.py', 'label_plane/judge_controls.py',
             'label_plane/exploratory_judge.py', 'tasks/acceptance_criteria_llm_judge_rubric.json']
    source_hashes = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
    configurations, metadata, prompts, order = {}, {}, {}, []
    for slot in config.providers:
        for arm in arms:
            record = {'provider': slot.public_metadata(), 'arm': arm, 'source_revision': revision,
                      'source_hashes': source_hashes, 'pack_sha256': pack['pack_sha256'],
                      'prompt_template': templates[arm], 'study': study,
                      'max_output_tokens': OUTPUT_TOKENS, 'repetitions': REPETITIONS,
                      'order_seed': ORDER_SEED, 'sdk_retries': 0, 'application_attempts': 1,
                      'budget_configuration_sha256': budget.configuration_sha256,
                      'identity_evidence': 'configured_and_returned_model; vendor_weights_not_verified'}
            digest = fingerprint(record)
            configurations[digest] = record
            metadata[digest] = {'arm': arm, 'provider': slot.id}
            for case in pack['cases']:
                identifier = case['request']['occurrence_id']
                prompts[(digest, identifier)] = comparison_prompt(case['request'], arm)
                for rep in range(REPETITIONS):
                    order.append({'configuration_sha256': digest, 'occurrence_id': identifier,
                                  'replication_id': rep})
    random.Random(ORDER_SEED).shuffle(order)
    slots = {s.id: s for s in config.providers}
    direct = 0
    for item in order:
        digest, identifier = item['configuration_sha256'], item['occurrence_id']
        prompt = prompts[digest, identifier]
        slot = slots[metadata[digest]['provider']]
        byte_bound = len(prompt.encode('utf-8')) + 64
        direct += slot.pricing.reservation_microusd(TokenBounds(byte_bound, OUTPUT_TOKENS))
    direct_envelope = (direct * 125 + 99)//100
    report = {'schema_version': 'live-judge-prompt-comparison/v1', 'state': 'preflight_ready',
              'confirmatory_eligible': False, 'study': study, 'planned_calls': len(order), 'actual_calls': 0,
              'direct_experiment_envelope_microusd': direct_envelope,
              'envelope_assumption': 'UTF8 bytes plus 64 framing tokens, 96 output, 25% contingency; not vendor tokenizer certification',
              'budget_scope': 'auxiliary_judge_only_subset; unused_generation_slots_never_dispatched',
              'budget': preflight.to_dict(), 'configurations': configurations,
              'pack_sha256': pack['pack_sha256'], 'source_revision': revision,
              'order': order, 'order_sha256': fingerprint(order)}
    if not preflight.passed or direct_envelope > budget.approved_cap_microusd:
        report['state'] = 'preflight_blocked'
    if not live or report['state'] != 'preflight_ready':
        return report
    output = prepare_private_output(output_dir)
    _write(output/'manifest.json', report)
    _write(output/'control-pack.json', pack)
    ledger = CostLedger(output/'cost-ledger.jsonl', budget)
    rows = []
    env = dict(os.environ if environ is None else environ)
    factory = provider_factory or _provider
    try:
        adapters = {s.id: budgeted_provider(factory(s, env), ledger) for s in config.providers}
        for index, item in enumerate(order):
            digest, identifier = item['configuration_sha256'], item['occurrence_id']
            prompt = prompts[digest, identifier]
            raw, error = None, None
            started = time.monotonic()
            try:
                raw = adapters[metadata[digest]['provider']].complete(
                    ProviderRequest(prompt, {'task_family': 'judge', 'output_keys': []},
                                    'opaque', 'judge', OUTPUT_TOKENS),
                    call_id=f'comparison:{index}', phase='judge', attempt=1)
            except Exception as exc:
                error = type(exc).__name__
                raise
            finally:
                row = {**item, 'pack_sha256': pack['pack_sha256'], 'raw_response': raw}
                rows.append(row)
                _append(output/'responses.jsonl', row)
                _append(output/'calls.jsonl', {**item,
                        'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                        'latency_ms': round((time.monotonic()-started)*1000, 3), 'error_class': error})
            if progress and (index+1) % 12 == 0:
                progress({'completed_calls': index+1, 'planned_calls': len(order)})
        report['state'] = 'completed'
    except Exception as exc:
        report['state'] = ledger.status if ledger.status.startswith('stopped_') else 'stopped_provider_error'
        report['error_class'] = type(exc).__name__
    report['budget'] = ledger.report()
    report['actual_calls'] = report['budget']['observed_attempt_count']
    report['scores'] = score_comparison(rows, metadata, REPETITIONS, study=study)
    _write(output/'report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT/'tasks/exploratory_llm_judged_prepilot.example.json')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--env-file', type=Path)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--study', choices=('comparison_v1', 'schema_smoke_v2'), default='comparison_v1')
    args = parser.parse_args()
    if args.env_file:
        load_private_env(args.env_file)
    result = run_comparison(args.config, args.output_dir, live=args.live, study=args.study,
                            progress=lambda value: print(json.dumps(value), flush=True))
    print(json.dumps({k: result[k] for k in ('state', 'planned_calls', 'actual_calls',
                                            'direct_experiment_envelope_microusd', 'budget')}, indent=2))
    return 0 if result['state'] in {'completed', 'preflight_ready'} else 2


if __name__ == '__main__':
    raise SystemExit(main())
