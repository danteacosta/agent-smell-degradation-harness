"""Fail-closed browser classification for Kanboard duplicate-title pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import uuid

TARGET = {"duplicate_title_1", "duplicate_title_2"}
NON_TARGET = {
    "source_preserved_1", "source_preserved_2",
    "unrelated_preserved_1", "unrelated_preserved_2",
    "same_project_1", "same_project_2",
}
SCREENSHOTS = ["fixture-1.png", "fixture-2.png"]


def classify(report: dict) -> str:
    if not isinstance(report, dict):
        return "malformed_report"
    if (
        report.get("schema_version") != "kanboard-duplicate-title-browser/v1"
        or re.fullmatch(r"[0-9a-f]{64}", str(report.get("app_sha256", ""))) is None
        or not isinstance(report.get("console_errors"), list)
        or len(report["console_errors"]) > 20
        or not all(isinstance(item, str) and len(item) <= 500 for item in report["console_errors"])
    ):
        return "malformed_report"
    if report.get("status") in {"interface_error", "browser_error"}:
        if (
            set(report) != {"schema_version", "status", "app_sha256", "assertions", "console_errors", "error"}
            or report["assertions"] != {}
            or not isinstance(report["error"], str)
            or len(report["error"]) > 1500
        ):
            return "malformed_report"
        return report["status"]
    if (
        report.get("status") != "complete"
        or set(report) != {"schema_version", "status", "app_sha256", "assertions", "console_errors", "screenshots"}
        or report.get("screenshots") != SCREENSHOTS
    ):
        return "malformed_report"
    assertions = report.get("assertions")
    if (
        not isinstance(assertions, dict)
        or set(assertions) != TARGET | NON_TARGET
        or not all(type(value) is bool for value in assertions.values())
    ):
        return "malformed_report"
    if report["console_errors"]:
        return "browser_error"
    target_failed = any(not assertions[key] for key in TARGET)
    non_target_failed = any(not assertions[key] for key in NON_TARGET)
    if target_failed and non_target_failed:
        return "mixed_failure"
    if target_failed:
        return "target_only_failure"
    if non_target_failed:
        return "non_target_only_failure"
    return "pass"


MARKER = "/* MODEL_BEHAVIOR */"
CONTROLS = {
    "reference": (
        "app.onDuplicate(task=>({...task,id:'copy-'+task.id}));", "pass",
    ),
    "alternative": (
        "app.onDuplicate(function(task){return {id:'new-'+task.id,projectId:task.projectId,title:task.title}});",
        "pass",
    ),
    "target-mutant": (
        "app.onDuplicate(task=>({...task,id:'copy-'+task.id,title:''}));",
        "target_only_failure",
    ),
    "non-target-mutant": (
        "app.onDuplicate(task=>({...task,id:'copy-'+task.id,projectId:'wrong-project'}));",
        "non_target_only_failure",
    ),
    "duplicate-identity": (
        "app.onDuplicate(task=>({...task}));", "interface_error",
    ),
    "precreated-duplicate": (
        "tasks.push({...tasks[0],id:'copy-source-task'});", "interface_error",
    ),
    "missing-behavior": ("", "interface_error"),
    "script-error": ("throw new Error('qualification control');", "browser_error"),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assemble(scaffold: str, behavior: str) -> str:
    if scaffold.count(MARKER) != 1:
        raise ValueError("one behavior marker required")
    return scaffold.replace(MARKER, behavior)


def docker_command(image: str, inputs: Path, output: Path) -> list[str]:
    if re.fullmatch(r"sha256:[0-9a-f]{64}", image) is None:
        raise ValueError("immutable image ID required")
    return [
        "docker", "run", "--rm", "--init", "--name", "kanboard-title-" + uuid.uuid4().hex,
        "--network", "none", "--user", f"{os.getuid()}:{os.getgid()}", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", "256", "--memory", "1g", "--cpus", "2",
        "--shm-size", "256m", "--tmpfs", "/tmp:rw,nosuid,size=256m",
        "--env", "HOME=/tmp", "--env", "NODE_PATH=/opt/openproject-remaining-pilot/node_modules",
        "--mount", f"type=bind,src={inputs.resolve()},dst=/input,readonly",
        "--mount", f"type=bind,src={output.resolve()},dst=/output",
        "--entrypoint", "node", image, "/input/runner.cjs",
    ]


def qualify(image: str, destination: Path) -> dict:
    found = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", image],
        check=True, capture_output=True, text=True, timeout=30,
    ).stdout.strip()
    if found != image:
        raise ValueError("image identity mismatch")
    fixture = Path(__file__).resolve().parent
    scaffold = (fixture / "page.html").read_text(encoding="utf-8")
    runner = fixture / "runner.cjs"
    destination.mkdir(parents=True, exist_ok=False)
    cases = []
    for mode, (behavior, expected) in CONTROLS.items():
        root = destination / mode
        inputs, output = root / "input", root / "output"
        inputs.mkdir(parents=True)
        output.mkdir()
        (inputs / "app.html").write_text(assemble(scaffold, behavior), encoding="utf-8")
        (inputs / "runner.cjs").write_bytes(runner.read_bytes())
        result = subprocess.run(
            docker_command(image, inputs, output), capture_output=True,
            timeout=90, check=False,
        )
        (root / "stdout.bin").write_bytes(result.stdout)
        (root / "stderr.bin").write_bytes(result.stderr)
        report_path = output / "report.json"
        report = json.loads(report_path.read_text()) if report_path.is_file() else {}
        observed = classify(report)
        if observed != expected:
            raise ValueError(f"{mode}: expected {expected}, got {observed}; stderr={result.stderr[-500:]!r}")
        if (result.returncode == 0) != (report.get("status") == "complete"):
            raise ValueError(f"{mode}: return code disagrees with report")
        if report.get("app_sha256") != digest(inputs / "app.html"):
            raise ValueError(f"{mode}: app digest mismatch")
        if report.get("status") == "complete":
            for name in SCREENSHOTS:
                image_path = output / name
                if not image_path.is_file() or not image_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
                    raise ValueError(f"{mode}: screenshot missing or invalid")
        cases.append({"mode": mode, "expected": expected, "observed": observed,
                      "report_sha256": digest(report_path)})
    evidence = {
        "schema_version": "kanboard-duplicate-title-qualification/v1",
        "qualified": True, "image_id": image, "controls": len(cases),
        "source_scaffold_sha256": digest(fixture / "page.html"),
        "runner_sha256": digest(runner), "cases": cases,
        "qualifier_sha256": digest(fixture / "qualify.py"),
    }
    (destination / "qualification.json").write_text(json.dumps(evidence, indent=2) + "\n")
    inventory = {p.relative_to(destination).as_posix(): digest(p)
                 for p in sorted(destination.rglob("*")) if p.is_file()}
    (destination / "receipt.json").write_text(json.dumps({
        "schema_version": "kanboard-duplicate-title-qualification-receipt/v1",
        "files": inventory,
    }, indent=2) + "\n")
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(qualify(args.image, args.output), indent=2))
