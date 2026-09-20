"""Fail-closed gold/mutant qualification for the TodoMVC Escape case.

The command supplied after ``--`` must execute the already-frozen browser
oracle.  This module never installs dependencies and never changes the oracle;
it runs the same command twice and changes only the reviewed one-line mutant.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import signal
import stat
from pathlib import Path
import subprocess
import tempfile
import threading
from xml.etree import ElementTree


REVISION = "1f2bd7f0a1fa8c602284451d282c3821d0d96aec"
COMPONENT = Path("examples/vue/src/components/TodoItem.vue")
ORACLE = Path("cypress/e2e/spec.cy.js")
JUNIT_REPORT = Path("todomvc-qualification-junit.xml")
VISUAL_SUPPORT = Path("cypress/support/qualification-visual.js")
MEDIA_DIRECTORIES = (Path("cypress/screenshots"), Path("cypress/videos"))
ESCAPE_TEST = "TodoMVC - vue Editing should cancel edits on escape"
ROOT_LOCK = Path("package-lock.json")
VUE_LOCK = Path("examples/vue/package-lock.json")
UPSTREAM_BLOBS = {
    COMPONENT: "3ca0eb4233e2fee3fddea3d198c58617844eb045",
    ORACLE: "478bcfb17f407d56b4db19c4bffadcd0aa1e0972",
}
GOLD_BINDING = '@keyup.escape="cancelEdit"'
MUTANT_BINDING = '@keyup.escape="commitEdit"'
REQUIRED_ORACLE_ASSERTIONS = (
    ".should('not.have.class', 'editing')",
    ".find('.edit').should('not.exist')",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(checkout: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=checkout, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def _atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _oracle_result(report: bytes) -> dict:
    """Accept only the frozen Escape test and its expected title assertion."""
    invalid = {"valid": False, "escape_passed": False, "targeted_failure": False}
    try:
        root = ElementTree.fromstring(report)
    except ElementTree.ParseError:
        return invalid
    if root.tag not in {"testsuites", "testsuite"}:
        return invalid
    tests = list(root.iter("testcase"))
    names = [test.get("name") for test in tests]
    if (not tests or any(not name for name in names)
            or len(set(names)) != len(names) or names.count(ESCAPE_TEST) != 1):
        return invalid
    escape_passed = False
    targeted_failure = False
    skipped = []
    for test in tests:
        name = test.get("name")
        failures = list(test.findall("failure"))
        if test.findall("error") or len(failures) > 1:
            return invalid
        if test.findall("skipped"):
            if name == ESCAPE_TEST or failures:
                return invalid
            skipped.append(name)
        elif failures:
            failure = failures[0]
            message = failure.get("message", "")
            if (name != ESCAPE_TEST or failure.get("type") != "AssertionError"
                    or re.fullmatch(
                        r"(?:Timed out retrying(?: after [0-9]+ms)?: )?"
                        r"expected '<li>' to contain 'feed the cat'", message) is None):
                return invalid
            targeted_failure = True
        elif name == ESCAPE_TEST:
            escape_passed = True
    return {
        "valid": True,
        "escape_passed": escape_passed,
        "targeted_failure": targeted_failure,
        "test_inventory_sha256": _sha256(json.dumps(sorted(names)).encode()),
        "skipped_tests_sha256": _sha256(json.dumps(sorted(skipped)).encode()),
    }


def _run(command: list[str], checkout: Path, evidence: Path) -> dict:
    evidence.mkdir()
    result = subprocess.run(command, cwd=checkout, text=False, capture_output=True)
    _atomic_write(evidence / "stdout.log", result.stdout)
    _atomic_write(evidence / "stderr.log", result.stderr)
    report_path = checkout / JUNIT_REPORT
    report = None
    if report_path.is_file() and not report_path.is_symlink():
        report = report_path.read_bytes()
        _atomic_write(evidence / "junit.xml", report)
    # The next arm must create its own report, never reuse the gold report.
    report_path.unlink(missing_ok=True)
    return {
        "returncode": result.returncode,
        "stdout_sha256": _sha256(result.stdout),
        "stderr_sha256": _sha256(result.stderr),
        "junit_sha256": _sha256(report) if report is not None else None,
        "oracle": _oracle_result(report or b""),
    }


def _reject_symlink_ancestors(checkout: Path, relative: Path) -> None:
    current = checkout
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"media capture refuses symlink: {current}")


def _require_fresh_media(checkout: Path) -> None:
    for relative in MEDIA_DIRECTORIES:
        _reject_symlink_ancestors(checkout, relative)
        if (checkout / relative).exists():
            raise ValueError(f"media directory must not already exist: {relative}")


def _capture_media(checkout: Path, evidence: Path) -> dict:
    """Preserve this run before Cypress can clear its output for the next arm.

    Validate every tree entry before moving anything. Moving the complete trees
    also preserves ancillary files without deleting unrelated content. Format
    signatures are a sanity check; decoding and visual review remain CI checks.
    """
    directories = []
    for relative in MEDIA_DIRECTORIES:
        _reject_symlink_ancestors(checkout, relative)
        source = checkout / relative
        if not source.exists():
            continue
        if not source.is_dir():
            raise ValueError(f"media path is not a directory: {relative}")
        for parent, subdirs, files in os.walk(source, followlinks=False):
            for name in subdirs + files:
                path = Path(parent) / name
                mode = path.lstat().st_mode
                if stat.S_ISLNK(mode):
                    raise ValueError(f"media capture refuses symlink: {path}")
                if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                    raise ValueError(f"media capture requires regular files: {path}")
        directories.append((source, evidence / "media" / relative.name))

    manifest = []
    screenshot = video = False
    for source, destination in directories:
        destination.parent.mkdir(exist_ok=True)
        # Evidence is fresh and the source disappears, so the mutant cannot
        # reuse gold media even if its command fails before launching Cypress.
        source.rename(destination)
        for path in sorted(destination.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".png", ".mp4"}:
                continue
            data = path.read_bytes()
            manifest.append({
                "path": path.relative_to(evidence.parent).as_posix(),
                "bytes": len(data),
                "sha256": _sha256(data),
            })
            if (path.name == "escape-after-interaction.png"
                    and path.parent.name == "spec.cy.js"
                    and destination.name == "screenshots"
                    and len(data) > 8 and data.startswith(b"\x89PNG\r\n\x1a\n")):
                screenshot = True
            if (path.name == "spec.cy.js.mp4" and destination.name == "videos"
                    and len(data) > 12 and data[4:8] == b"ftyp"):
                video = True
    return {"media": manifest, "visual_complete": screenshot and video}


def _run_arm(command: list[str], checkout: Path, evidence: Path, capture_media: bool) -> dict:
    if capture_media:
        _require_fresh_media(checkout)
    result = _run(command, checkout, evidence)
    if capture_media:
        result.update(_capture_media(checkout, evidence))
    return result


@contextmanager
def _restore_on_termination():
    """Let the mutation's finally block run on normal CLI termination."""
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    previous = signal.getsignal(signal.SIGTERM)

    def interrupted(_signum, _frame):
        raise KeyboardInterrupt("qualification terminated")

    signal.signal(signal.SIGTERM, interrupted)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, previous)


