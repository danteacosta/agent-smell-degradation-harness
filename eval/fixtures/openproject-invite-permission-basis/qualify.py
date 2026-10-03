"""Qualify and classify the openproject-invite-permission-basis browser endpoint (generated, do not edit)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import uuid

SCHEMA = "openproject-invite-permission-basis-browser/v1"
TARGET = set(["group_basis_selectable_1", "placeholder_basis_selectable_2"])
NON_TARGET = set(["existing_members_kept_1", "existing_members_kept_2", "existing_user_added_2", "new_user_invited_by_email_1"])
SCREENSHOTS = ["fixture-1.png", "fixture-2.png"]
MARKER = "/* MODEL_BEHAVIOR */"
CONTROLS = {
    "reference": ("const box=document.createElement('fieldset');box.append(el('legend',{},'Invite a'));for(const [v,l] of [['user','User'],['group','Group'],['placeholder_user','Placeholder user']]){const lab=el('label');const r=el('input',{type:'radio',name:'kind',value:v});r.checked=v==='user';lab.append(r,' '+l);box.append(lab)}document.querySelector('#invite-name').closest('label').before(box);app.onInvite(f=>{const kind=document.querySelector('input[name=kind]:checked').value;if(kind==='user'&&f.name.includes('@')){app.inviteByEmail(f.project,f.name,f.role);return}const p=app.principals().find(x=>x.kind===kind&&x.name===f.name);if(!p){app.showMessage('No '+kind+' named '+f.name);return}app.addMember(f.project,p.id,f.role)});", "pass"),
    "alternative": ("var sel=document.createElement('select');sel.id='principal-type';[['user','User'],['group','Group'],['placeholder_user','Placeholder user']].forEach(function(o){var op=document.createElement('option');op.value=o[0];op.textContent=o[1];sel.appendChild(op)});var lab=document.createElement('label');lab.textContent='Permissions based on ';lab.appendChild(sel);document.querySelector('#invite-project').parentNode.after(lab);app.onInvite(function(f){var kind=sel.value;var p=app.principals().filter(function(x){return x.kind===kind&&x.name.toLowerCase()===f.name.toLowerCase()})[0];if(p)app.addMember(f.project,p.id,f.role);else if(kind==='user'&&/@/.test(f.name))app.inviteByEmail(f.project,f.name,f.role);else app.showMessage('Not found')});", "pass"),
    "target-mutant": ("app.onInvite(f=>{if(f.name.includes('@')){app.inviteByEmail(f.project,f.name,f.role);return}const p=app.principals().find(x=>x.kind==='user'&&x.name===f.name);if(p)app.addMember(f.project,p.id,f.role);else app.showMessage('User not found')});", "target_only_failure"),
    "two-bases-mutant": ("const box=document.createElement('fieldset');for(const [v,l] of [['user','User'],['group','Group']]){const lab=el('label');const r=el('input',{type:'radio',name:'kind',value:v});r.checked=v==='user';lab.append(r,' '+l);box.append(lab)}document.querySelector('#invite-name').closest('label').before(box);app.onInvite(f=>{const kind=document.querySelector('input[name=kind]:checked').value;if(kind==='user'&&f.name.includes('@')){app.inviteByEmail(f.project,f.name,f.role);return}const p=app.principals().find(x=>x.kind===kind&&x.name===f.name);if(p)app.addMember(f.project,p.id,f.role)});", "target_only_failure"),
    "non-target-mutant": ("const box=document.createElement('fieldset');for(const [v,l] of [['user','User'],['group','Group'],['placeholder_user','Placeholder user']]){const lab=el('label');const r=el('input',{type:'radio',name:'kind',value:v});r.checked=v==='user';lab.append(r,' '+l);box.append(lab)}document.querySelector('#invite-name').closest('label').before(box);app.onInvite(f=>{const kind=document.querySelector('input[name=kind]:checked').value;if(kind==='user')return;const p=app.principals().find(x=>x.kind===kind&&x.name===f.name);if(p)app.addMember(f.project,p.id,f.role)});", "non_target_only_failure"),
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
        command = ["docker", "run", "--rm", "--init", "--name", "openproject-invite-permission-basis-" + uuid.uuid4().hex,
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
    evidence = {"schema_version": "openproject-invite-permission-basis-qualification/v1", "qualified": True,
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
