from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .runner import load_bundle, load_fixture, run_bundle, to_sarif
from .schema import REPLAY_VERSION, ContractError, canonical_json_bytes, sha256_bytes


def _write(path: str | None, value: Any) -> None:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def _invalid_report(exc: Exception) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema_version": "constraint-replay/v1",
        "replay_version": REPLAY_VERSION,
        "decision": "invalid-contract",
        "exit_code": 30,
        "error": {"code": "invalid_contract", "message": str(exc)},
        "semantic_evidence": [],
    }
    report["report_sha256"] = sha256_bytes(canonical_json_bytes(report))
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay a pre-final constraint trace offline")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--fixture", help="checked-in fixture case ID")
    source.add_argument("--bundle", help="path to an arbitrary replay bundle")
    parser.add_argument("--json", help="JSON report path; defaults to stdout")
    parser.add_argument("--sarif", help="SARIF report path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.fixture:
            bundle = load_fixture(args.fixture, Path(__file__).parent / "fixtures")
        else:
            bundle = load_bundle(args.bundle)
        report = run_bundle(bundle)
    except (ContractError, OSError, ValueError) as exc:
        report = _invalid_report(exc)
    _write(args.json, report)
    if args.sarif:
        _write(args.sarif, to_sarif(report))
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
