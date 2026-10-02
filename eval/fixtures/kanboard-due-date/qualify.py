"""Fail-closed classification for the bounded Kanboard board-color endpoint."""
from __future__ import annotations

import re
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


SCHEMA = "kanboard-due-date-browser/v2"
TARGET = {f"{name}_{index}" for index in (1, 2)
          for name in ("overdue_red", "upcoming_black")}
NON_TARGET = {f"{name}_{index}" for index in (1, 2)
              for name in ("task_titles", "due_text")}
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


def behavior(*, overdue: str = "#b91c1c", upcoming: str = "#111827",
             wrong_title: bool = False, wrong_text: bool = False,
             duplicate: bool = False, missing_date: bool = False,
             hidden_date: bool = False, covered_date: bool = False,
             card_background_only: bool = False,
             nested_text_colors: tuple[str, str] | None = None) -> str:
    """Authored controls, never included in model prompts."""
    title = "'Wrong title'" if wrong_title else "task.title"
    date_text = "'?'+task.dueDate" if wrong_text else "task.dueDate"
    color = "'#111827'" if card_background_only else f"(task.dueDate<today?{overdue!r}:{upcoming!r})"
    date_render = (f"due.textContent={date_text};" if nested_text_colors is None else
                   f"const ink=document.createElement('span');ink.textContent={date_text};"
                   f"ink.style.color=task.dueDate<today?{nested_text_colors[0]!r}:{nested_text_colors[1]!r};due.append(ink);")
    due = "" if missing_date else f"const due=document.createElement('span');due.dataset.role='due-date';{date_render}due.style.color={color};card.append(due);"
    if hidden_date:
        due += "due.hidden=true;"
    if covered_date:
        due += "const cover=document.createElement('div');cover.style.cssText='position:absolute;background:white;inset:0';card.style.position='relative';card.append(cover);"
    background = "card.style.backgroundColor=task.dueDate<today?'#b91c1c':'#111827';" if card_background_only else ""
    repeat = "board.append(card.cloneNode(true));" if duplicate else ""
    return ("const board=document.querySelector('#board');"
            "const today=new Date().toISOString().slice(0,10);"
            "for(const task of window.boardTasks){"
            "const card=document.createElement('article');card.dataset.taskId=task.id;"
            f"const title=document.createElement('h2');title.textContent={title};card.append(title);"
            f"{background}{due}board.append(card);{repeat}" "}")


def alternative_behavior() -> str:
    return ("const root=document.getElementById('board');"
            "window.boardTasks.map(item=>{const row=document.createElement('section');"
            "row.setAttribute('data-task-id',item.id);"
            "const heading=document.createElement('strong');heading.textContent=item.title;row.append(heading);"
            "const date=document.createElement('time');date.setAttribute('data-role','due-date');"
            "date.textContent=item.dueDate;date.style.display='block';"
            "date.style.color=Date.parse(item.dueDate+'T00:00:00Z')<Date.now()?'#a00':'#202020';"
            "row.append(date);return row}).forEach(row=>root.append(row));")


CONTROLS = {
    "reference": (behavior(), "pass"),
    "alternative": (alternative_behavior(), "pass"),
    "all-black": (behavior(overdue="#111827"), "target_only_failure"),
    "all-red": (behavior(upcoming="#b91c1c"), "target_only_failure"),
    "swapped": (behavior(overdue="#111827", upcoming="#b91c1c"), "target_only_failure"),
    "background-only": (behavior(card_background_only=True), "target_only_failure"),
    "nested-wrong-text-color": (behavior(nested_text_colors=("#111827", "#b91c1c")), "target_only_failure"),
    "nested-correct-text-color": (behavior(overdue="#111827", upcoming="#b91c1c",
                                           nested_text_colors=("#b91c1c", "#111827")), "pass"),
    "wrong-title": (behavior(wrong_title=True), "non_target_only_failure"),
    "wrong-date-text": (behavior(wrong_text=True), "non_target_only_failure"),
    "duplicate-card": (behavior(duplicate=True), "interface_error"),
    "missing-date": (behavior(missing_date=True), "interface_error"),
    "hidden-date": (behavior(hidden_date=True), "interface_error"),
    "covered-date": (behavior(covered_date=True), "interface_error"),
    "script-error": ("throw new Error('authored control');", "browser_error"),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def qualify(image: str, destination: Path) -> dict:
    """Run every authored control in the exact offline browser image."""
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
    summary = {"schema_version": "kanboard-due-date-qualification/v2", "qualified": True,
               "controls": len(rows), "image_id": image, "page_sha256": digest(PAGE),
               "runner_sha256": digest(RUNNER), "qualifier_sha256": digest(Path(__file__)),
               "cases": rows}
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
