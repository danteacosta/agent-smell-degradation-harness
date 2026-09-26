"""Fail-closed classification for the OpenProject Remaining work browser report."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import uuid


TARGET = {"remaining_6h", "remaining_15h"}
NON_TARGET = {"work_10h", "work_20h", "percent_40", "percent_25"}
SCREENSHOTS = ["fixture-1.png", "fixture-2.png"]


def classify(report: dict) -> str:
    if not isinstance(report, dict):
        return "malformed_report"
    if (
        report.get("schema_version") != "openproject-remaining-browser/v1"
        or re.fullmatch(r"[0-9a-f]{64}", str(report.get("app_sha256", ""))) is None
        or not isinstance(report.get("console_errors"), list)
        or len(report["console_errors"]) > 20
        or not all(
            isinstance(item, str) and len(item) <= 500
            for item in report["console_errors"]
        )
    ):
        return "malformed_report"
    if report.get("status") in {"interface_error", "browser_error"}:
        if (
            set(report)
            != {
                "schema_version", "status", "app_sha256", "assertions",
                "console_errors", "error",
            }
            or report["assertions"] != {}
            or not isinstance(report["error"], str)
            or len(report["error"]) > 1500
        ):
            return "malformed_report"
        return report["status"]
    if (
        report.get("status") != "complete"
        or set(report)
        != {
            "schema_version", "status", "app_sha256", "assertions",
            "console_errors", "screenshots",
        }
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
        "app.onSave(values=>({...values,remaining:String(Number(values.work)*(1-Number(values.percent)/100))}));",
        "pass",
    ),
    "alternative": (
        "app.onSave(function(values){const done=parseFloat(values.percent)/100;return {...values,remaining:String(parseFloat(values.work)-parseFloat(values.work)*done)}});",
        "pass",
    ),
    "target-mutant": ("app.onSave(values=>values);", "target_only_failure"),
    "non-target-mutant": (
        "app.onSave(values=>({...values,remaining:String(Number(values.work)*(1-Number(values.percent)/100)),percent:'0'}));",
        "non_target_only_failure",
    ),
    "duplicate-interface": (
        "document.querySelector('main').append(document.querySelector('[aria-label=\"Remaining work\"]').cloneNode());",
        "interface_error",
    ),
    "missing-behavior": ("", "target_only_failure"),
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
        "docker", "run", "--rm", "--init", "--name", "openproject-remaining-" + uuid.uuid4().hex,
        "--network", "none", "--user", f"{os.getuid()}:{os.getgid()}", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", "256", "--memory", "1g", "--cpus", "2",
        "--shm-size", "256m", "--tmpfs", "/tmp:rw,nosuid,size=256m",
        "--env", "HOME=/tmp",
        "--mount", f"type=bind,src={inputs.resolve()},dst=/input,readonly",
        "--mount", f"type=bind,src={output.resolve()},dst=/output", image,
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
    destination.mkdir(parents=True, exist_ok=False)
    rows = []
    for mode, (behavior, expected) in CONTROLS.items():
        root = destination / mode
        inputs, output = root / "input", root / "output"
        inputs.mkdir(parents=True)
        output.mkdir()
        (inputs / "app.html").write_text(assemble(scaffold, behavior), encoding="utf-8")
        result = subprocess.run(
            docker_command(image, inputs, output),
            capture_output=True, timeout=90, check=False,
        )
        (root / "stdout.bin").write_bytes(result.stdout)
        (root / "stderr.bin").write_bytes(result.stderr)
        report_path = output / "report.json"
        report = json.loads(report_path.read_text()) if report_path.is_file() else {}
        observed = classify(report)
        rows.append({
            "mode": mode, "expected": expected, "observed": observed,
            "returncode": result.returncode,
            "report_sha256": digest(report_path) if report_path.is_file() else None,
            "screenshots": {
                name: digest(output / name)
                for name in SCREENSHOTS if (output / name).is_file()
            },
        })
    qualified = all(row["expected"] == row["observed"] for row in rows)
    evidence = {
        "schema_version": "openproject-remaining-qualification/v1",
        "qualified": qualified,
        "image_id": image,
        "source_scaffold_sha256": digest(fixture / "page.html"),
        "runner_sha256": digest(fixture / "runner.cjs"),
        "controls": len(rows),
        "cases": rows,
        "limitations": "Authored control qualification only; no generated implementation or H1/H2 result.",
    }
    (destination / "qualification.json").write_text(json.dumps(evidence, indent=2) + "\n")
    files = {
        path.relative_to(destination).as_posix(): digest(path)
        for path in sorted(destination.rglob("*")) if path.is_file()
    }
    (destination / "receipt.json").write_text(json.dumps({
        "schema_version": "openproject-remaining-qualification-receipt/v1",
        "files": files,
    }, indent=2) + "\n")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    evidence = qualify(args.image, args.output)
    print(json.dumps({"qualified": evidence["qualified"], "controls": evidence["controls"]}))
    return 0 if evidence["qualified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
