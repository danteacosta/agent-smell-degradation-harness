from __future__ import annotations

import json
from pathlib import Path

from mitigation.tradeoff import build_mitigation_report


def write_mitigation_report(
    work_dir: Path,
    output_path: Path,
) -> dict:
    report = build_mitigation_report(work_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    work_dir = repo_root / "eval" / ".mitigation_work"
    output_path = repo_root / "eval" / "mitigation_report.json"
    write_mitigation_report(work_dir, output_path)


if __name__ == "__main__":
    main()
