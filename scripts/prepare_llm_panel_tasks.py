"""Expand a private candidate pool into blinded, configured-judge tasks."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from label_plane.llm_panel import PANEL_PROVIDERS, build_panel_tasks


def _assert_private_output(path: Path) -> None:
    try:
        path.resolve().relative_to(REPOSITORY_ROOT.resolve())
    except ValueError:
        return
    raise ValueError(
        f"raw panel tasks must stay outside the repository: {path}; use /private/tmp or another private directory"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument(
        "--judge-ids",
        nargs="+",
        default=list(PANEL_PROVIDERS),
        help="arbitrary judge slot IDs; defaults preserve the historical v1 task file",
    )
    args = parser.parse_args()
    _assert_private_output(args.output)
    candidates = [
        json.loads(line)
        for line in args.candidates.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    tasks = build_panel_tasks(candidates, judge_ids=args.judge_ids)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rendered = "".join(json.dumps(task, ensure_ascii=False, sort_keys=True) + "\n" for task in tasks)
    args.output.write_text(rendered, encoding="utf-8")
    summary = {"candidate_count": len(candidates), "task_count": len(tasks), "output": str(args.output)}
    if args.manifest:
        digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        manifest = {
            "schema_version": "requirements-smell-panel-task-manifest/v1",
            "status": "panel_tasks_ready_pending_provider_responses",
            "panel_version": tasks[0]["panel_version"] if tasks else None,
            "judges": sorted({str(task["provider_id"]) for task in tasks}),
            "candidate_count": len(candidates),
            "task_count": len(tasks),
            "tasks_per_judge": dict(sorted(Counter(str(task["provider_id"]) for task in tasks).items())),
            "task_file_sha256": digest,
            "private_task_file": str(args.output),
            "raw_prompts_in_repository": False,
        }
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        summary["manifest"] = str(args.manifest)
        summary["task_file_sha256"] = digest
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
