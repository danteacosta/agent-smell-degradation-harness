from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from protocol.paired_stats import group_binary_pairs


def _load_episodes(path: Path) -> list[dict[str, Any]]:
    episodes: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                episodes.append(json.loads(line))
    return episodes


def _paired_outcomes(episodes: list[dict[str, Any]]) -> dict[tuple, dict[str, bool]]:
    return group_binary_pairs(episodes)


def _compute_paired_degradation_rate(
    outcomes: dict[tuple, dict[str, bool]],
) -> float:
    if not outcomes:
        return 0.0
    degraded = sum(
        1
        for results in outcomes.values()
        if results.get("clean") and not results.get("smelly")
    )
    return degraded / len(outcomes)


def _per_intent_table(episodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_intent: dict[str, dict[str, Any]] = {}
    for episode in episodes:
        intent_id = episode["intent_id"]
        row = by_intent.setdefault(
            intent_id,
            {
                "intent_id": intent_id,
                "clean_pass": 0,
                "clean_total": 0,
                "smelly_pass": 0,
                "smelly_total": 0,
            },
        )
        if episode["variant"] == "clean":
            row["clean_total"] += 1
            row["clean_pass"] += int(episode["oracle_passed"])
        else:
            row["smelly_total"] += 1
            row["smelly_pass"] += int(episode["oracle_passed"])

    table = []
    for row in sorted(by_intent.values(), key=lambda item: item["intent_id"]):
        clean_rate = row["clean_pass"] / row["clean_total"] if row["clean_total"] else 0.0
        smelly_rate = row["smelly_pass"] / row["smelly_total"] if row["smelly_total"] else 0.0
        table.append(
            {
                **row,
                "clean_pass_rate": round(clean_rate, 4),
                "smelly_pass_rate": round(smelly_rate, 4),
                "paired_delta": round(clean_rate - smelly_rate, 4),
            }
        )
    return table


def analyze_episodes(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    if not episodes:
        raise ValueError("empty episodes cannot establish a negative effect boundary")
    outcomes = _paired_outcomes(episodes)
    paired_rate = _compute_paired_degradation_rate(outcomes)
    per_intent = _per_intent_table(episodes)

    smell_types: dict[str, int] = {}
    for episode in episodes:
        if episode.get("variant") == "smelly" and episode.get("smell"):
            smell_type = episode["smell"]["type"]
            if not episode["oracle_passed"]:
                smell_types[smell_type] = smell_types.get(smell_type, 0) + 1

    return {
        "analysis_scope": "legacy_binary_descriptive_only",
        "confirmatory_eligible": False,
        "H1_paired_degradation": {
            "paired_degradation_rate": round(paired_rate, 4),
            "pair_count": len(outcomes),
            "effect_detected": paired_rate > 0,
        },
        "H2_by_smell_type": smell_types,
        "per_intent_table": per_intent,
        "negative_boundary": abs(paired_rate) < 0.05,
    }


def write_thesis_analysis(
    episodes_path: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    episodes = _load_episodes(episodes_path)
    report = analyze_episodes(episodes)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Legacy descriptive binary report; historical H1/H2 keys are not hypothesis tests")
    parser.add_argument("--episodes", required=True, help="Path to episodes JSONL")
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output JSON path (default: alongside episodes as thesis_tables.json)",
    )
    args = parser.parse_args(argv)

    episodes_path = Path(args.episodes)
    output_path = (
        Path(args.output)
        if args.output
        else episodes_path.parent / "thesis_tables.json"
    )
    write_thesis_analysis(episodes_path, output_path)


if __name__ == "__main__":
    main()
