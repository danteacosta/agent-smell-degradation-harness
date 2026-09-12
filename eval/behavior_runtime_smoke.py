"""Exercise the real code executor with three original, harmless controls.

This qualifies only a small local execution path, never a provider, source
oracle, security boundary against arbitrary hostile code, or H1/H2 outcome.
"""
from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

from eval import codegen_sandbox


def run_smoke() -> dict:
    tests = [{"args": [2], "expected": 3}]
    controls = [
        ("correct_increment", "def evaluate(x):\n    return x + 1", "passed"),
        ("incorrect_increment", "def evaluate(x):\n    return x", "failed"),
        ("forbidden_import", "import os\ndef evaluate(x):\n    return x + 1", "rejected"),
    ]
    records = []
    for name, source, expected in controls:
        result = codegen_sandbox.evaluate(source, tests)
        records.append({
            "control": name, "expected_status": expected,
            "observed_status": result["status"],
            "matched": result["status"] == expected,
            "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "executed_cases": len(result.get("cases", [])),
            "safety_controls": result.get("safety_controls", {}),
            "safety_error_codes": [e.get("code") for e in result.get("safety_errors", [])],
        })
    return {
        "schema_version": "behavior-runtime-smoke/v1",
        "scope": "original_control_subprocess_smoke_only",
        "status": "smoke_passed" if all(r["matched"] for r in records) else "smoke_blocked_or_failed",
        "platform": platform.system(), "python_version": platform.python_version(),
        "executor_sha256": hashlib.sha256(Path(codegen_sandbox.__file__).read_bytes()).hexdigest(),
        "same_test_sha256": hashlib.sha256(json.dumps(tests, sort_keys=True).encode()).hexdigest(),
        "provider_qualified": False, "oracle_approved": False,
        "confirmatory_eligible": False, "controls": records,
        "limitations": "No provider calls, latency benchmark, adversarial-isolation proof or source-derived outcome validation. Live discovery remains quarantined.",
    }


if __name__ == "__main__":
    report = run_smoke()
    print(json.dumps(report, sort_keys=True, indent=2))
    raise SystemExit(0 if report["status"] == "smoke_passed" else 2)
