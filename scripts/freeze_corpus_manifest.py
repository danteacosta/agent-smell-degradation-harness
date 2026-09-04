"""Freeze a validated redacted corpus candidate at the canonical repository path."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from eval.corpus_intake import CorpusIntakeError, freeze_validated_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--frozen-at", required=True)
    parser.add_argument("--freeze-reviewer-id", required=True)
    args = parser.parse_args()
    try:
        candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
        frozen = freeze_validated_manifest(
            candidate,
            frozen_at=args.frozen_at,
            freeze_reviewer_id=args.freeze_reviewer_id,
        )
    except (OSError, json.JSONDecodeError, CorpusIntakeError, TypeError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")

    output = REPOSITORY_ROOT / "data/prepilot/corpus-manifest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(frozen, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = temporary.name
            temporary.write(serialized)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, output)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass
    print(json.dumps({
        "status": frozen["status"],
        "record_count": frozen["record_count"],
        "project_count": frozen["project_count"],
        "manifest_sha256": frozen["manifest_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
