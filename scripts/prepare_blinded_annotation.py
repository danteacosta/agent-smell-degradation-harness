"""Prepare private, blinded annotation tasks with a frozen duplicate subset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from label_plane.annotation_protocol import (  # noqa: E402
    freeze_blinded_tasks,
    load_annotation_rubric,
)


def _load_records(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".jsonl":
        values = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        payload = json.loads(text)
        values = payload if isinstance(payload, list) else payload.get("records", [])
    if not isinstance(values, list) or not all(isinstance(value, dict) for value in values):
        raise ValueError("annotation input must be a JSON array or JSONL objects")
    return values


def _assert_private(path: Path) -> None:
    try:
        path.resolve().relative_to(REPOSITORY_ROOT.resolve())
    except ValueError:
        return
    raise ValueError(
        "annotation tasks contain raw annotator-visible text and must stay outside "
        "the repository"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="private episode/artifact JSON or JSONL")
    parser.add_argument("--tasks", required=True, type=Path, help="private annotator task JSONL")
    parser.add_argument("--manifest", required=True, type=Path, help="private selection manifest")
    parser.add_argument("--rubric", type=Path)
    parser.add_argument("--fraction", type=float, default=0.20)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    for path in (args.input, args.tasks, args.manifest):
        if path != args.input:
            _assert_private(path)
    try:
        rubric = load_annotation_rubric(args.rubric)
        tasks, selection = freeze_blinded_tasks(
            _load_records(args.input),
            fraction=args.fraction,
            seed=args.seed,
            rubric_version=str(rubric["rubric_version"]),
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.exit(1, f"error: {error}\n")
    args.tasks.parent.mkdir(parents=True, exist_ok=True)
    args.tasks.write_text(
        "".join(
            json.dumps(task, ensure_ascii=False, sort_keys=True) + "\n"
            for task in tasks
        ),
        encoding="utf-8",
    )
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(selection, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "prepared",
                "item_count": selection["item_count"],
                "duplicate_item_count": selection["duplicate_item_count"],
                "selection_sha256": selection["selection_sha256"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
