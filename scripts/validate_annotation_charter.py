#!/usr/bin/env python3
"""Validate a private annotation-study charter without collecting labels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from label_plane.annotation_charter import (  # noqa: E402
    evaluate_annotation_charter,
    load_annotation_charter,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--charter", required=True, type=Path)
    parser.add_argument("--rubric", required=True, type=Path)
    parser.add_argument("--queue-manifest", type=Path)
    args = parser.parse_args()
    report = evaluate_annotation_charter(
        load_annotation_charter(args.charter),
        rubric_path=args.rubric,
        queue_manifest_path=args.queue_manifest,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
