from __future__ import annotations

from pathlib import Path

from eval.runner import run_eval


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    run_eval(
        output_path=repo_root / "eval" / "last_run.json",
        traces_dir=repo_root / "eval" / "traces",
    )


if __name__ == "__main__":
    main()
