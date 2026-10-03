"""Build the selection-case fixtures and A/B/C configs from their specs.

  build   write eval/fixtures/<case>/{page.html,runner.cjs,qualify.py} and
          data/abc-cases/<case>.json for every spec
  check   local pre-qualification without Docker: run every control of every
          case with the local Node and Playwright and compare the class with
          the expected one. The binding qualification is each fixture's
          qualify.py inside the pinned Docker image (scripts/qualify_selection_cases.sh).

Each spec is written before any generation and never sees a model output.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.selection_cases import templates  # noqa: E402
from scripts.selection_cases.specs_immich_mealie import CASES as IMMICH_MEALIE  # noqa: E402
from scripts.selection_cases.specs_paperless import CASES as PAPERLESS  # noqa: E402
from scripts.selection_cases.specs_grist import CASES as GRIST  # noqa: E402
from scripts.selection_cases.specs_mattermost import CASES as MATTERMOST  # noqa: E402
from scripts.selection_cases.specs_nextcloud import CASES as NEXTCLOUD  # noqa: E402
from scripts.selection_cases.specs_openproject import CASES as OPENPROJECT  # noqa: E402
from scripts.selection_cases.specs_wekan import CASES as WEKAN  # noqa: E402
from scripts.selection_cases.specs_zulip import CASES as ZULIP  # noqa: E402

# Batch 1 first and in its original order so that existing seeds do not change.
SPECS = PAPERLESS + IMMICH_MEALIE + GRIST + MATTERMOST + NEXTCLOUD + OPENPROJECT + WEKAN + ZULIP
IMAGE = "sha256:00d1265095773b7f8a12aa73e81d0bab75563cbd672dd0b5d91783ea1b6d4400"
MODELS = ["gpt-5.6-luna", "gpt-5.6-sol"]
REPETITIONS = 2  # pre-registration: two repetitions per arm and model
FIRST_SEED = 2026100301


def instruction(spec: dict) -> str:
    return ("Implement only the requirement in the frozen browser page. Replace the single /* MODEL_BEHAVIOR */ "
            "marker with vanilla JavaScript statements using the provided app API. Register "
            f"{spec['register']} to handle the visible {spec['control']}. Do not change any other byte of the page. "
            "Return only the complete HTML page.")


def validate(spec: dict) -> None:
    arms = spec["arms"]
    if set(arms) != {"A", "B", "C"} or len({arms["A"], arms["B"], arms["C"]}) != 3:
        raise ValueError(f"{spec['case']}: three distinct arms required")
    if not arms["A"].startswith(arms["C"].rstrip(".")[:60]):
        raise ValueError(f"{spec['case']}: C must be A with one span removed")
    if len(arms["C"]) >= len(arms["A"]):
        raise ValueError(f"{spec['case']}: C must be shorter than A")
    if set(spec["target"]) & set(spec["non_target"]) or not spec["target"] or not spec["non_target"]:
        raise ValueError(f"{spec['case']}: target and non-target assertions must be disjoint and non-empty")
    expected = {e for _, e in spec["controls"].values()}
    if not {"pass", "target_only_failure", "non_target_only_failure"} <= expected:
        raise ValueError(f"{spec['case']}: controls must cover pass, target and non-target failures")
    if len(spec["fixtures"]) != 2:
        raise ValueError(f"{spec['case']}: two fixtures required")


def build(root: Path = ROOT) -> list[str]:
    names = []
    for offset, spec in enumerate(SPECS):
        validate(spec)
        spec = {**spec, "controls": {**spec["controls"], **templates.STANDARD_CONTROLS}}
        fixture = root / "eval/fixtures" / spec["case"]
        fixture.mkdir(parents=True, exist_ok=True)
        (fixture / "page.html").write_text(templates.page(spec))
        (fixture / "runner.cjs").write_text(templates.runner(spec))
        (fixture / "qualify.py").write_text(templates.qualifier(spec))
        config = {
            "case": spec["case"], "intent_id": spec["case"], "project_id": spec["project_id"],
            "candidate_id": spec["candidate_id"], "source": spec["source"],
            "fixture": f"eval/fixtures/{spec['case']}", "marker": templates.MARKER,
            "instruction": instruction(spec), "arms": spec["arms"], "models": MODELS,
            "repetitions": REPETITIONS, "seed": FIRST_SEED + offset, "image": IMAGE,
            "status": "draft_pending_qualification_and_arm_review",
        }
        (root / "data/abc-cases").mkdir(parents=True, exist_ok=True)
        (root / "data/abc-cases" / f"{spec['case']}.json").write_text(
            json.dumps(config, indent=2, ensure_ascii=False) + "\n")
        names.append(spec["case"])
    return names


def check(work: Path, only: list[str] | None = None) -> dict:
    """Run every control locally; /input and /output are the runner's fixed paths."""
    inputs, outputs = Path("/input"), Path("/output")
    results = {}
    for spec in SPECS:
        if only and spec["case"] not in only:
            continue
        fixture = ROOT / "eval/fixtures" / spec["case"]
        qualifier = runpy.run_path(str(fixture / "qualify.py"))
        page = (fixture / "page.html").read_text()
        for mode, (behavior, expected) in qualifier["CONTROLS"].items():
            for d in (inputs, outputs):
                shutil.rmtree(d, ignore_errors=True)
                d.mkdir()
            (inputs / "app.html").write_text(page.replace(templates.MARKER, behavior))
            proc = subprocess.run(["node", str(fixture / "runner.cjs")], capture_output=True, text=True,
                                  timeout=120, env={**os.environ})
            report_path = outputs / "report.json"
            report = json.loads(report_path.read_text()) if report_path.is_file() else {}
            observed = qualifier["classify"](report)
            key = f"{spec['case']}/{mode}"
            results[key] = {"expected": expected, "observed": observed, "ok": observed == expected}
            if observed != expected:
                results[key]["detail"] = {"assertions": report.get("assertions"), "error": report.get("error"),
                                          "console": report.get("console_errors"), "stderr": proc.stderr[-400:]}
            dest = work / spec["case"] / mode
            dest.mkdir(parents=True, exist_ok=True)
            for item in outputs.iterdir():
                shutil.copy(item, dest / item.name)
    return results


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("build")
    c = sub.add_parser("check")
    c.add_argument("--work", type=Path, required=True)
    c.add_argument("--case", action="append")
    args = parser.parse_args(argv)
    if args.mode == "build":
        print(json.dumps(build(), indent=2))
        return
    results = check(args.work, args.case)
    print(json.dumps(results, indent=2))
    failed = [k for k, v in results.items() if not v["ok"]]
    print(f"{len(results) - len(failed)}/{len(results)} controls classified as expected")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
