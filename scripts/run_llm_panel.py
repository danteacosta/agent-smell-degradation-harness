"""Run private blinded panel tasks against configured model adapters.

The default mode is a ten-task-per-judge smoke run.  A full run requires both
``--full-run`` and ``--confirm-full-run`` with a ``full_panel`` config so an
accidental invocation cannot spend the whole panel budget. Use ``--resume``
to continue an interrupted run without repeating successful calls.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from label_plane.panel_runtime import (
    PanelAdapterError,
    PanelConfigurationError,
    PanelRunConfig,
    PanelRunner,
    load_panel_tasks,
)


def _assert_private_output(path: Path, repository_root: Path) -> None:
    resolved = path.resolve()
    try:
        resolved.relative_to(repository_root.resolve())
    except ValueError:
        return
    raise ValueError(
        f"raw panel output must stay outside the repository: {path}; use /private/tmp or another private directory"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", required=True, type=Path, help="private blinded task JSONL")
    parser.add_argument("--config", required=True, type=Path, help="private or tracked secret-free runtime JSON")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--responses", required=True, type=Path, help="private normalized response JSONL")
    parser.add_argument("--errors", required=True, type=Path, help="private error JSONL")
    parser.add_argument("--manifest", required=True, type=Path, help="hash/count-only manifest")
    parser.add_argument("--limit-per-judge", type=int, default=10)
    parser.add_argument("--full-run", action="store_true")
    parser.add_argument("--confirm-full-run", action="store_true")
    parser.add_argument("--resume", action="store_true", help="resume an existing run without repeating successful tasks")
    args = parser.parse_args()

    if args.full_run and not args.confirm_full_run:
        parser.error("--full-run requires --confirm-full-run")
    if args.confirm_full_run and not args.full_run:
        parser.error("--confirm-full-run is valid only with --full-run")
    limit = None if args.full_run else args.limit_per_judge
    repository_root = REPOSITORY_ROOT
    _assert_private_output(args.tasks, repository_root)
    _assert_private_output(args.responses, repository_root)
    _assert_private_output(args.errors, repository_root)
    try:
        config = PanelRunConfig.from_json(args.config)
        if args.full_run and config.stage != "full_panel":
            parser.error("--full-run requires a config with stage=full_panel")
        manifest = PanelRunner(config).run(
            load_panel_tasks(args.tasks),
            run_id=args.run_id,
            limit_per_judge=limit,
            responses_path=args.responses,
            errors_path=args.errors,
            manifest_path=args.manifest,
            resume=args.resume,
        )
    except (PanelConfigurationError, PanelAdapterError, OSError, ValueError) as exc:
        parser.exit(1, f"error: {exc}\n")
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
