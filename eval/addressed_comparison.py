"""Offline comparison preparation/audit. No provider, credential or live option."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eval.addressed_comparison_audit import audit_comparison
from eval.addressed_comparison_plan import (
    AUTHORITY, ComparisonError, prepare_comparison, preparation_summary, read_json, safe_path,
)
from eval.live_judge_controls import _write, prepare_private_output
from eval.pilot_preparation import digest


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's default includes unrecognized argument values and paths.
        raise ComparisonError('invalid_arguments')


def _export(directory, report, plan=None):
    try:
        output = prepare_private_output(safe_path(directory))
        if plan is not None:
            _write(output / 'plan.json', plan)
            _write(output / 'plan-integrity.json', {'sha256': digest(plan)})
        _write(output / 'report.json', report)
    except (OSError, ValueError) as exc:
        # Partial files remain private for inspection; never remove or overwrite.
        raise ComparisonError('private_output_unavailable') from exc


def main(argv=None):
    parser = _Parser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True, parser_class=_Parser)
    prepare = commands.add_parser('prepare', help='Prepare a proposal; do not apply closure or dispatch')
    prepare.add_argument('--predecessor', type=Path, required=True)
    prepare.add_argument('--approve-offline', action='store_true')
    prepare.add_argument('--output-dir', type=Path)
    audit = commands.add_parser('audit', help='Audit supplied responses, not verified provider receipts')
    audit.add_argument('--plan', type=Path, required=True)
    audit.add_argument('--responses', type=Path, required=True)
    audit.add_argument('--output-dir', type=Path)
    try:
        args = parser.parse_args(argv)
        plan = None
        if args.command == 'prepare':
            plan = prepare_comparison(args.predecessor, approval=args.approve_offline)
            report = preparation_summary(plan)
            status = 0
        else:
            report = audit_comparison(read_json(args.plan), read_json(args.responses))
            status = 0 if all(v == 'met_offline_only' for v in report['candidate_response_rules'].values()) else 2
        if args.output_dir is not None:
            _export(args.output_dir, report, plan)
        print(json.dumps(report, indent=2, sort_keys=True))
        return status
    except ComparisonError as exc:
        print(json.dumps({'error': str(exc), **AUTHORITY}, sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
