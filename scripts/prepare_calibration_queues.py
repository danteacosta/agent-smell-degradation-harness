"""Freeze disjoint probability-audit and diagnostic-review annotation queues."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from label_plane.calibration_queues import freeze_calibration_queues  # noqa: E402


def _load_rows(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".jsonl":
        value = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        payload = json.loads(text)
        value = payload if isinstance(payload, list) else payload.get("records", [])
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise ValueError("input must contain a JSON array or JSONL objects")
    return value


def _assert_private(path: Path) -> None:
    try:
        path.resolve().relative_to(REPOSITORY_ROOT.resolve())
    except ValueError:
        return
    raise ValueError("annotation queue inputs and outputs must stay outside the repository")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", required=True, type=Path, help="private blinded task JSON/JSONL")
    parser.add_argument("--signals", required=True, type=Path, help="private review-signal JSON/JSONL")
    parser.add_argument("--calibration-tasks", required=True, type=Path)
    parser.add_argument("--triage-tasks", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--calibration-count", required=True, type=int)
    parser.add_argument("--triage-count", required=True, type=int)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--source-selection-sha256", required=True)
    args = parser.parse_args()
    for path in (
        args.tasks,
        args.signals,
        args.calibration_tasks,
        args.triage_tasks,
        args.manifest,
    ):
        _assert_private(path)
    try:
        calibration, triage, manifest = freeze_calibration_queues(
            _load_rows(args.tasks),
            _load_rows(args.signals),
            calibration_count=args.calibration_count,
            triage_count=args.triage_count,
            seed=args.seed,
            source_selection_sha256=args.source_selection_sha256,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.exit(1, f"error: {error}\n")
    _write_jsonl(args.calibration_tasks, calibration)
    _write_jsonl(args.triage_tasks, triage)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "prepared",
                "population_count": manifest["population_count"],
                "calibration_count": manifest["calibration_count"],
                "triage_count": manifest["triage_count"],
                "selection_sha256": manifest["selection_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
