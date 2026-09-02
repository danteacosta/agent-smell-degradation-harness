"""Run the redacted real-provider/runtime-native qualification smoke."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from eval.native_provider_smoke import (  # noqa: E402
    NativeSmokeConfigurationError,
    run_native_provider_smoke,
)
from label_plane.private_env import load_private_env  # noqa: E402


def _assert_private_output(path: Path) -> None:
    try:
        path.resolve().relative_to(REPOSITORY_ROOT.resolve())
    except ValueError:
        return
    raise ValueError(
        "native smoke output must stay outside the repository; use /private/tmp "
        "or another private directory"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--intents",
        nargs="+",
        help="specific checked-in intent IDs; otherwise use --limit",
    )
    parser.add_argument("--limit", type=int, default=1)
    args = parser.parse_args()
    _assert_private_output(args.output)
    try:
        load_private_env(REPOSITORY_ROOT / ".env")
        report = run_native_provider_smoke(
            args.config,
            args.output,
            intent_ids=args.intents,
            limit=None if args.intents else args.limit,
            repository_root=REPOSITORY_ROOT,
        )
    except (NativeSmokeConfigurationError, OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
