from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from eval.runner import run_eval
from gates.run import check_gate, load_thresholds

MODES: dict[str, dict[str, Any]] = {
    "smell-blind": {
        "failure_mode": "smell-blind",
        "skip_semantic_provenance": False,
    },
    "oracle-mismatch": {
        "failure_mode": "oracle-mismatch",
        "skip_semantic_provenance": False,
    },
    "provenance-collapse": {
        "failure_mode": None,
        "skip_semantic_provenance": True,
    },
}


def check_gate_pre_harness(
    metrics: dict[str, Any],
    thresholds: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Operational-only gate used as pre-harness baseline: always pass if episodes ran."""
    _ = thresholds
    if metrics.get("episode_count", 0) > 0:
        return True, []
    return False, ["episode_count is 0"]


def _catch_rate(passed: bool) -> float:
    return 0.0 if passed else 1.0


def simulate_mode(
    mode: str,
    *,
    traces_dir: Path,
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}; expected one of {sorted(MODES)}")

    config = MODES[mode]
    metrics_path = traces_dir.parent / "metrics.json"
    metrics = run_eval(
        failure_mode=config["failure_mode"],
        skip_semantic_provenance=config["skip_semantic_provenance"],
        output_path=metrics_path,
        traces_dir=traces_dir,
    )

    before_passed, _ = check_gate_pre_harness(metrics, thresholds)
    after_passed, _ = check_gate(metrics, thresholds)

    return {
        "before_catch_rate": _catch_rate(before_passed),
        "after_catch_rate": _catch_rate(after_passed),
        "metrics": metrics,
    }


def simulate_all(
    *,
    report_path: Path | None = None,
    thresholds: dict[str, Any] | None = None,
    work_dir: Path | None = None,
    last_run_path: Path | None = None,
) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[1]
    if report_path is None:
        report_path = repo_root / "eval" / "sim_report.json"
    if thresholds is None:
        thresholds = load_thresholds(repo_root / "eval" / "thresholds.yaml")
    if work_dir is None:
        work_dir = repo_root / "eval" / ".simulate_work"
    if last_run_path is None:
        last_run_path = repo_root / "eval" / "last_run.json"

    last_run_snapshot: str | None = None
    if last_run_path.exists():
        last_run_snapshot = last_run_path.read_text(encoding="utf-8")

    report: dict[str, Any] = {}
    task_families: set[str] = set()

    for mode in MODES:
        mode_dir = work_dir / mode
        result = simulate_mode(
            mode,
            traces_dir=mode_dir / "traces",
            thresholds=thresholds,
        )
        report[mode] = result
        task_families.update(result["metrics"].get("task_families_exercised", []))

    report["task_families_exercised"] = sorted(task_families)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if last_run_snapshot is not None:
        current = last_run_path.read_text(encoding="utf-8")
        if current != last_run_snapshot:
            raise RuntimeError(
                f"simulate must not modify {last_run_path}; isolation rule violated"
            )

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate smell-degradation failure modes FM1–FM3.",
    )
    parser.add_argument(
        "--mode",
        choices=sorted(MODES),
        help="Run a single failure mode instead of all three.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Output report path (default: eval/sim_report.json).",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    report_path = args.report or (repo_root / "eval" / "sim_report.json")
    thresholds = load_thresholds(repo_root / "eval" / "thresholds.yaml")

    if args.mode:
        work_dir = repo_root / "eval" / ".simulate_work"
        result = simulate_mode(
            args.mode,
            traces_dir=work_dir / args.mode / "traces",
            thresholds=thresholds,
        )
        report = {args.mode: result}
        families = result["metrics"].get("task_families_exercised", [])
        report["task_families_exercised"] = sorted(families)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    else:
        simulate_all(report_path=report_path, thresholds=thresholds)


if __name__ == "__main__":
    main()
