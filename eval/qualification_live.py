"""Sequential whole-context v4/v5 collection with receipt-derived phase gates."""
from __future__ import annotations

import json
import os
from pathlib import Path

from agents.providers import ProviderRequest
from eval import scoped_judge_study as historical
from eval.addressed_comparison import _Parser
from eval.addressed_comparison_live import _inspect as inspect_receipts
from eval.addressed_comparison_plan import ComparisonError, PHASES, read_bytes, read_json, safe_path
from eval.live_judge_controls import _provider
from eval.pilot_ledger import PilotLedger, PilotStop
from eval.provider_runtime_config import parse_provider_slot
from eval.qualification_audit import ARMS, audit
from eval.qualification_custody import create_run, custody_locks, load_run, verify_custody, write_new
from eval.qualification_plan import check_budget, prices_for
from label_plane.private_env import load_private_env
from label_plane.qualified_judge import build_prompt


def _cost_strata(plan, completed):
    rows = []
    for phase in PHASES:
        for index, slot in enumerate(plan['providers']):
            for arm in ARMS:
                calls = [c for c in plan['calls'] if c['phase'] == phase and c['slot'] == slot['id']
                         and c['id'].split(':')[1] == arm]
                receipts = [completed[c['id']] for c in calls if c['id'] in completed]
                rows.append({'phase': phase, 'provider_slot': f'provider_{index+1}', 'arm': arm,
                             'completed': len(receipts),
                             'spent_microusd': sum(r['actual_cost_microusd'] for r in receipts),
                             'usage': {k: sum(r['usage'][k] for r in receipts) for k in
                                       ('input_tokens', 'output_tokens', 'cached_tokens')},
                             'completed_latency_ms': round(sum(r['latency_ms'] for r in receipts), 3)})
    return rows


def _snapshot_report(directory):
    directory = safe_path(directory)
    # Frozen-runtime validation must run outside ancestor locks.
    manifest = load_run(directory)
    plan = manifest['plan']
    with custody_locks(plan), historical.parent_lock(directory):
        verify_custody(directory, manifest)
        ledger, completed, observations = inspect_receipts(directory, plan)
        budget = check_budget(plan, ledger['spent_microusd'], completed)
        scored = audit(plan, completed)  # Pure; no nested lock or external read.
        verify_custody(directory, manifest)
        current, _, _ = inspect_receipts(directory, plan)
        if current['ledger_head'] != ledger['ledger_head']:
            raise ComparisonError('journal_changed')
    ready = ledger['state'] == 'ready' and not ledger['pending_count']
    attempts = len(completed) + ledger['pending_count']
    result = {'schema_version': 'qualified-comparison-live-report/v1',
              'main_collection_released': False, 'semantic_validity': 'not_measured',
              'phases': {p: 'pass_auxiliary_only' if ready and scored['candidate_passed'][p] else 'pause'
                         for p in PHASES},
              'audit': scored, 'budget': budget,
              'accounting': {'state': ledger['state'], 'planned_calls': len(plan['calls']),
                  'reserved_attempts': attempts, 'observed_provider_outcomes': observations,
                  'reconciled_completions': len(completed), 'pending_attempts': ledger['pending_count'],
                  'unattempted_calls': len(plan['calls']) - attempts,
                  'spent_microusd': ledger['spent_microusd'],
                  'cost_basis': 'verified_usage_at_frozen_rates_not_invoice', 'invoice_reconciled': False,
                  'active_reserved_microusd': ledger['active_reserved_microusd'],
                  'cost_complete_for_reserved_attempts': not ledger['pending_count'],
                  'attempt_count_basis': 'reservations_may_include_a_pre_dispatch_crash'},
              'cost_strata': _cost_strata(plan, completed)}
    return manifest, ledger['ledger_head'], result


def report(directory):
    """Read-only aggregates; keep private identities and journal hashes out."""
    return _snapshot_report(directory)[2]


