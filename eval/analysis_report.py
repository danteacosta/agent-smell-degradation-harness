from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from baselines.compare import compare_baselines
from eval.runner import run_eval
from protocol.paired_stats import export_paired_stats, pair_degradation_outcomes


def _summary_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    """Metrics snapshot without episode-level bulk."""
    return dict(metrics)


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

    return {
        "happy": _summary_metrics(happy_metrics),
        "smell_blind": _summary_metrics(smell_blind_metrics),
        "effect_detected": smell_blind_metrics["paired_degradation_rate"] > 0,
        "baselines": baselines,
        "observability_gate_passed": provenance_auroc >= operational_auroc,
        "paired_stats": paired_stats,
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
