from __future__ import annotations

import json
import sys
from pathlib import Path

from gates.run import check_gate, load_baseline, load_thresholds


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    metrics_path = repo_root / "eval" / "last_run.json"
    thresholds_path = repo_root / "eval" / "thresholds.yaml"
    baseline_path = repo_root / "eval" / "baselines" / "ci.json"

    if not metrics_path.exists():
        print(f"Missing metrics file: {metrics_path}", file=sys.stderr)
        print("Run `python -m eval` first.", file=sys.stderr)
        sys.exit(1)

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    thresholds = load_thresholds(thresholds_path)
    baseline = load_baseline(baseline_path)

    passed, failures = check_gate(metrics, thresholds, baseline)
    if passed:
        print("Gate PASSED")
        sys.exit(0)

    print("Gate FAILED:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)


if __name__ == "__main__":
    main()
