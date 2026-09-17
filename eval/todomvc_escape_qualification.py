"""Fail-closed gold/mutant qualification for the TodoMVC Escape case.

The command supplied after ``--`` must execute the already-frozen browser
oracle.  This module never installs dependencies and never changes the oracle;
it runs the same command twice and changes only the reviewed one-line mutant.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


REVISION = "1f2bd7f0a1fa8c602284451d282c3821d0d96aec"
COMPONENT = Path("examples/vue/src/components/TodoItem.vue")
ORACLE = Path("cypress/e2e/spec.cy.js")
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


def _run(command: list[str], checkout: Path) -> dict:
    result = subprocess.run(command, cwd=checkout, text=False, capture_output=True)
    return {
        "returncode": result.returncode,
        "stdout_sha256": _sha256(result.stdout),
        "stderr_sha256": _sha256(result.stderr),
    }


def qualify(checkout: Path, output: Path, command: list[str]) -> dict:
    checkout = checkout.resolve(strict=True)
    if not command:
        raise ValueError("an oracle command is required after --")
    if _git(checkout, "rev-parse", "HEAD") != REVISION:
        raise ValueError(f"checkout must be detached at {REVISION}")

    for path, expected_blob in UPSTREAM_BLOBS.items():
        observed = _git(checkout, "rev-parse", f"HEAD:{path.as_posix()}")
        if observed != expected_blob:
            raise ValueError(f"unexpected upstream blob for {path}")

    component_path = checkout / COMPONENT
    oracle_path = checkout / ORACLE
    component = component_path.read_bytes()
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
    gold = _run(command, checkout)
    mutant_result = None
    if gold["returncode"] == 0:
        mutant = component_text.replace(GOLD_BINDING, MUTANT_BINDING).encode()
        try:
            _atomic_write(component_path, mutant)
            mutant_result = _run(command, checkout)
        finally:
            _atomic_write(component_path, component)
    if component_path.read_bytes() != component:
        raise RuntimeError("component restoration failed")

    receipt = {
        "schema_version": "repository-e2e-qualification/v1",
        "case_id": "TODOMVC-EDIT-ESCAPE-001",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "binding": binding,
        "gold": gold,
        "mutant": mutant_result,
        "gold_passed": gold["returncode"] == 0,
        "mutation_killed": (
            gold["returncode"] == 0
            and mutant_result is not None
            and mutant_result["returncode"] != 0
        ),
        "scientific_claim": "oracle_rehearsal_only",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(receipt, indent=2, sort_keys=True).encode() + b"\n"
    _atomic_write(output, encoded)
    return {**receipt, "receipt_sha256": _sha256(encoded)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    try:
        receipt = qualify(args.checkout, args.output, command)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.error(str(error))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["gold_passed"] and receipt["mutation_killed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
