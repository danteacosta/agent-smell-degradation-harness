from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from eval.runner import run_eval


def _resolve_api_key() -> str | None:
    return os.environ.get("AGENT_LIVE_API_KEY") or os.environ.get("OPENAI_API_KEY")


def _usage_message() -> str:
    return """\
Experiment runner requires live credentials or --stub-as-live.

Offline schema demo (no API keys):
  python -m eval.experiment --stub-as-live

Live experiment (requires openai + key):
  export AGENT_EXPERIMENT=1
  export OPENAI_API_KEY=...   # or AGENT_LIVE_API_KEY
  python -m eval.experiment [--replications N] [--also-last-run]
"""


def _write_episodes_jsonl(
    episodes: list[dict[str, Any]],
    path: Path,
    *,
    replication_id: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for episode in episodes:
        row = dict(episode)
        row["replication_id"] = replication_id
        lines.append(json.dumps(row, sort_keys=True))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_experiment(
    *,
    stub_as_live: bool = False,
    replications: int = 1,
    also_last_run: bool = False,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]

    eval_dir = repo_root / "eval"
    work_dir = eval_dir / ".experiment_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    runs: list[dict[str, Any]] = []
    combined_episodes: list[dict[str, Any]] = []

    for replication_id in range(replications):
        rep_dir = work_dir / f"rep_{replication_id}"
        metrics_path = rep_dir / "metrics.json"
        episodes_path = rep_dir / "episodes.jsonl"
        traces_dir = rep_dir / "traces"

        metrics, episodes = run_eval(
            output_path=metrics_path,
            traces_dir=traces_dir,
            episodes_path=episodes_path,
        )
        _write_episodes_jsonl(
            episodes,
            episodes_path,
            replication_id=replication_id,
        )

        enriched = []
        for episode in episodes:
            row = dict(episode)
            row["replication_id"] = replication_id
            enriched.append(row)
        combined_episodes.extend(enriched)

        runs.append(
            {
                "replication_id": replication_id,
                "metrics": metrics,
                "episodes_path": str(episodes_path.relative_to(repo_root)),
            }
        )

    experiment_episodes_path = eval_dir / "experiment_run_episodes.jsonl"
    experiment_episodes_path.parent.mkdir(parents=True, exist_ok=True)
    episode_lines = [json.dumps(ep, sort_keys=True) for ep in combined_episodes]
    experiment_episodes_path.write_text(
        "\n".join(episode_lines) + "\n",
        encoding="utf-8",
    )

    report: dict[str, Any] = {
        "mode": "stub-as-live" if stub_as_live else "live",
        "replications": replications,
        "runs": runs,
        "episodes_path": str(experiment_episodes_path.relative_to(repo_root)),
    }

    experiment_run_path = eval_dir / "experiment_run.json"
    experiment_run_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if also_last_run:
        run_eval(
            output_path=eval_dir / "last_run.json",
            traces_dir=eval_dir / "traces",
            episodes_path=eval_dir / "last_run_episodes.jsonl",
        )

    return report


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run experiment export path")
    parser.add_argument(
        "--stub-as-live",
        action="store_true",
        help="Run stub agent with experiment-shaped export (offline)",
    )
    parser.add_argument(
        "--replications",
        type=int,
        default=1,
        help="Number of replication runs (default: 1)",
    )
    parser.add_argument(
        "--also-last-run",
        action="store_true",
        help="Also write eval/last_run.json (overwrites gate artifact)",
    )
    args = parser.parse_args(argv)

    if args.replications < 1:
        print("error: --replications must be >= 1", file=sys.stderr)
        sys.exit(2)

    if not args.stub_as_live:
        if os.environ.get("AGENT_EXPERIMENT") != "1" or not _resolve_api_key():
            print(_usage_message(), file=sys.stderr)
            sys.exit(0)

    run_experiment(
        stub_as_live=args.stub_as_live,
        replications=args.replications,
        also_last_run=args.also_last_run,
    )


if __name__ == "__main__":
    main()
