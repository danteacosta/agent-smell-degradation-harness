from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from baselines.score import mann_whitney_auroc
from eval.calibration import CalibrationError, evaluate_threshold, fit_threshold, select_family
from eval.splits import apply_split_manifest, build_grouped_split_manifest
from feature_plane import DeployableFeatureInput, extract_deployable_features, semantic_risk
from eval.runner import run_eval
from observability.features import extract_tier_a_features
from eval.feature_manifest import validate_feature_manifest
from eval.confirmatory_report import clustered_pr_auc_delta, finalize_h2_claim
from label_plane.human_annotation import load_primary_label_manifest
from eval.sample_gate import validate_confirmatory_design

FAMILIES = ("static_smell", "operational", "provenance_semantic")


def _episode_label(
    episode: dict[str, Any], primary_labels: dict[str, int] | None = None
) -> int:
    if primary_labels is not None:
        episode_id = str(episode.get("episode_id", ""))
        if episode_id not in primary_labels:
            raise ValueError(f"missing primary human label for {episode_id}")
        label = primary_labels[episode_id]
        if label not in (0, 1):
            raise ValueError(f"primary human label for {episode_id} must be binary")
        return label
    return 1 if episode.get("variant") == "smelly" and not episode.get("oracle_passed") else 0


def _family_score(family: str, features: dict[str, Any]) -> float:
    if family == "static_smell":
        static = features["static_smell"]
        return float(static.get("requirement_length", static.get("smell_present", 0))) / 1000.0
    if family == "operational":
        operational = features["operational"]
        return float(operational["event_count"]) + float(operational["latency_ms"]) / 1000.0
    if family == "provenance_semantic":
        return semantic_risk(features["provenance_semantic"])
    return 0.0


def _average_precision(scores: list[float], labels: list[int]) -> float:
    positives = sum(labels)
    if positives == 0:
        return 0.0
    ranked = sorted(zip(scores, labels), key=lambda item: item[0], reverse=True)
    hits = 0
    area = 0.0
    for rank, (_, label) in enumerate(ranked, start=1):
        if label:
            hits += 1
            area += hits / rank
    return area / positives


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
        family_pr_auc: dict[str, float] = {}
        for family in FAMILIES:
            scores = []
            for episode in test_eps:
                deployable = extract_deployable_features(
                    DeployableFeatureInput.from_episode(episode), episode["provenance_path"]
                )
                features = {
                    "static_smell": deployable["static"],
                    "operational": deployable["operational"],
                    "provenance_semantic": deployable["provenance"],
                }
                scores.append(_family_score(family, features))
            family_aurocs[family] = mann_whitney_auroc(scores, labels)
            family_pr_auc[family] = _average_precision(scores, labels)

        fold_reports.append(
            {
                "fold": fold_index,
                "test_intents": sorted(test_intents),
                "auroc": family_aurocs,
                "pr_auc": family_pr_auc,
            }
        )

    aggregate: dict[str, list[float]] = {family: [] for family in FAMILIES}
    pr_aggregate: dict[str, list[float]] = {family: [] for family in FAMILIES}
    for report in fold_reports:
        for family in FAMILIES:
            aggregate[family].append(report["auroc"][family])
            pr_aggregate[family].append(report["pr_auc"][family])

    summary = {
        family: sum(values) / len(values) if values else 0.5
        for family, values in aggregate.items()
    }

    return {
        "k": k,
        "folds": fold_reports,
        "mean_auroc": summary,
        "mean_pr_auc": {
            family: sum(values) / len(values) if values else 0.0
            for family, values in pr_aggregate.items()
        },
    }


def _episode_family_scores(
    episodes: list[dict[str, Any]],
    *,
    feature_manifest: dict[str, Any] | None = None,
    confirmatory: bool = False,
) -> dict[str, list[float]]:
    """Build deployable scores without allowing terminal labels into features."""

    scores = {family: [] for family in FAMILIES}
    manifest_rows: dict[str, Any] = {}
    if feature_manifest is not None:
        validate_feature_manifest(feature_manifest, episodes)
        manifest_rows = {
            str(row["episode_id"]): row for row in feature_manifest["rows"]
        }
    for episode in episodes:
        episode_id = str(episode.get("episode_id", ""))
        if confirmatory and feature_manifest is None and (
            "h2_scores" in episode or "feature_scores" in episode
        ):
            raise ValueError("confirmatory H2 score injection requires a feature manifest")
        if episode_id in manifest_rows:
            supplied = manifest_rows[episode_id]["scores"]
            for family in FAMILIES:
                scores[family].append(float(supplied[family]))
            continue
        supplied = episode.get("h2_scores") or episode.get("feature_scores")
        if isinstance(supplied, dict) and all(family in supplied for family in FAMILIES):
            for family in FAMILIES:
                scores[family].append(float(supplied[family]))
            continue
        deployable = extract_deployable_features(
            DeployableFeatureInput.from_episode(episode), episode.get("provenance_path", "")
        )
        features = {
            "static_smell": deployable["static"],
            "operational": deployable["operational"],
            "provenance_semantic": deployable["provenance"],
        }
        for family in FAMILIES:
            scores[family].append(_family_score(family, features))
    return scores


