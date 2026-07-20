from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agents.live import LiveAgent, _build_prompt
from agents.mock_transport import MockTransport
from agents.stub import StubAgent
from eval.manifest import build_manifest
from eval.metrics import aggregate_metrics
from eval.runner import TASK_FAMILIES, VARIANTS, run_eval, run_eval_with_agent


def _resolve_api_key() -> str | None:
    return os.environ.get("AGENT_LIVE_API_KEY") or os.environ.get("OPENAI_API_KEY")


def _usage_message() -> str:
    return """\
Experiment runner requires live credentials or an offline flag.

Offline modes (no API keys):
  python -m eval.experiment --stub-as-live
  python -m eval.experiment --dry-run
  python -m eval.experiment --mock-live

Live experiment (requires openai + key):
  export AGENT_EXPERIMENT=1
  export OPENAI_API_KEY=...   # or AGENT_LIVE_API_KEY
  python -m eval.experiment [--replications N] [--also-last-run]
"""


def _make_run_id() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _filter_pairs(
    pairs: list[dict[str, Any]],
    intents: list[str] | None,
) -> list[dict[str, Any]]:
    if not intents:
        return pairs
    allowed = set(intents)
    return [pair for pair in pairs if pair["intent_id"] in allowed]


def _write_episodes_jsonl(
    episodes: list[dict[str, Any]],
    path: Path,
    *,
    replication_id: int = 0,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for episode in episodes:
        row = dict(episode)
        row["replication_id"] = replication_id
        lines.append(json.dumps(row, sort_keys=True))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_manifest(run_dir: Path, config: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    manifest = build_manifest(config, repo_root=repo_root)
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def _build_mock_responses(pairs: list[dict[str, Any]]) -> list[str]:
    weaken_agent = StubAgent(failure_mode="smell-blind")
    responses: list[str] = []
    for pair in pairs:
        for task_family in TASK_FAMILIES:
            for variant in VARIANTS:
                if variant == "clean":
                    artifact = copy.deepcopy(pair["oracle_spec"][task_family])
                else:
                    artifact = weaken_agent.generate(
                        pair,
                        variant="smelly",
                        task_family=task_family,
                    )
                responses.append(json.dumps(artifact))
    return responses


def run_dry_run(
    *,
    repo_root: Path,
    run_id: str | None = None,
    intents: list[str] | None = None,
    model: str = "gpt-4o-mini",
    policy: str = "direct",
    seed: int | None = None,
    replications: int = 1,
) -> dict[str, Any]:
    from pairs.loader import load_all_pairs

    if run_id is None:
        run_id = _make_run_id()

    pairs = _filter_pairs(load_all_pairs(), intents)
    run_dir = repo_root / "runs" / run_id
    prompts_dir = run_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    for pair in pairs:
        for task_family in TASK_FAMILIES:
            for variant in VARIANTS:
                prompt = _build_prompt(pair, variant, task_family)
                filename = f"{pair['intent_id']}_{task_family}_{variant}.txt"
                (prompts_dir / filename).write_text(prompt + "\n", encoding="utf-8")

    config = {
        "mode": "dry-run",
        "run_id": run_id,
        "model": model,
        "policy": policy,
        "seed": seed,
        "replications": replications,
        "intents": intents or [],
        "pair_count": len(pairs),
    }
    _write_manifest(run_dir, config, repo_root)

    return {"mode": "dry-run", "run_id": run_id, "run_dir": str(run_dir.relative_to(repo_root))}


def run_mock_live(
    *,
    repo_root: Path,
    run_id: str | None = None,
    intents: list[str] | None = None,
    model: str = "mock-live",
    policy: str = "direct",
    seed: int | None = None,
    replications: int = 1,
) -> dict[str, Any]:
    from pairs.loader import load_all_pairs

    if run_id is None:
        run_id = _make_run_id()

    pairs = _filter_pairs(load_all_pairs(), intents)
    run_dir = repo_root / "runs" / run_id
    traces_dir = run_dir / "traces"

    config = {
        "mode": "mock-live",
        "run_id": run_id,
        "model": model,
        "policy": policy,
        "seed": seed,
        "replications": replications,
        "intents": intents or [],
        "pair_count": len(pairs),
    }
    _write_manifest(run_dir, config, repo_root)

    responses = _build_mock_responses(pairs)
    transport = MockTransport(responses)
    agent = LiveAgent(transport=transport, model=model, provider="mock")

    metrics, episodes = run_eval_with_agent(
        agent,
        pairs=pairs,
        policy=policy,
        output_path=run_dir / "metrics.json",
        traces_dir=traces_dir,
        episodes_path=run_dir / "episodes.jsonl",
    )
    _write_episodes_jsonl(episodes, run_dir / "episodes.jsonl")

    return {
        "mode": "mock-live",
        "run_id": run_id,
        "run_dir": str(run_dir.relative_to(repo_root)),
        "metrics": metrics,
        "episode_count": len(episodes),
    }


def run_experiment(
    *,
    stub_as_live: bool = False,
    dry_run: bool = False,
    mock_live: bool = False,
    replications: int = 1,
    also_last_run: bool = False,
    repo_root: Path | None = None,
    intents: list[str] | None = None,
    model: str = "gpt-4o-mini",
    policy: str = "direct",
    seed: int | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]

    if dry_run:
        return run_dry_run(
            repo_root=repo_root,
            run_id=run_id,
            intents=intents,
            model=model,
            policy=policy,
            seed=seed,
            replications=replications,
        )

    if mock_live:
        return run_mock_live(
            repo_root=repo_root,
            run_id=run_id,
            intents=intents,
            model=model,
            policy=policy,
            seed=seed,
            replications=replications,
        )

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
            policy=policy,
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
            policy=policy,
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
        "--dry-run",
        action="store_true",
        help="Write prompts and manifest under runs/ without model calls",
    )
    parser.add_argument(
        "--mock-live",
        action="store_true",
        help="Run LiveAgent with MockTransport under runs/ (offline)",
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
    parser.add_argument("--model", default="gpt-4o-mini", help="Model identifier for manifest")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for manifest")
    parser.add_argument("--policy", default="direct", help="Mitigation policy")
    parser.add_argument(
        "--intents",
        nargs="*",
        default=None,
        help="Optional intent_id filter",
    )
    args = parser.parse_args(argv)

    if args.replications < 1:
        print("error: --replications must be >= 1", file=sys.stderr)
        sys.exit(2)

    offline_flags = sum([args.stub_as_live, args.dry_run, args.mock_live])
    if offline_flags > 1:
        print("error: choose at most one of --stub-as-live, --dry-run, --mock-live", file=sys.stderr)
        sys.exit(2)

    repo_root = Path.cwd()

    if args.dry_run or args.mock_live:
        run_experiment(
            dry_run=args.dry_run,
            mock_live=args.mock_live,
            replications=args.replications,
            intents=args.intents,
            model=args.model,
            policy=args.policy,
            seed=args.seed,
            repo_root=repo_root,
        )
        return

    if not args.stub_as_live:
        if os.environ.get("AGENT_EXPERIMENT") != "1" or not _resolve_api_key():
            print(_usage_message(), file=sys.stderr)
            sys.exit(0)

    run_experiment(
        stub_as_live=args.stub_as_live,
        replications=args.replications,
        also_last_run=args.also_last_run,
        intents=args.intents,
        model=args.model,
        policy=args.policy,
        seed=args.seed,
        repo_root=repo_root,
    )


if __name__ == "__main__":
    main()
