"""Qualify and classify the zulip-reverse-linkifier-paste browser endpoint (generated, do not edit)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import uuid

SCHEMA = "zulip-reverse-linkifier-paste-browser/v1"
TARGET = set(["pasted_url_converted_1", "pasted_url_converted_2", "unmatched_paste_kept_1", "unmatched_paste_kept_2"])
NON_TARGET = set(["one_message_per_send_1", "one_message_per_send_2", "typed_reference_linked_1", "typed_reference_linked_2"])
SCREENSHOTS = ["fixture-1.png", "fixture-2.png"]
MARKER = "/* MODEL_BEHAVIOR */"
CONTROLS = {
    "converted-text-without-link": ("let wasPaste=false;document.querySelector('#compose').addEventListener('paste',()=>{wasPaste=true});const LK=app.linkifiers();const esc=s=>s.replace(/[.*+?^${}()|[\\]\\\\]/g,'\\\\$&');const fill=(t,g)=>t.replace(/\\{(\\w+)\\}/g,(_,k)=>g[k]);\nconst REV=LK.filter(l=>l.linkText).map(l=>{const names=[];const src='^'+l.urlTemplate.split(/(\\{\\w+\\})/).map(p=>{const m=/^\\{(\\w+)\\}$/.exec(p);if(m){names.push(m[1]);return '([^/?#&]+)'}return esc(p)}).join('')+'$';return {re:new RegExp(src),names,l}});\ndocument.querySelector('#compose').addEventListener('paste',e=>{const t=(e.clipboardData.getData('text/plain')||'').trim();for(const r of REV){const m=r.re.exec(t);if(m){e.preventDefault();const g={};r.names.forEach((k,i)=>g[k]=decodeURIComponent(m[i+1]));const box=e.target;box.setRangeText(fill(r.l.linkText,g),box.selectionStart,box.selectionEnd,'end');return}}});\napp.onSend(text=>{const parts=[];let i=0;const rules=LK.map(l=>({re:new RegExp(l.pattern,'g'),l}));while(i<text.length){let best=null;for(const r of rules){r.re.lastIndex=i;const m=r.re.exec(text);if(m&&m[0]&&(!best||m.index<best.m.index))best={m,l:r.l}}if(!best){parts.push({text:text.slice(i)});break}if(best.m.index>i)parts.push({text:text.slice(i,best.m.index)});const g={};for(const [k,v] of Object.entries(best.m.groups||{}))g[k]=encodeURIComponent(v);parts.push({text:best.m[0],href:fill(best.l.urlTemplate,g)});i=best.m.index+best.m[0].length}if(parts.length)app.sendMessage(wasPaste?parts.map(p=>({text:p.text})):parts);wasPaste=false});", "target_only_failure"),
    "reference": ("const LK=app.linkifiers();const esc=s=>s.replace(/[.*+?^${}()|[\\]\\\\]/g,'\\\\$&');const fill=(t,g)=>t.replace(/\\{(\\w+)\\}/g,(_,k)=>g[k]);\nconst REV=LK.filter(l=>l.linkText).map(l=>{const names=[];const src='^'+l.urlTemplate.split(/(\\{\\w+\\})/).map(p=>{const m=/^\\{(\\w+)\\}$/.exec(p);if(m){names.push(m[1]);return '([^/?#&]+)'}return esc(p)}).join('')+'$';return {re:new RegExp(src),names,l}});\ndocument.querySelector('#compose').addEventListener('paste',e=>{const t=(e.clipboardData.getData('text/plain')||'').trim();for(const r of REV){const m=r.re.exec(t);if(m){e.preventDefault();const g={};r.names.forEach((k,i)=>g[k]=decodeURIComponent(m[i+1]));const box=e.target;box.setRangeText(fill(r.l.linkText,g),box.selectionStart,box.selectionEnd,'end');return}}});\napp.onSend(text=>{const parts=[];let i=0;const rules=LK.map(l=>({re:new RegExp(l.pattern,'g'),l}));while(i<text.length){let best=null;for(const r of rules){r.re.lastIndex=i;const m=r.re.exec(text);if(m&&m[0]&&(!best||m.index<best.m.index))best={m,l:r.l}}if(!best){parts.push({text:text.slice(i)});break}if(best.m.index>i)parts.push({text:text.slice(i,best.m.index)});const g={};for(const [k,v] of Object.entries(best.m.groups||{}))g[k]=encodeURIComponent(v);parts.push({text:best.m[0],href:fill(best.l.urlTemplate,g)});i=best.m.index+best.m[0].length}if(parts.length)app.sendMessage(parts)});", "pass"),
    "convert-on-send": ("function linkify(text){var LK=app.linkifiers(),parts=[],i=0;while(i<text.length){var best=null,bl=null;LK.forEach(function(l){var re=new RegExp(l.pattern,'g');re.lastIndex=i;var m=re.exec(text);if(m&&m[0]&&(!best||m.index<best.index)){best=m;bl=l}});if(!best){parts.push({text:text.slice(i)});break}if(best.index>i)parts.push({text:text.slice(i,best.index)});parts.push({text:best[0],href:bl.urlTemplate.replace(/\\{(\\w+)\\}/g,function(_,k){return encodeURIComponent(best.groups[k])})});i=best.index+best[0].length}return parts}\nfunction reverse(text){return text.replace(/https?:\\/\\/\\S+/g,function(url){var out=url;app.linkifiers().some(function(l){if(!l.linkText)return false;var names=[];var src=l.urlTemplate.replace(/[.*+?^$()|[\\]\\\\]/g,'\\\\$&').replace(/\\{(\\w+)\\}/g,function(_,k){names.push(k);return '([^/?#&]+)'});var m=new RegExp('^'+src+'$').exec(url);if(!m)return false;out=l.linkText.replace(/\\{(\\w+)\\}/g,function(_,k){return m[names.indexOf(k)+1]});return true});return out})}\napp.onSend(function(text){if(text.trim())app.sendMessage(linkify(reverse(text)))});", "target_only_failure"),
    "input-event": ("const LK=app.linkifiers();function rev(url){for(const l of LK){if(!l.linkText)continue;const names=[];const src=l.urlTemplate.replace(/[.*+?^$()|[\\]\\\\]/g,'\\\\$&').replace(/\\{(\\w+)\\}/g,(_,k)=>{names.push(k);return '([^/?#&]+)'});const m=new RegExp('^'+src+'$').exec(url);if(m)return l.linkText.replace(/\\{(\\w+)\\}/g,(_,k)=>m[names.indexOf(k)+1])}return null}\ndocument.querySelector('#compose').addEventListener('input',e=>{if(e.inputType!=='insertFromPaste')return;const box=e.target;box.value=box.value.replace(/https?:\\/\\/\\S+/g,u=>rev(u)??u)});\napp.onSend(text=>{const parts=[];let rest=text;while(rest){let best=null;for(const l of LK){const m=new RegExp(l.pattern).exec(rest);if(m&&m[0]&&(!best||m.index<best.m.index))best={m,l}}if(!best){parts.push({text:rest});break}if(best.m.index)parts.push({text:rest.slice(0,best.m.index)});parts.push({text:best.m[0],href:best.l.urlTemplate.replace(/\\{(\\w+)\\}/g,(_,k)=>encodeURIComponent(best.m.groups[k]))});rest=rest.slice(best.m.index+best.m[0].length)}app.sendMessage(parts)});", "pass"),
    "target-mutant": ("const LK=app.linkifiers();app.onSend(text=>{const parts=[];let rest=text;while(rest){let best=null;for(const l of LK){const m=new RegExp(l.pattern).exec(rest);if(m&&m[0]&&(!best||m.index<best.m.index))best={m,l}}if(!best){parts.push({text:rest});break}if(best.m.index)parts.push({text:rest.slice(0,best.m.index)});parts.push({text:best.m[0],href:best.l.urlTemplate.replace(/\\{(\\w+)\\}/g,(_,k)=>encodeURIComponent(best.m.groups[k]))});rest=rest.slice(best.m.index+best.m[0].length)}app.sendMessage(parts)});", "target_only_failure"),
    "unlinked-message-mutant": ("const LK=app.linkifiers();function rev(url){for(const l of LK){if(!l.linkText)continue;const names=[];const src=l.urlTemplate.replace(/[.*+?^$()|[\\]\\\\]/g,'\\\\$&').replace(/\\{(\\w+)\\}/g,(_,k)=>{names.push(k);return '([^/?#&]+)'});const m=new RegExp('^'+src+'$').exec(url);if(m)return l.linkText.replace(/\\{(\\w+)\\}/g,(_,k)=>m[names.indexOf(k)+1])}return null}\ndocument.querySelector('#compose').addEventListener('paste',e=>{const t=e.clipboardData.getData('text/plain').trim();const r=rev(t);if(r!==null){e.preventDefault();e.target.setRangeText(r,e.target.selectionStart,e.target.selectionEnd,'end')}});\napp.onSend(text=>app.sendMessage([{text}]));", "mixed_failure"),
    "non-target-mutant": ("let wasPaste=false;document.querySelector('#compose').addEventListener('paste',()=>{wasPaste=true});const LK=app.linkifiers();const esc=s=>s.replace(/[.*+?^${}()|[\\]\\\\]/g,'\\\\$&');const fill=(t,g)=>t.replace(/\\{(\\w+)\\}/g,(_,k)=>g[k]);\nconst REV=LK.filter(l=>l.linkText).map(l=>{const names=[];const src='^'+l.urlTemplate.split(/(\\{\\w+\\})/).map(p=>{const m=/^\\{(\\w+)\\}$/.exec(p);if(m){names.push(m[1]);return '([^/?#&]+)'}return esc(p)}).join('')+'$';return {re:new RegExp(src),names,l}});\ndocument.querySelector('#compose').addEventListener('paste',e=>{const t=(e.clipboardData.getData('text/plain')||'').trim();for(const r of REV){const m=r.re.exec(t);if(m){e.preventDefault();const g={};r.names.forEach((k,i)=>g[k]=decodeURIComponent(m[i+1]));const box=e.target;box.setRangeText(fill(r.l.linkText,g),box.selectionStart,box.selectionEnd,'end');return}}});\napp.onSend(text=>{const parts=[];let i=0;const rules=LK.map(l=>({re:new RegExp(l.pattern,'g'),l}));while(i<text.length){let best=null;for(const r of rules){r.re.lastIndex=i;const m=r.re.exec(text);if(m&&m[0]&&(!best||m.index<best.m.index))best={m,l:r.l}}if(!best){parts.push({text:text.slice(i)});break}if(best.m.index>i)parts.push({text:text.slice(i,best.m.index)});const g={};for(const [k,v] of Object.entries(best.m.groups||{}))g[k]=encodeURIComponent(v);parts.push({text:best.m[0],href:fill(best.l.urlTemplate,g)});i=best.m.index+best.m[0].length}if(parts.length)app.sendMessage(wasPaste?parts:parts.map(p=>({text:p.text})));wasPaste=false});", "non_target_only_failure"),
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
        command = ["docker", "run", "--rm", "--init", "--name", "zulip-reverse-linkifier-paste-" + uuid.uuid4().hex,
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
    evidence = {"schema_version": "zulip-reverse-linkifier-paste-qualification/v1", "qualified": True,
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
