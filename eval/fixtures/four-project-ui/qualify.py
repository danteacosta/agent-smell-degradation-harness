"""Qualify four browser oracles against authored controls before generation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import uuid


PROJECT_ASSERTIONS = {
    "paperless-ngx": {
        "target": {"drop_creates_document"},
        "non_target": {"existing_document_visible", "upload_button_usable"},
    },
    "kanboard": {
        "target": {"subtask_todo-subtask_done", "subtask_progress-subtask_done"},
        "non_target": {
            "subtask_done-subtask_done", "closed_task_leaves_board",
            "unrelated_task_unchanged",
        },
    },
    "nextcloud": {
        "target": {"restore_returns_to_all"},
        "non_target": {"deleted_visible_in_trash", "deleted_absent_from_all", "unrelated_file_unchanged"},
    },
    "openproject": {
        "target": {"remaining_matches_work"},
        "non_target": {"work_preserved", "percent_zero"},
    },
}
MODES = {
    "reference": "pass",
    "alternative": "pass",
    "target-mutant": "target_only_failure",
    "non-target-mutant": "non_target_only_failure",
    "interface-ambiguous": "interface_error",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify(report: dict) -> str:
    if not isinstance(report, dict):
        return "malformed_report"
    project = report.get("project_id")
    if project not in PROJECT_ASSERTIONS:
        return "malformed_report"
    if (
        report.get("schema_version") != "four-project-ui-browser/v1"
        or re.fullmatch(r"[0-9a-f]{64}", str(report.get("app_sha256", ""))) is None
        or not isinstance(report.get("console_errors"), list)
        or len(report["console_errors"]) > 20
        or not all(isinstance(item, str) and len(item) <= 500 for item in report["console_errors"])
    ):
        return "malformed_report"
    if report.get("status") in {"interface_error", "browser_error"}:
        if (
            set(report) != {"schema_version", "project_id", "status", "app_sha256", "assertions", "console_errors", "error"}
            or report["assertions"] != {}
            or not isinstance(report.get("error"), str)
            or len(report["error"]) > 1500
        ):
            return "malformed_report"
        return report["status"]
    if (
        report.get("status") != "complete"
        or set(report) != {"schema_version", "project_id", "status", "app_sha256", "assertions", "console_errors", "screenshot"}
        or report.get("screenshot") != "final.png"
        or not isinstance(report.get("assertions"), dict)
    ):
        return "malformed_report"
    contract = PROJECT_ASSERTIONS[project]
    if set(report["assertions"]) != contract["target"] | contract["non_target"]:
        return "malformed_report"
    if not all(type(value) is bool for value in report["assertions"].values()):
        return "malformed_report"
    target = any(not report["assertions"][key] for key in contract["target"])
    non_target = any(not report["assertions"][key] for key in contract["non_target"])
    if target and non_target:
        return "mixed_failure"
    if target:
        return "target_only_failure"
    if non_target:
        return "non_target_only_failure"
    return "pass"


def docker_command(image: str, inputs: Path, output: Path) -> list[str]:
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image):
        raise ValueError("immutable Docker image ID required")
    return [
        "docker", "run", "--rm", "--init", "--name", "four-project-ui-" + uuid.uuid4().hex,
        "--network", "none", "--user", f"{os.getuid()}:{os.getgid()}", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "256",
        "--memory", "1g", "--cpus", "2", "--shm-size", "256m",
        "--tmpfs", "/tmp:rw,nosuid,size=256m", "--env", "HOME=/tmp",
        "--mount", f"type=bind,src={inputs.resolve()},dst=/input,readonly",
        "--mount", f"type=bind,src={output.resolve()},dst=/output", image,
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    found = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", args.image],
        check=True, capture_output=True, text=True, timeout=30,
    ).stdout.strip()
    if found != args.image:
        raise ValueError("image identity mismatch")
    args.output.mkdir(parents=True, exist_ok=False)
    fixture = Path(__file__).resolve().parent
    rows = []
    for project in PROJECT_ASSERTIONS:
        for mode, expected in MODES.items():
            root = args.output / project / mode
            inputs = root / "input"
            output = root / "output"
            inputs.mkdir(parents=True)
            output.mkdir()
            (inputs / "app.html").write_bytes((fixture / "control.html").read_bytes())
            (inputs / "case.json").write_text(
                json.dumps({"project_id": project, "mode": mode}) + "\n", encoding="utf-8"
            )
            command = docker_command(args.image, inputs, output)
            result = subprocess.run(command, capture_output=True, timeout=90, check=False)
            report_path = output / "report.json"
            raw = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else {}
            observed = classify(raw)
            rows.append({
                "project_id": project, "mode": mode, "expected": expected,
                "observed": observed, "returncode": result.returncode,
                "report_sha256": digest(report_path) if report_path.is_file() else None,
                "screenshot_sha256": digest(output / "final.png") if (output / "final.png").is_file() else None,
            })
    qualified = all(row["expected"] == row["observed"] for row in rows)
    evidence = {
        "schema_version": "four-project-ui-qualification/v1",
        "qualified": qualified,
        "image_id": args.image,
        "cases": rows,
        "controls": len(rows),
        "project_count": len(PROJECT_ASSERTIONS),
        "limitations": "Authored controls qualify bounded replica oracles; no generated artifact or H1/H2 result.",
    }
    (args.output / "qualification.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"qualified": qualified, "controls": len(rows)}))
    return 0 if qualified else 1


if __name__ == "__main__":
    raise SystemExit(main())
