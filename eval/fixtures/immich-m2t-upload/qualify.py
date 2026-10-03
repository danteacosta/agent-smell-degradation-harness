"""Qualify and classify the immich-m2t-upload browser endpoint (generated, do not edit)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import uuid

SCHEMA = "immich-m2t-upload-browser/v1"
TARGET = set(["m2t_accepted_1", "m2t_accepted_2"])
NON_TARGET = set(["each_file_decided_once_1", "each_file_decided_once_2", "non_video_rejected_1", "non_video_rejected_2", "other_video_accepted_1", "other_video_accepted_2"])
SCREENSHOTS = ["fixture-1.png", "fixture-2.png"]
MARKER = "/* MODEL_BEHAVIOR */"
CONTROLS = {
    "ts-missing-mutant": ("const VIDEO=['.3gp','.3gpp','.avi','.flv','.m4v','.mkv','.mts','.m2ts','.m2t','.mp4','.insv','.mpg','.mpe','.mpeg','.mov','.webm','.wmv'];app.onFiles(files=>{for(const f of files){const ext=f.name.slice(f.name.lastIndexOf('.')).toLowerCase();if(VIDEO.includes(ext))app.accept(f.name);else app.reject(f.name,'Unsupported file type')}});", "non_target_only_failure"),
    "reference": ("const VIDEO=['.3gp','.3gpp','.avi','.flv','.m4v','.mkv','.mts','.m2ts','.ts','.m2t','.mp4','.insv','.mpg','.mpe','.mpeg','.mov','.webm','.wmv'];app.onFiles(files=>{for(const f of files){const ext=f.name.slice(f.name.lastIndexOf('.')).toLowerCase();if(VIDEO.includes(ext))app.accept(f.name);else app.reject(f.name,'Unsupported file type')}});", "pass"),
    "alternative": ("app.onFiles(function(files){files.forEach(function(f){if(/\\.(3gpp?|avi|flv|m4v|mkv|mts|m2ts?|ts|mp4|insv|mp(g|e|eg)|mov|webm|wmv)$/i.test(f.name))app.accept(f.name);else app.reject(f.name)})});", "pass"),
    "target-mutant": ("const VIDEO=['.3gp','.3gpp','.avi','.flv','.m4v','.mkv','.mts','.m2ts','.ts','.mp4','.insv','.mpg','.mpe','.mpeg','.mov','.webm','.wmv'];app.onFiles(files=>{for(const f of files){const ext=f.name.slice(f.name.lastIndexOf('.')).toLowerCase();if(VIDEO.includes(ext))app.accept(f.name);else app.reject(f.name)}});", "target_only_failure"),
    "mime-mutant": ("app.onFiles(files=>files.forEach(f=>f.type.startsWith('video/')?app.accept(f.name):app.reject(f.name)));", "target_only_failure"),
    "non-target-mutant": ("app.onFiles(files=>files.forEach(f=>app.accept(f.name)));", "non_target_only_failure"),
    "missing-handler": ("", "interface_error"),
    "script-error": ("throw new Error('qualification control');", "browser_error"),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify(report: dict) -> str:
    if not isinstance(report, dict) or report.get("schema_version") != SCHEMA:
        return "malformed_report"
    if re.fullmatch(r"[0-9a-f]{64}", str(report.get("app_sha256", ""))) is None:
        return "malformed_report"
    errors = report.get("console_errors")
    if not isinstance(errors, list) or len(errors) > 20 or not all(
            isinstance(item, str) and len(item) <= 500 for item in errors):
        return "malformed_report"
    if report.get("status") in ("interface_error", "browser_error"):
        if (set(report) != {"schema_version", "status", "app_sha256", "assertions", "console_errors", "error"}
                or report["assertions"] != {} or not isinstance(report["error"], str)
                or len(report["error"]) > 1500):
            return "malformed_report"
        return report["status"]
    if (report.get("status") != "complete"
            or set(report) != {"schema_version", "status", "app_sha256", "assertions", "console_errors", "screenshots"}
            or report.get("screenshots") != SCREENSHOTS):
        return "malformed_report"
    assertions = report.get("assertions")
    if (not isinstance(assertions, dict) or set(assertions) != TARGET | NON_TARGET
            or any(type(value) is not bool for value in assertions.values())):
        return "malformed_report"
    if errors:
        return "browser_error"
    target_failed = any(not assertions[key] for key in TARGET)
    control_failed = any(not assertions[key] for key in NON_TARGET)
    if target_failed and control_failed:
        return "mixed_failure"
    if target_failed:
        return "target_only_failure"
    if control_failed:
        return "non_target_only_failure"
    return "pass"


def qualify(image: str, destination: Path) -> dict:
    found = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", image],
                           capture_output=True, text=True, check=True, timeout=30).stdout.strip()
    if found != image:
        raise ValueError("image identity mismatch")
    fixture = Path(__file__).resolve().parent
    page = (fixture / "page.html").read_text()
    if page.count(MARKER) != 1:
        raise ValueError("one behavior marker required")
    destination.mkdir(parents=True, exist_ok=False)
    cases = []
    for mode, (behavior, expected) in CONTROLS.items():
        root = destination / mode
        inputs, output = root / "input", root / "output"
        inputs.mkdir(parents=True)
        output.mkdir()
        (inputs / "app.html").write_text(page.replace(MARKER, behavior))
        (inputs / "runner.cjs").write_bytes((fixture / "runner.cjs").read_bytes())
        command = ["docker", "run", "--rm", "--init", "--name", "immich-m2t-upload-" + uuid.uuid4().hex,
                   "--network", "none", "--user", f"{os.getuid()}:{os.getgid()}", "--read-only",
                   "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "256",
                   "--memory", "1g", "--cpus", "2", "--shm-size", "256m",
                   "--tmpfs", "/tmp:rw,nosuid,size=256m", "--env", "HOME=/tmp",
                   "--env", "NODE_PATH=/opt/openproject-remaining-pilot/node_modules",
                   "--mount", f"type=bind,src={inputs.resolve()},dst=/input,readonly",
                   "--mount", f"type=bind,src={output.resolve()},dst=/output",
                   "--entrypoint", "node", image, "/input/runner.cjs"]
        process = subprocess.run(command, capture_output=True, timeout=120, check=False)
        (root / "stdout.bin").write_bytes(process.stdout)
        (root / "stderr.bin").write_bytes(process.stderr)
        report_path = output / "report.json"
        report = json.loads(report_path.read_text()) if report_path.is_file() else {}
        observed = classify(report)
        if observed != expected:
            raise ValueError(f"{mode}: expected {expected}, got {observed}; stderr={process.stderr[-500:]!r}; report={report}")
        if (process.returncode == 0) != (report.get("status") == "complete"):
            raise ValueError(f"{mode}: return code disagrees with report")
        if report.get("app_sha256") != digest(inputs / "app.html"):
            raise ValueError(f"{mode}: app digest mismatch")
        if report.get("status") == "complete":
            for name in SCREENSHOTS:
                path = output / name
                if not path.is_file() or not path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
                    raise ValueError(f"{mode}: screenshot missing")
        cases.append({"mode": mode, "expected": expected, "observed": observed,
                      "report_sha256": digest(report_path)})
    evidence = {"schema_version": "immich-m2t-upload-qualification/v1", "qualified": True,
                "image_id": image, "controls": len(cases), "source_scaffold_sha256": digest(fixture / "page.html"),
                "runner_sha256": digest(fixture / "runner.cjs"), "qualifier_sha256": digest(fixture / "qualify.py"),
                "cases": cases}
    (destination / "qualification.json").write_text(json.dumps(evidence, indent=2) + "\n")
    files = {p.relative_to(destination).as_posix(): digest(p) for p in sorted(destination.rglob("*")) if p.is_file()}
    (destination / "receipt.json").write_text(json.dumps({"files": files}, indent=2) + "\n")
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(qualify(args.image, args.output), indent=2))
