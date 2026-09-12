from __future__ import annotations

import os
import subprocess
import sys
import json

from eval.behavior_runtime_smoke import run_smoke


def test_real_runtime_smoke_never_qualifies_a_provider_or_oracle():
    report = run_smoke()
    assert report["provider_qualified"] is False
    assert report["oracle_approved"] is False
    assert report["confirmatory_eligible"] is False
    records = report["controls"]
    assert len(records) == 3
    assert records[2]["observed_status"] == "rejected"
    assert records[2]["executed_cases"] == 0
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        assert report["status"] == "smoke_blocked_or_failed"
        assert all(r["observed_status"] == "unsafe_not_run" for r in records[:2])
        assert all("root_user" in r["safety_error_codes"] for r in records[:2])
    elif sys.platform == "linux":
        assert report["status"] == "smoke_passed"
        assert all(r["matched"] for r in records)
        assert all(r["executed_cases"] == 1 for r in records[:2])


def test_smoke_cli_exit_code_agrees_with_actual_report():
    result = subprocess.run([sys.executable, "-m", "eval.behavior_runtime_smoke"],
                            capture_output=True, text=True, timeout=10)
    report = json.loads(result.stdout)
    assert result.returncode == (0 if report["status"] == "smoke_passed" else 2)
