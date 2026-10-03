"""Qualify and classify the zulip-resolved-notice-auto-read browser endpoint (generated, do not edit)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import uuid

SCHEMA = "zulip-resolved-notice-auto-read-browser/v1"
TARGET = set(["notice_read_when_enabled_1", "notice_read_when_enabled_2", "notice_unread_when_disabled_1", "notice_unread_when_disabled_2"])
NON_TARGET = set(["notice_posted_for_each_change_1", "notice_posted_for_each_change_2", "other_messages_unchanged_1", "other_messages_unchanged_2", "topic_state_toggled_1", "topic_state_toggled_2"])
SCREENSHOTS = ["fixture-1.png", "fixture-2.png"]
MARKER = "/* MODEL_BEHAVIOR */"
CONTROLS = {
    "accessible-switch": ("const box=el('button',{type:'button',role:'switch','aria-checked':String(app.setting('autoReadResolvedNotices')===true)},'Read topic events automatically');document.querySelector('#settings').append(box);box.addEventListener('click',()=>{const next=box.getAttribute('aria-checked')!=='true';box.setAttribute('aria-checked',String(next));app.saveSetting('autoReadResolvedNotices',next)});app.onResolve(t=>{const r=!t.resolved;app.setResolved(t.id,r);const id=app.sendNotice(t.id,'@'+app.user().name+' has marked this topic as '+(r?'resolved':'unresolved')+'.');if(app.setting('autoReadResolvedNotices')===true)app.markAsRead(id)});", "pass"),
    "renamed-setting": ("const box=el('input',{type:'checkbox',id:'auto-read-resolved'});box.checked=app.setting('autoReadResolvedNotices')===true;const label=el('label');label.append(box,' Read topic status updates automatically');document.querySelector('#settings').append(label);box.addEventListener('change',()=>app.saveSetting('autoReadResolvedNotices',box.checked));app.onResolve(t=>{const r=!t.resolved;app.setResolved(t.id,r);const id=app.sendNotice(t.id,'@'+app.user().name+' has marked this topic as '+(r?'resolved':'unresolved')+'.');if(app.setting('autoReadResolvedNotices')===true)app.markAsRead(id)});", "pass"),
    "reference": ("const box=el('input',{type:'checkbox',id:'auto-read-resolved'});box.checked=app.setting('autoReadResolvedNotices')===true;const label=el('label');label.append(box,' Automatically mark resolved topic notices as read');document.querySelector('#settings').append(label);box.addEventListener('change',()=>app.saveSetting('autoReadResolvedNotices',box.checked));app.onResolve(t=>{const r=!t.resolved;app.setResolved(t.id,r);const id=app.sendNotice(t.id,'@'+app.user().name+' has marked this topic as '+(r?'resolved':'unresolved')+'.');if(app.setting('autoReadResolvedNotices')===true)app.markAsRead(id)});", "pass"),
    "alternative-select": ("var s=el('select',{id:'resolved-read'});[['always','Always'],['except_followed','Except for topics I follow'],['never','Never']].forEach(function(o){s.append(el('option',{value:o[0]},o[1]))});s.value=app.setting('resolvedNoticesRead')||'never';var l=el('label',{},'Automatically mark resolved topic notices as read ');l.append(s);document.querySelector('#settings').append(l);s.addEventListener('change',function(){app.saveSetting('resolvedNoticesRead',s.value)});app.onResolve(function(t){app.setResolved(t.id,!t.resolved);var id=app.sendNotice(t.id,'Topic '+(t.resolved?'unresolved':'resolved')+'.');if(app.setting('resolvedNoticesRead')==='always')app.markAsRead(id)});", "pass"),
    "target-mutant": ("app.onResolve(t=>{const r=!t.resolved;app.setResolved(t.id,r);app.sendNotice(t.id,'@'+app.user().name+' has marked this topic as '+(r?'resolved':'unresolved')+'.')});", "target_only_failure"),
    "always-read-mutant": ("app.onResolve(t=>{app.setResolved(t.id,!t.resolved);app.markAsRead(app.sendNotice(t.id,'Topic status changed.'))});", "target_only_failure"),
    "ignored-setting-mutant": ("const box=el('input',{type:'checkbox'});const label=el('label');label.append(box,' Automatically mark resolved topic notices as read');document.querySelector('#settings').append(label);app.onResolve(t=>{app.setResolved(t.id,!t.resolved);app.sendNotice(t.id,'Topic status changed.')});", "target_only_failure"),
    "non-target-mutant": ("const box=el('input',{type:'checkbox'});box.checked=app.setting('autoRead')===true;const label=el('label');label.append(box,' Automatically mark resolved topic notices as read');document.querySelector('#settings').append(label);box.addEventListener('change',()=>app.saveSetting('autoRead',box.checked));app.onResolve(t=>app.setResolved(t.id,!t.resolved));", "non_target_only_failure"),
    "mark-everything-mutant": ("const box=el('input',{type:'checkbox'});box.checked=app.setting('autoRead')===true;const label=el('label');label.append(box,' Automatically mark resolved topic notices as read');document.querySelector('#settings').append(label);box.addEventListener('change',()=>app.saveSetting('autoRead',box.checked));app.onResolve(t=>{app.setResolved(t.id,!t.resolved);app.sendNotice(t.id,'Topic status changed.');if(app.setting('autoRead'))app.messages().forEach(m=>{if(!m.read)app.markAsRead(m.id)})});", "non_target_only_failure"),
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
        command = ["docker", "run", "--rm", "--init", "--name", "zulip-resolved-notice-auto-read-" + uuid.uuid4().hex,
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
    evidence = {"schema_version": "zulip-resolved-notice-auto-read-qualification/v1", "qualified": True,
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