def evaluate_confirmatory(
    episodes: list[dict[str, Any]],
    *,
    seed: int = 0,
    split_manifest: dict[str, Any] | None = None,
    confirmatory: bool = False,
    primary_labels: dict[str, int] | dict[str, Any] | None = None,
    feature_manifest: dict[str, Any] | None = None,
    enforce_design: bool = True,
) -> dict[str, Any]:
    """Run the preregistered H2 train/calibration/test protocol.

    Candidate feature-family selection is fit on train groups, the threshold
    is fit on calibration groups, and every reported held-out metric is
    computed exactly once on untouched test groups.  The split manifest is
    returned verbatim as provenance so a result can be reproduced or audited.
    """

    if not episodes:
        raise ValueError("H2 confirmatory evaluation requires episodes")
    if confirmatory and primary_labels is None:
        raise ValueError("confirmatory H2 requires primary human labels")
    if confirmatory and isinstance(primary_labels, dict) and "schema_version" in primary_labels:
        primary_labels = load_primary_label_manifest(
            primary_labels, (str(episode.get("episode_id", "")) for episode in episodes)
        )
    if confirmatory and feature_manifest is None and any(
        "h2_scores" in episode or "feature_scores" in episode for episode in episodes
    ):
        raise ValueError("confirmatory H2 score injection requires a feature manifest")
    if feature_manifest is not None:
        validate_feature_manifest(feature_manifest, episodes)
    manifest = split_manifest or build_grouped_split_manifest(episodes, seed=seed)
    partitions = apply_split_manifest(episodes, manifest)
    if confirmatory and enforce_design:
        validate_confirmatory_design(episodes, partitions)
    split_scores: dict[str, dict[str, list[float]]] = {
        split: {family: [] for family in FAMILIES} for split in ("train", "calibration", "test")
    }
    split_labels: dict[str, list[int]] = {split: [] for split in ("train", "calibration", "test")}
    # Recompute score rows from each partition; this is intentionally simple
    # and prevents accidental positional leakage if a caller supplies a custom
    # manifest with a different partition ordering.
    for split, rows in partitions.items():
        row_scores = _episode_family_scores(
            list(rows), feature_manifest=feature_manifest, confirmatory=confirmatory
        )
        split_scores[split] = row_scores
        split_labels[split] = [
            _episode_label(episode, primary_labels if confirmatory else None)
            for episode in rows
        ]
        if not {0, 1}.issubset(set(split_labels[split])):
            raise CalibrationError(
                f"{split} group must contain both clean and degraded labels for confirmatory H2"
            )
    selection = select_family(split_scores["train"], split_labels["train"], split="train")
    selected_family = selection["selected_family"]
    calibration = fit_threshold(
        split_scores["calibration"][selected_family],
        split_labels["calibration"],
        split="calibration",
    )
    held_out = evaluate_threshold(
        split_scores["test"][selected_family],
        split_labels["test"],
        calibration["threshold"],
        split="test",
    )
    primary_effect: dict[str, Any] | None = None
    if confirmatory:
        train_candidates = selection["candidates"]
        baseline_family = max(
            ("static_smell", "operational"),
            key=lambda family: (
                float(train_candidates[family]["pr_auc"]),
                float(train_candidates[family]["auroc"]),
                family,
            ),
        )
        test_rows = list(partitions["test"])
        test_scores = _episode_family_scores(
            test_rows, feature_manifest=feature_manifest, confirmatory=confirmatory
        )
        primary_effect = clustered_pr_auc_delta(
            test_rows,
            test_scores["provenance_semantic"],
            test_scores[baseline_family],
            split_labels["test"],
            cluster_key="source_intent_id",
            draws=2000,
            seed=seed,
        )
        primary_effect["baseline_family"] = baseline_family
        primary_effect["provenance_family"] = "provenance_semantic"
        primary_effect = finalize_h2_claim(primary_effect, margin=0.05)
    report = {
        "protocol": "H2-confirmatory-v1",
        "selected_family": selected_family,
        "split": manifest,
        "model_selection": selection,
        "calibration": calibration,
        "held_out": {
            **held_out,
            "family": selected_family,
        },
    }
    if confirmatory:
        report["labels"] = {"source": "primary_human_adjudicated"}
        report["features"] = {
            "schema_version": str(feature_manifest["schema_version"])
            if feature_manifest
            else "computed-from-traces"
        }
        report["primary_effect"] = primary_effect
    return report


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
