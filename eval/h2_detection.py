from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from baselines.score import mann_whitney_auroc
from eval.runner import run_eval
from observability.features import extract_tier_a_features

FAMILIES = ("static_smell", "operational", "provenance_semantic")


def _episode_label(episode: dict[str, Any]) -> int:
    return 1 if episode.get("variant") == "smelly" and not episode.get("oracle_passed") else 0


def _family_score(family: str, features: dict[str, Any]) -> float:
    if family == "static_smell":
        return float(features["static_smell"]["smell_present"])
    if family == "operational":
        operational = features["operational"]
        return float(operational["event_count"]) + float(operational["latency_ms"]) / 1000.0
    if family == "provenance_semantic":
        semantic = features["provenance_semantic"]
        if semantic.get("is_weak_comparator"):
            return 1.0
        return float(1 - semantic.get("constraint_match", 0))
    return 0.0


def group_kfold_intent_ids(intent_ids: list[str], k: int) -> list[list[str]]:
    unique = sorted(set(intent_ids))
    if not unique:
        return []
    k = min(k, len(unique))
    folds: list[list[str]] = [[] for _ in range(k)]
    for index, intent_id in enumerate(unique):
        folds[index % k].append(intent_id)
    return folds


def evaluate_group_split(
    episodes: list[dict[str, Any]],
    *,
    k: int = 3,
) -> dict[str, Any]:
    by_intent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for episode in episodes:
        by_intent[episode["intent_id"]].append(episode)

    folds = group_kfold_intent_ids([episode["intent_id"] for episode in episodes], k=k)
    fold_reports: list[dict[str, Any]] = []

    for fold_index, test_intents in enumerate(folds):
        test_set = set(test_intents)
        test_eps = [ep for ep in episodes if ep["intent_id"] in test_set]
        if not test_eps:
            continue

        labels = [_episode_label(ep) for ep in test_eps]
        family_aurocs: dict[str, float] = {}
        for family in FAMILIES:
            scores = []
            for episode in test_eps:
                features = extract_tier_a_features(episode, episode["provenance_path"])
                scores.append(_family_score(family, features))
            family_aurocs[family] = mann_whitney_auroc(scores, labels)

        fold_reports.append(
            {
                "fold": fold_index,
                "test_intents": sorted(test_intents),
                "auroc": family_aurocs,
            }
        )

    aggregate: dict[str, list[float]] = {family: [] for family in FAMILIES}
    for report in fold_reports:
        for family in FAMILIES:
            aggregate[family].append(report["auroc"][family])

    summary = {
        family: sum(values) / len(values) if values else 0.5
        for family, values in aggregate.items()
    }

    return {
        "k": k,
        "folds": fold_reports,
        "mean_auroc": summary,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H2 group-split detector comparison")
    parser.add_argument(
        "--episodes",
        type=Path,
        help="Episodes JSONL path (default: generate smell-blind stub run)",
    )
    parser.add_argument("--k", type=int, default=3)
    args = parser.parse_args(argv)

    if args.episodes:
        episodes = [
            json.loads(line)
            for line in args.episodes.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    else:
        episodes_path = Path("eval/h2_episodes.jsonl")
        traces_dir = Path("eval/h2_traces")
        _, episodes = run_eval(
            failure_mode="smell-blind",
            output_path=Path("eval/h2_metrics.json"),
            traces_dir=traces_dir,
            episodes_path=episodes_path,
        )

    report = evaluate_group_split(episodes, k=args.k)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
