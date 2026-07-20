from __future__ import annotations

import json
from pathlib import Path

from protocol.packaging import build_dissertation_bundle, render_bundle_summary


def write_dissertation_bundle(
    repo_root: Path,
    work_dir: Path,
    output_path: Path,
    summary_path: Path,
) -> dict:
    bundle = build_dissertation_bundle(repo_root, work_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(render_bundle_summary(bundle), encoding="utf-8")
    return bundle


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    work_dir = repo_root / "eval" / ".dissertation_work"
    output_path = repo_root / "eval" / "dissertation_bundle.json"
    summary_path = repo_root / "docs" / "dissertation" / "BUNDLE_SUMMARY.md"
    write_dissertation_bundle(repo_root, work_dir, output_path, summary_path)


if __name__ == "__main__":
    main()
