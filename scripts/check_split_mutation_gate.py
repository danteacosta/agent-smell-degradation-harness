"""Qualify the H2 split tests with two isolated, targeted code mutations.

Only copies of the split module are modified. Neither the checkout nor any
scientific episode, manifest, or frozen evidence is changed by this gate.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "eval" / "splits.py"
TEST = ROOT / "tests" / "test_split_manifest.py"
MUTATIONS = (
    (
        "project_id holdout",
        '        if project in project_splits and project_splits[project] != split:\n'
        '            raise ValueError("project_id crosses split boundary")\n',
        "test_applying_manifest_rejects_cross_project_leakage_with_recomputed_hash",
    ),
    (
        "source_intent_id holdout",
        '        if source in intent_splits and intent_splits[source] != split:\n'
        '            raise ValueError("source_intent_id crosses split boundary")\n',
        "test_applying_manifest_rejects_intent_leakage_across_projects",
    ),
)


def _run(test_name: str, workspace: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=short", f"tests/test_split_manifest.py::{test_name}"],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def main() -> int:
    original = SOURCE.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="h2-split-mutations-") as scratch:
        workspace = Path(scratch)
        (workspace / "eval").mkdir()
        (workspace / "tests").mkdir()
        shutil.copy2(ROOT / "eval" / "__init__.py", workspace / "eval" / "__init__.py")
        shutil.copy2(TEST, workspace / "tests" / TEST.name)
        destination = workspace / "eval" / "splits.py"
        destination.write_text(original, encoding="utf-8")

        for label, guard, test_name in MUTATIONS:
            baseline = _run(test_name, workspace)
            if baseline.returncode != 0 or "1 passed" not in baseline.stdout:
                print(f"Baseline failed for {label}:\n{baseline.stdout}\n{baseline.stderr}", file=sys.stderr)
                return 1
            if original.count(guard) != 1:
                print(f"Expected exactly one guard for {label}", file=sys.stderr)
                return 1

            destination.write_text(original.replace(guard, "", 1), encoding="utf-8")
            try:
                mutant = _run(test_name, workspace)
            finally:
                destination.write_text(original, encoding="utf-8")
            report = mutant.stdout + mutant.stderr
            if (
                mutant.returncode != 1
                or f"FAILED tests/test_split_manifest.py::{test_name}" not in report
                or "Failed: DID NOT RAISE" not in report
            ):
                print(f"Mutation survived or failed for the wrong reason ({label}):\n{report}", file=sys.stderr)
                return 1
            print(f"KILLED: {label} (the intended leakage test detected the missing guard)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
