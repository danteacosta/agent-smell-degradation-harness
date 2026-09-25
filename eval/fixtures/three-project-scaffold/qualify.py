"""Qualify fixed-scaffold browser oracles against authored controls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import uuid


PLACEHOLDER = "/* MODEL_BEHAVIOR */"
PROJECT_ASSERTIONS = {
    "paperless-ngx": {
        "target": {"drop_creates_document"},
        "non_target": {"existing_document_visible", "upload_creates_document"},
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
    "missing-behavior": "mixed_failure",
}
LOGIC = {
    "paperless-ngx": {
        "reference": "app.register('upload',file=>app.addDocument(file));app.register('page-drop',file=>app.addDocument(file));",
        "alternative": "function accept(file){app.addDocument(file)} app.register('page-drop',accept);app.register('upload',accept);",
        "target-mutant": "app.register('upload',file=>app.addDocument(file));",
        "non-target-mutant": "app.register('page-drop',file=>app.addDocument(file));",
        "interface-ambiguous": "app.register('upload',file=>app.addDocument(file));app.register('page-drop',file=>app.addDocument(file));setTimeout(()=>document.querySelector('#documents').append(document.querySelector('[data-document-id]').cloneNode(true)),0);",
        "missing-behavior": "",
    },
    "nextcloud": {
        "reference": "app.register('delete',id=>app.moveToTrash(id));app.register('restore',id=>app.restore(id));",
        "alternative": "const act={delete:id=>app.moveToTrash(id),restore:id=>app.restore(id)};for(const [name,fn] of Object.entries(act))app.register(name,fn);",
        "target-mutant": "app.register('delete',id=>app.moveToTrash(id));",
        "non-target-mutant": "app.register('delete',id=>{app.moveToTrash(id);app.moveToTrash('file-control')});app.register('restore',id=>app.restore(id));",
        "interface-ambiguous": "app.register('delete',id=>app.moveToTrash(id));app.register('restore',id=>app.restore(id));setTimeout(()=>document.querySelector('#files').append(document.querySelector('[data-file-id]').cloneNode(true)),0);",
        "missing-behavior": "",
    },
    "openproject": {
        "reference": "app.onSave(values=>({...values,remaining:values.work,percent:'0%'}));",
        "alternative": "app.onSave(function(values){values.remaining=values.work;values.percent='0';return values});",
        "target-mutant": "app.onSave(values=>({...values,percent:'0%'}));",
        "non-target-mutant": "app.onSave(values=>({...values,remaining:values.work,percent:'50%'}));",
        "interface-ambiguous": "app.onSave(values=>({...values,remaining:values.work,percent:'0%'}));document.querySelector('main').append(document.querySelector('[aria-label=\"Remaining Work\"]').cloneNode());",
        "missing-behavior": "",
    },
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify(report: dict) -> str:
    if not isinstance(report, dict) or report.get("project_id") not in PROJECT_ASSERTIONS:
        return "malformed_report"
    if (
        report.get("schema_version") != "three-project-fixed-scaffold-browser/v1"
        or re.fullmatch(r"[0-9a-f]{64}", str(report.get("app_sha256", ""))) is None
        or not isinstance(report.get("console_errors"), list)
        or len(report["console_errors"]) > 20
        or not all(isinstance(item, str) and len(item) <= 500 for item in report["console_errors"])
    ):
        return "malformed_report"
    if report.get("status") in {"interface_error", "browser_error"}:
        if set(report) != {"schema_version", "project_id", "status", "app_sha256", "assertions", "console_errors", "error"} or report["assertions"] != {}:
            return "malformed_report"
        return report["status"]
    if (
        report.get("status") != "complete"
        or set(report) != {"schema_version", "project_id", "status", "app_sha256", "assertions", "console_errors", "screenshot"}
        or report.get("screenshot") != "final.png"
    ):
        return "malformed_report"
    contract = PROJECT_ASSERTIONS[report["project_id"]]
    assertions = report.get("assertions")
    if not isinstance(assertions, dict) or set(assertions) != contract["target"] | contract["non_target"] or not all(type(value) is bool for value in assertions.values()):
        return "malformed_report"
    target = any(not assertions[key] for key in contract["target"])
    non_target = any(not assertions[key] for key in contract["non_target"])
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
        "docker", "run", "--rm", "--init", "--name", "three-project-scaffold-" + uuid.uuid4().hex,
        "--network", "none", "--user", f"{os.getuid()}:{os.getgid()}", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "256",
        "--memory", "1g", "--cpus", "2", "--shm-size", "256m",
        "--tmpfs", "/tmp:rw,nosuid,size=256m", "--env", "HOME=/tmp",
        "--mount", f"type=bind,src={inputs.resolve()},dst=/input,readonly",
        "--mount", f"type=bind,src={output.resolve()},dst=/output", image,
    ]


def assemble(scaffold: str, logic: str) -> str:
    if scaffold.count(PLACEHOLDER) != 1:
        raise ValueError("scaffold marker mismatch")
    return scaffold.replace(PLACEHOLDER, logic)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    found = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", args.image], check=True, capture_output=True, text=True, timeout=30).stdout.strip()
    if found != args.image:
        raise ValueError("image identity mismatch")
    args.output.mkdir(parents=True, exist_ok=False)
    fixture = Path(__file__).resolve().parent
    rows = []
    for project in PROJECT_ASSERTIONS:
        scaffold = (fixture / f"{project}.html").read_text()
        for mode, expected in MODES.items():
            root = args.output / project / mode
            inputs, output = root / "input", root / "output"
            inputs.mkdir(parents=True)
            output.mkdir()
            (inputs / "app.html").write_text(assemble(scaffold, LOGIC[project][mode]))
            (inputs / "case.json").write_text(json.dumps({"project_id": project}) + "\n")
            result = subprocess.run(docker_command(args.image, inputs, output), capture_output=True, timeout=90, check=False)
            report_path = output / "report.json"
            raw = json.loads(report_path.read_text()) if report_path.is_file() else {}
            observed = classify(raw)
            rows.append({
                "project_id": project, "mode": mode, "expected": expected, "observed": observed,
                "returncode": result.returncode,
                "report_sha256": digest(report_path) if report_path.is_file() else None,
                "screenshot_sha256": digest(output / "final.png") if (output / "final.png").is_file() else None,
            })
    qualified = all(row["expected"] == row["observed"] for row in rows)
    evidence = {
        "schema_version": "three-project-fixed-scaffold-qualification/v1",
        "qualified": qualified,
        "image_id": args.image,
        "controls": len(rows),
        "project_count": len(PROJECT_ASSERTIONS),
        "cases": rows,
        "limitations": "Authored controls qualify bounded fixed-scaffold oracles; no provider call or H1/H2 result.",
    }
    (args.output / "qualification.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"qualified": qualified, "controls": len(rows)}))
    return 0 if qualified else 1


if __name__ == "__main__":
    raise SystemExit(main())
