"""Omission Bench: build the public benchmark and score new models on it.

A case is one requirement with three variants: A (complete), B (reworded, same
meaning) and C (one testable rule removed). A model receives each prompt,
returns a complete HTML page, and a frozen browser oracle checks the target
rule. The question the benchmark answers: when the rule is missing from the
request, does the generated interface still follow it?

  build   materialize prompts, oracle paths and the reference leaderboard
          from the repository into benchmark/omission-bench
  score   run the oracle on a directory of generated pages and summarize
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "benchmark/omission-bench"
IMAGE = "sha256:00d1265095773b7f8a12aa73e81d0bab75563cbd672dd0b5d91783ea1b6d4400"

# case -> (collector module that defines prompt() and FIXTURE, public results summary)
CASES = {
    "kanboard-closed-filter": ("scripts.kanboard_closed_filter_pilot_v2",
                               "data/e2e-kanboard-closed-filter/results-20260927/summary.json"),
    "nextcloud-restore-conflict": ("scripts.nextcloud_restore_conflict_v4_pilot",
                                   "data/e2e-nextcloud-restore-conflict/results-20260927/summary.json"),
    "openproject-invalid-remaining": ("scripts.openproject_invalid_remaining_pilot",
                                      "data/e2e-openproject-invalid-remaining/results-20260926/summary.json"),
    "paperless-inbox-suggestions": ("scripts.paperless_inbox_suggestions_pilot_v3",
                                    "data/e2e-paperless-inbox-suggestions/replication-20261001-v3/summary.json"),
    "paperless-nested-tags": ("scripts.paperless_nested_tags_pilot",
                              "data/e2e-paperless-nested-tags/results-20260927/summary.json"),
    "realworld-comment-delete": ("scripts.realworld_comment_delete_replication",
                                 "data/e2e-realworld-comment-delete/replication-20261001/summary.json"),
    "todomvc-clear-button": ("scripts.todomvc_clear_button_replication",
                             "data/e2e-todomvc-clear-button/replication-20261001/summary.json"),
}
ARMS = ("A", "B", "C")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def leaderboard_rows(summary: dict, case: str) -> list[dict]:
    rows = []
    for model, arms in summary["counts"].items():
        for arm, categories in arms.items():
            total = sum(categories.values())
            rows.append({"case": case, "model": model, "arm": arm, "runs": total,
                         "pass": categories.get("pass", 0),
                         "target_failure": categories.get("target_only_failure", 0),
                         "other": total - categories.get("pass", 0) - categories.get("target_only_failure", 0)})
    return rows


def build(out: Path = OUT) -> dict:
    if out.exists():
        shutil.rmtree(out)
    cases, board = [], []
    for case, (module_name, summary_path) in CASES.items():
        module = importlib.import_module(module_name)
        fixture = Path(module.FIXTURE)
        case_dir = out / "cases" / case
        case_dir.mkdir(parents=True)
        prompts = {}
        for arm in ARMS:
            text = module.prompt(arm)
            (case_dir / f"{arm}.prompt.txt").write_text(text)
            prompts[arm] = sha256_bytes(text.encode())
        oracle = {name: str((fixture / name).relative_to(ROOT)) for name in ("page.html", "runner.cjs", "qualify.py")}
        cases.append({"case": case, "prompt_sha256": prompts, "oracle": oracle,
                      "oracle_sha256": {n: sha256_bytes((ROOT / p).read_bytes()) for n, p in oracle.items()},
                      "reference_results": summary_path, "collector": module_name})
        board += leaderboard_rows(json.loads((ROOT / summary_path).read_text()), case)
    manifest = {"schema_version": "omission-bench/v1", "image": IMAGE, "arms": ARMS, "cases": cases,
                "license_note": "Requirement texts are excerpts of each project's documentation under its own "
                                "license; see the project sources recorded with each case."}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (out / "reference-leaderboard.json").write_text(json.dumps(board, indent=2) + "\n")
    (out / "LEADERBOARD.md").write_text(render_leaderboard(board))
    return {"cases": len(cases), "rows": len(board)}


def render_leaderboard(board: list[dict]) -> str:
    per_model = defaultdict(Counter)
    for row in board:
        key = row["model"]
        per_model[key][f"{row['arm']}_runs"] += row["runs"]
        per_model[key][f"{row['arm']}_target_failure"] += row["target_failure"]
    cases_with_c_failure = defaultdict(set)
    for row in board:
        if row["arm"] == "C" and row["target_failure"]:
            cases_with_c_failure[row["model"]].add(row["case"])
    n_cases = len({row["case"] for row in board})
    lines = ["# Omission Bench reference results", "",
             "Target-rule failures by arm. A good model fails rarely in A and B; C shows how often a "
             "missing rule is also missing from the interface.", "",
             "| Model | A failures | B failures | C failures | Cases with a C failure |",
             "| --- | ---: | ---: | ---: | ---: |"]
    for model, c in sorted(per_model.items()):
        lines.append(f"| {model} | {c['A_target_failure']}/{c['A_runs']} | {c['B_target_failure']}/{c['B_runs']} | "
                     f"{c['C_target_failure']}/{c['C_runs']} | {len(cases_with_c_failure[model])}/{n_cases} |")
    lines += ["", "Per case and arm: `reference-leaderboard.json`. Runs are repetitions of the same case, "
              "not independent requirements."]
    return "\n".join(lines) + "\n"


def score(outputs: Path, results: Path, executor=None) -> dict:
    """Score generated pages named <case>__<arm>__<run>.html with each case's frozen oracle."""
    if executor is None:
        from scripts.kanboard_duplicate_collect import execute
        executor = lambda case, html, out: execute(  # noqa: E731
            IMAGE, html.parent, out, ROOT / case["oracle"]["runner.cjs"], ROOT / case["oracle"]["qualify.py"])
    manifest = json.loads((OUT / "manifest.json").read_text())
    cases = {c["case"]: c for c in manifest["cases"]}
    counts = defaultdict(Counter)
    rows = []
    for page in sorted(outputs.glob("*.html")):
        case_name, arm, run = page.stem.split("__")
        if case_name not in cases or arm not in ARMS:
            raise ValueError(f"unknown case or arm in {page.name}")
        collector = importlib.import_module(cases[case_name]["collector"])
        try:
            admitted = collector.admit(page.read_text())  # same scaffold rules as the reference runs
        except (UnicodeError, ValueError):
            counts[(case_name, arm)]["invalid_output"] += 1
            rows.append({"case": case_name, "arm": arm, "run": run, "category": "invalid_output"})
            continue
        staging = results / "inputs" / page.stem
        staging.mkdir(parents=True, exist_ok=False)
        (staging / "app.html").write_bytes(admitted)
        try:
            category = executor(cases[case_name], staging / "app.html", results / "execution" / page.stem)["category"]
        except Exception as error:
            category = f"runner_error:{type(error).__name__}"
        counts[(case_name, arm)][category] += 1
        rows.append({"case": case_name, "arm": arm, "run": run, "category": category})
    summary = {f"{c}/{a}": dict(v) for (c, a), v in sorted(counts.items())}
    (results / "scores.json").write_text(json.dumps({"rows": rows, "summary": summary}, indent=2) + "\n")
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("build")
    s = sub.add_parser("score")
    s.add_argument("--outputs", type=Path, required=True)
    s.add_argument("--results", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(build() if args.mode == "build" else score(args.outputs, args.results), indent=2))


if __name__ == "__main__":
    main()