def qualify(checkout: Path, output: Path, command: list[str], *,
            capture_media: bool = False) -> dict:
    checkout = checkout.resolve(strict=True)
    if not command:
        raise ValueError("an oracle command is required after --")
    if capture_media:
        _require_fresh_media(checkout)
        _reject_symlink_ancestors(checkout, VISUAL_SUPPORT)
    if _git(checkout, "rev-parse", "HEAD") != REVISION:
        raise ValueError(f"checkout must be detached at {REVISION}")

    for path, expected_blob in UPSTREAM_BLOBS.items():
        observed = _git(checkout, "rev-parse", f"HEAD:{path.as_posix()}")
        if observed != expected_blob:
            raise ValueError(f"unexpected upstream blob for {path}")

    component_path = checkout / COMPONENT
    oracle_path = checkout / ORACLE
    component = component_path.read_bytes()
    component_blob = hashlib.sha1(
        f"blob {len(component)}\0".encode() + component, usedforsecurity=False).hexdigest()
    if component_blob != UPSTREAM_BLOBS[COMPONENT]:
        raise ValueError("working-tree component does not match the frozen upstream blob")
    oracle = oracle_path.read_text(encoding="utf-8")
    component_text = component.decode("utf-8")
    if component_text.count(GOLD_BINDING) != 1 or MUTANT_BINDING in component_text:
        raise ValueError("gold Escape binding is not unique")
    missing = [item for item in REQUIRED_ORACLE_ASSERTIONS if item not in oracle]
    if missing:
        raise ValueError(f"strengthened oracle assertions missing: {missing}")

    binding = {
        "revision": REVISION,
        "command": command,
        "component_sha256": _sha256(component),
        "oracle_sha256": _sha256(oracle_path.read_bytes()),
        "root_lock_sha256": _sha256((checkout / ROOT_LOCK).read_bytes()),
        "vue_lock_sha256": _sha256((checkout / VUE_LOCK).read_bytes()),
    }
    if capture_media:
        binding["visual_support_sha256"] = _sha256((checkout / VISUAL_SUPPORT).read_bytes())
    report_path = checkout / JUNIT_REPORT
    if report_path.exists() or report_path.is_symlink():
        raise ValueError("qualification report path must not already exist")
    evidence = output.with_suffix(".evidence")
    evidence.mkdir(parents=True, exist_ok=False)
    gold = _run_arm(command, checkout, evidence / "gold", capture_media)
    gold_passed = gold["returncode"] == 0 and gold["oracle"]["escape_passed"]
    mutant_result = None
    if gold_passed:
        mutant = component_text.replace(GOLD_BINDING, MUTANT_BINDING).encode()
        with _restore_on_termination():
            try:
                _atomic_write(component_path, mutant)
                mutant_result = _run_arm(command, checkout, evidence / "mutant", capture_media)
            finally:
                _atomic_write(component_path, component)
    if component_path.read_bytes() != component:
        raise RuntimeError("component restoration failed")
    mutation_killed = bool(
        gold_passed and mutant_result is not None
        and mutant_result["returncode"] == 1
        and mutant_result["oracle"]["targeted_failure"]
        and all(gold["oracle"][key] == mutant_result["oracle"][key]
                for key in ("test_inventory_sha256", "skipped_tests_sha256"))
    )

    receipt = {
        "schema_version": "repository-e2e-qualification/v2",
        "case_id": "TODOMVC-EDIT-ESCAPE-001",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "binding": binding,
        "gold": gold,
        "mutant": mutant_result,
        "gold_passed": gold_passed,
        "mutation_killed": mutation_killed,
        "evidence_directory": evidence.name,
        "scientific_claim": "oracle_rehearsal_only",
    }
    if capture_media:
        receipt["visual_complete"] = bool(
            gold["visual_complete"] and mutant_result is not None
            and mutant_result["visual_complete"])
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(receipt, indent=2, sort_keys=True).encode() + b"\n"
    _atomic_write(output, encoded)
    return {**receipt, "receipt_sha256": _sha256(encoded)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--capture-media", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    try:
        receipt = qualify(args.checkout, args.output, command, capture_media=args.capture_media)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.error(str(error))
    print(json.dumps(receipt, sort_keys=True))
    passed = receipt["gold_passed"] and receipt["mutation_killed"]
    if args.capture_media:
        passed = passed and receipt["visual_complete"]
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
