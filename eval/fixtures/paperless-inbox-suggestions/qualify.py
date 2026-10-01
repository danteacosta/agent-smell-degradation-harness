"""Fail-closed browser classification and authored controls for inbox suggestions."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

SCHEMA = "paperless-inbox-suggestions-browser/v1"
TARGET = {f"{name}_{index}" for index in (1, 2)
          for name in ("request_once", "suggestion_visible")}
NON_TARGET = {f"{name}_{index}" for index in (1, 2)
              for name in ("document_title", "document_id", "suggest_button")}
SCREENSHOTS = ["fixture-1.png", "fixture-2.png"]


def classify(report: dict) -> str:
    if not isinstance(report, dict) or report.get("schema_version") != SCHEMA:
        return "malformed_report"
    if re.fullmatch(r"[0-9a-f]{64}", str(report.get("app_sha256", ""))) is None:
        return "malformed_report"
    errors = report.get("console_errors")
    if (not isinstance(errors, list) or len(errors) > 20
            or not all(isinstance(item, str) and len(item) <= 500 for item in errors)):
        return "malformed_report"
    if report.get("status") in ("interface_error", "browser_error"):
        if (set(report) != {"schema_version", "status", "app_sha256", "assertions", "console_errors", "error"}
                or report.get("assertions") != {} or not isinstance(report.get("error"), str)
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
    neutral_failed = any(not assertions[key] for key in NON_TARGET)
    if target_failed and neutral_failed:
        return "mixed_failure"
    if target_failed:
        return "target_only_failure"
    if neutral_failed:
        return "non_target_only_failure"
    return "pass"


PAGE = Path(__file__).with_name("page.html")
RUNNER = Path(__file__).with_name("runner.cjs")
MARKER = "/* MODEL_BEHAVIOR */"
REQUEST = "app.onView(()=>{const doc=app.document();if(doc.tags.includes('inbox'))app.requestSuggestions(doc.id)})"
CONTROLS = {
    "reference": (REQUEST, "pass"),
    "alternative": ("app.onView(function(){let d=app.document();if(d.tags.indexOf('inbox')>=0){app.requestSuggestions(d.id)}})", "pass"),
    "no-request": ("app.onView(()=>{})", "target_only_failure"),
    "manual-only": ("app.onView(()=>document.querySelector('#suggest-button').addEventListener('click',()=>app.requestSuggestions(app.document().id)))", "target_only_failure"),
    "fake-chip": ("app.onView(()=>{const d=app.document();const li=document.createElement('li');li.dataset.suggestionId=d.id==='doc-41'?'tag-7':'tag-9';li.textContent=d.id==='doc-41'?'Taxes':'Travel';document.querySelector('#suggestions').append(li)})", "target_only_failure"),
    "double-request": ("app.onView(()=>{app.requestSuggestions(app.document().id);app.requestSuggestions(app.document().id)})", "target_only_failure"),
    "wrong-id": ("app.onView(()=>app.requestSuggestions('wrong-id'))", "browser_error"),
    "wrong-suggestion": (REQUEST + ";document.querySelector('#suggestions li').textContent='Wrong'", "target_only_failure"),
    "wrong-title": (REQUEST + ";document.querySelector('#document-title').textContent='Wrong'", "non_target_only_failure"),
    "hidden-button": (REQUEST + ";document.querySelector('#suggest-button').hidden=true", "interface_error"),
    "hidden-area": (REQUEST + ";document.querySelector('#suggestions').hidden=true", "interface_error"),
    "script-error": ("throw new Error('authored control')", "browser_error"),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def qualify(image: str, destination: Path) -> dict:
    repository = Path(__file__).resolve().parents[3]
    if str(repository) not in sys.path:
        sys.path.insert(0, str(repository))
    from scripts.kanboard_duplicate_collect import execute

    found = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", image],
                           capture_output=True, text=True, check=True, timeout=30).stdout.strip()
    if found != image:
        raise ValueError("browser image identity mismatch")
    page = PAGE.read_text()
    if page.count(MARKER) != 1 or destination.exists():
        raise ValueError("one marker and fresh destination required")
    destination.mkdir(mode=0o700, parents=True)
    rows = []
    for name, (script, expected) in CONTROLS.items():
        root = destination / name
        inputs = root / "input"
        inputs.mkdir(parents=True)
        (inputs / "app.html").write_text(page.replace(MARKER, script))
        result = execute(image, inputs, root / "output", RUNNER, Path(__file__))
        rows.append({"name": name, "expected": expected, "observed": result["category"],
                     "report_sha256": result.get("report_sha256")})
        print(json.dumps(rows[-1]), flush=True)
        if result["category"] != expected:
            raise ValueError(f"{name}: expected {expected}, got {result['category']}")
    summary = {"schema_version": "paperless-inbox-suggestions-qualification/v1", "qualified": True,
               "controls": len(rows), "image_id": image, "page_sha256": digest(PAGE),
               "runner_sha256": digest(RUNNER), "qualifier_sha256": digest(Path(__file__)), "cases": rows}
    (destination / "qualification.json").write_text(json.dumps(summary, indent=2) + "\n")
    files = {str(path.relative_to(destination)): digest(path) for path in destination.rglob("*") if path.is_file()}
    (destination / "receipt.json").write_text(json.dumps({"files": dict(sorted(files.items()))}, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(qualify(args.image, args.output), indent=2))
