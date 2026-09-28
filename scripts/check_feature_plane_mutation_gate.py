"""Check three pre-final feature boundaries with isolated, targeted mutations.

The repository, frozen evidence, and provider runtime are never modified.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "feature_plane" / "deployable.py"
TEST = ROOT / "tests" / "test_deployable_feature_schema.py"
MUTATIONS = (
    (
        "T4 checkpoint marker",
        'if event_name in _TERMINAL_EVENT_NAMES or str(event.get("checkpoint", "")).upper() in {\n'
        '            "T4",\n'
        '            "FINAL",\n'
        '        }:',
        "if event_name in _TERMINAL_EVENT_NAMES:",
        "test_t4_checkpoint_cannot_enter_deployable_features",
        "assert 1 == 0",
    ),
    (
        "pre-final event after T4",
        '        if label_plane_started:\n'
        '            raise ValueError(f"pre-final checkpoint {event_name!r} occurs after the label plane")\n',
        "",
        "test_pre_final_event_after_t4_is_rejected",
        "Failed: DID NOT RAISE",
    ),
    (
        "canonical label attribute",
        "        terminal_key = _contains_terminal_key(terminal_source)\n",
        "        terminal_key = None\n",
        "test_canonical_label_field_is_rejected_from_deployable_trace",
        "Failed: DID NOT RAISE",
    ),
)


def _run(test_name: str, workspace: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(filter(None, (str(ROOT), env.get("PYTHONPATH", ""))))
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=short", f"tests/{TEST.name}::{test_name}"],
        cwd=workspace,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def main() -> int:
    original = SOURCE.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="h2-feature-mutations-") as scratch:
        workspace = Path(scratch)
        shutil.copytree(ROOT / "feature_plane", workspace / "feature_plane", ignore=shutil.ignore_patterns("__pycache__"))
        (workspace / "tests").mkdir()
        shutil.copy2(TEST, workspace / "tests" / TEST.name)
        destination = workspace / "feature_plane" / "deployable.py"

        for label, guard, replacement, test_name, expected in MUTATIONS:
            baseline = _run(test_name, workspace)
            if baseline.returncode != 0 or "1 passed" not in baseline.stdout:
                print(f"Baseline failed for {label}:\n{baseline.stdout}\n{baseline.stderr}", file=sys.stderr)
                return 1
            if original.count(guard) != 1:
                print(f"Expected exactly one guard for {label}", file=sys.stderr)
                return 1

            destination.write_text(original.replace(guard, replacement, 1), encoding="utf-8")
            try:
                mutant = _run(test_name, workspace)
            finally:
                destination.write_text(original, encoding="utf-8")
            report = mutant.stdout + mutant.stderr
            if (
                mutant.returncode != 1
                or f"FAILED tests/{TEST.name}::{test_name}" not in report
                or expected not in report
            ):
                print(f"Mutation survived or failed for the wrong reason ({label}):\n{report}", file=sys.stderr)
                return 1
            print(f"KILLED: {label} (the intended pre-final boundary test detected the mutation)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