def run_phase(directory, phase, *, approval=False, provider_factory=None, environ=None, progress=None):
    if approval is not True:
        raise ComparisonError('approval_required')
    if phase not in PHASES:
        raise ComparisonError('invalid_phase')
    directory = safe_path(directory)
    manifest, head, prior = _snapshot_report(directory)
    if prior['accounting']['state'] != 'ready' or prior['accounting']['pending_attempts']:
        raise PilotStop('unresolved_comparison')
    if phase == 'evaluation' and prior['phases']['development'] != 'pass_auxiliary_only':
        raise ComparisonError('development_gate_failed')
    plan = manifest['plan']
    slots = {s['id']: parse_provider_slot(s) for s in plan['providers']}
    env = dict(os.environ if environ is None else environ)
    if provider_factory is None and any(not str(env.get(s.api_key_env, '')).strip() for s in slots.values()):
        raise ComparisonError('missing_credentials')
    with custody_locks(plan):
        verify_custody(directory, manifest)
        with PilotLedger(directory/'ledger.jsonl', plan['calls'], prices_for(plan), approval=True) as ledger:
            if ledger.head != head:
                raise ComparisonError('journal_changed')
            cases = {c['id']: c for c in plan['cases']}
            providers = {}
            for call in (c for c in plan['calls'] if c['phase'] == phase):
                if call['id'] in ledger.completed:
                    continue
                verify_custody(directory, manifest)
                check_budget(plan, ledger.spent, ledger.completed)
                case_id, arm, slot = call['id'].split(':', 2)
                if slot not in providers:
                    providers[slot] = (provider_factory or _provider)(slots[slot], env)
                request = ProviderRequest(build_prompt(cases[case_id]['item'], arm), {}, 'opaque', 'test_gen',
                                          call['output_bound'])
                ledger.complete(call['id'], providers[slot], request)
                if progress:
                    progress({'phase': phase, 'completed': len(ledger.completed), 'spent_microusd': ledger.spent})
    return report(directory)


def _save_report(directory):
    _, head, result = _snapshot_report(directory)
    path = safe_path(directory)/f'report-{head}.json'
    if path.exists():
        if read_json(path) != result:
            raise ComparisonError('saved_report_changed')
    else:
        write_new(path, result)
    return result


def main(argv=None):
    parser = _Parser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'development', 'evaluation', 'report'))
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--approved-plan', type=Path)
    parser.add_argument('--env-file', type=Path)
    parser.add_argument('--approve-live', action='store_true')
    args = None
    try:
        args = parser.parse_args(argv)
        if args.command != 'report' and not args.approve_live:
            raise ComparisonError('approval_required')
        if ((args.command == 'prepare') != (args.approved_plan is not None)
                or (args.command in ('prepare', 'report') and args.env_file is not None)):
            raise ComparisonError('invalid_arguments')
        if args.command == 'prepare':
            create_run(read_json(args.approved_plan), args.directory, approval=True)
            result = _save_report(args.directory)
        elif args.command == 'report':
            result = report(args.directory)
        else:
            env = dict(os.environ)
            if args.env_file is not None:
                read_bytes(args.env_file)
                load_private_env(args.env_file, environ=env)
            run_phase(args.directory, args.command, approval=True, environ=env,
                      progress=lambda row: print(json.dumps(row), flush=True))
            result = _save_report(args.directory)
        print(json.dumps(result, sort_keys=True))
        return 0 if args.command in ('prepare', 'report') or result['phases'][args.command] == 'pass_auxiliary_only' else 2
    except (PilotStop, KeyboardInterrupt):
        result = {'error': 'unresolved_comparison', 'main_collection_released': False}
        if args is not None:
            try:
                result['report'] = _save_report(args.directory)
            except Exception:
                result['report_unavailable'] = True
        print(json.dumps(result, sort_keys=True))
        return 2
    except Exception as exc:
        code = str(exc) if isinstance(exc, ComparisonError) else 'invalid_live_state'
        print(json.dumps({'error': code, 'main_collection_released': False}, sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
