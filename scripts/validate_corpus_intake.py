"""Validate a private corpus file and export a redacted candidate manifest."""

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

from eval.corpus_intake import (
    CorpusIntakeError,
    build_redacted_manifest,
    load_private_records,
)


def _atomic_write(path: Path, contents: str) -> None:
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = temporary.name
            temporary.write(contents)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="private JSON or JSONL")
    parser.add_argument("--output", required=True, type=Path, help="redacted manifest")
    parser.add_argument("--expected-intents", type=int, default=12)
    parser.add_argument("--minimum-projects", type=int, default=6)
    args = parser.parse_args()
    try:
        manifest = build_redacted_manifest(
            load_private_records(args.input),
            expected_intents=args.expected_intents,
            minimum_projects=args.minimum_projects,
        )
    except (CorpusIntakeError, OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(
        args.output,
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "record_count": manifest["record_count"],
                "project_count": manifest["project_count"],
                "output": str(args.output),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
