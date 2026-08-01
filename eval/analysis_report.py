from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from baselines.compare import compare_baselines
from eval.runner import run_eval
from feature_plane import DeployableFeatureInput, extract_deployable_features
from protocol.paired_stats import (
    clustered_bootstrap_ci,
    export_paired_stats,
    ordinal_paired_delta,
    paired_permutation_pvalue,
    pair_degradation_outcomes,
)


def _summary_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    """Metrics snapshot without episode-level bulk."""
    return dict(metrics)


def _average_precision(scores: list[float], labels: list[int]) -> float:
    positives = sum(labels)
    if positives == 0:
        return 0.0
    hits = 0
    area = 0.0
    for rank, (_, label) in enumerate(sorted(zip(scores, labels), reverse=True), start=1):
        if label:
            hits += 1
            area += hits / rank
    return area / positives


def _ordinal_deltas(episodes: list[dict[str, Any]]) -> dict[str, list[float]]:
    severity_scale = {"low": 0.0, "medium": 1.0, "high": 2.0}
    grouped: dict[tuple[str, int], dict[str, float]] = {}
    for episode in episodes:
        key = (str(episode["intent_id"]), int(episode.get("replication_id", 0)))
        raw = episode.get("degradation_severity", 0)
        severity = float(raw) if isinstance(raw, (int, float)) else severity_scale.get(str(raw), 0.0)
        grouped.setdefault(key, {})[str(episode["variant"])] = severity
    by_intent: dict[str, list[float]] = {}
    for (intent_id, _replication), variants in grouped.items():
        if "clean" in variants and "smelly" in variants:
            by_intent.setdefault(intent_id, []).append(variants["clean"] - variants["smelly"])
    return by_intent


def _h2_pr_auc(episodes: list[dict[str, Any]], *, family: str = "provenance") -> float:
    scores: list[float] = []
    labels: list[int] = []
    for episode in episodes:
        features = extract_deployable_features(
            DeployableFeatureInput.from_episode(episode), episode["provenance_path"]
        )
        provenance = features["provenance"]
        if family == "static":
            scores.append(float(features["static"]["requirement_length"]))
        else:
            scores.append(float(provenance["constraint_count"] == 0))
        labels.append(int(episode.get("variant") == "smelly" and not episode.get("oracle_passed")))
    return _average_precision(scores, labels)


def build_analysis_report(work_dir: Path) -> dict[str, Any]:
    """Run happy + smell-blind evals and assemble effect/observability report."""
    work_dir.mkdir(parents=True, exist_ok=True)

    happy_dir = work_dir / "happy"
    smell_blind_dir = work_dir / "smell_blind"

    happy_metrics, _happy_episodes = run_eval(
        failure_mode=None,
        output_path=happy_dir / "metrics.json",
        traces_dir=happy_dir / "traces",
        episodes_path=happy_dir / "episodes.jsonl",
    )
    smell_blind_metrics, smell_blind_episodes = run_eval(
        failure_mode="smell-blind",
        output_path=smell_blind_dir / "metrics.json",
        traces_dir=smell_blind_dir / "traces",
        episodes_path=smell_blind_dir / "episodes.jsonl",
    )

    baselines = compare_baselines(smell_blind_episodes)
    provenance_auroc = baselines["provenance_semantic"]["auroc"]
    operational_auroc = baselines["operational"]["auroc"]

    pair_outcomes = pair_degradation_outcomes(smell_blind_episodes)
    paired_stats = export_paired_stats(
        smell_blind_metrics["oracle_pass_rate_clean"],
        smell_blind_metrics["oracle_pass_rate_smelly"],
        pair_outcomes=pair_outcomes,
    )
    ordinal_deltas = _ordinal_deltas(smell_blind_episodes)
    cluster_means = [
        sum(values) / len(values) for values in ordinal_deltas.values() if values
    ]
    ordinal_delta = sum(cluster_means) / len(cluster_means) if cluster_means else 0.0
    ordinal_ci = clustered_bootstrap_ci(ordinal_deltas)
    ordinal_p = paired_permutation_pvalue(ordinal_deltas)
    provenance_pr_auc = _h2_pr_auc(smell_blind_episodes, family="provenance")
    deployable_pr_auc = _h2_pr_auc(smell_blind_episodes, family="static")

    return {
        "happy": _summary_metrics(happy_metrics),
        "smell_blind": _summary_metrics(smell_blind_metrics),
        "effect_detected": smell_blind_metrics["paired_degradation_rate"] > 0,
        "baselines": baselines,
        "observability_gate_passed": provenance_auroc >= operational_auroc,
        "paired_stats": paired_stats,
        "estimands": {
            "H1.ordinal_delta": {
                "value": ordinal_delta,
                "ci95": {"low": ordinal_ci[0], "high": ordinal_ci[1]},
                "paired_permutation_pvalue": ordinal_p,
                "cluster": "intent_id",
            },
            "H2.pre_final_pr_auc": {
                "provenance": provenance_pr_auc,
                "deployable_baseline": deployable_pr_auc,
                "primary_metric": "PR-AUC",
                "grouping": "intent_id",
            },
        },
    }


def write_analysis_report(
    work_dir: Path,
    output_path: Path,
) -> dict[str, Any]:
    report = build_analysis_report(work_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    work_dir = repo_root / "eval" / ".analysis_work"
    output_path = repo_root / "eval" / "analysis_report.json"
    write_analysis_report(work_dir, output_path)


if __name__ == "__main__":
    main()
