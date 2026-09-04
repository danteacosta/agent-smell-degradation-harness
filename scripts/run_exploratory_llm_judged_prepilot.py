"""Run or preflight the private exploratory LLM-judged pre-pilot."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from eval.exploratory_prepilot import run_exploratory_prepilot  # noqa: E402
from label_plane.private_env import load_private_env  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--env-file", type=Path, default=REPOSITORY_ROOT / ".env")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--private-corpus", required=True, type=Path)
    parser.add_argument("--reference-constraints", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--confirm-live",
        action="store_true",
        help="explicitly authorize provider calls under the frozen cap",
    )
    parser.add_argument("--resume-run", type=Path)
    args = parser.parse_args()
    environment = dict(os.environ)
    try:
        load_private_env(args.env_file, environ=environment)
        report = run_exploratory_prepilot(
            args.config,
            args.output,
            private_corpus_path=args.private_corpus,
            reference_constraints_path=args.reference_constraints,
            repository_root=REPOSITORY_ROOT,
            environ=environment,
            dry_run=args.dry_run,
            confirm_live=args.confirm_live,
            resume_run=args.resume_run,
        )
    except (OSError, ValueError) as error:
        parser.exit(1, f"error: {type(error).__name__}: {error}\n")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["state"] in {"completed", "completed_with_uncertainty", "preflight_ready"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
