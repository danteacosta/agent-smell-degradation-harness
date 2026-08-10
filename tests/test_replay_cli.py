from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from replay.runner import run_fixture, to_sarif

ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "replay" / "fixtures"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    return subprocess.run(
        [sys.executable, "-m", "replay", *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
    )


def test_cli_emits_consistent_json_and_valid_sarif(tmp_path: Path) -> None:
    json_path = tmp_path / "report.json"
    sarif_path = tmp_path / "report.sarif"
    result = _run("--fixture", "constraint-loss", "--json", str(json_path), "--sarif", str(sarif_path))
    assert result.returncode == 20
    report = json.loads(json_path.read_text(encoding="utf-8"))
    sarif = json.loads(sarif_path.read_text(encoding="utf-8"))
    assert report["decision"] == "block"
    assert sarif["version"] == "2.1.0"
    assert sarif["$schema"].endswith("sarif-schema-2.1.0.json")
    assert len(sarif["runs"]) == 1
    run = sarif["runs"][0]
    assert run["tool"]["driver"]["rules"]
    assert run["results"]
    assert run["results"][0]["properties"]["decision"] == report["decision"]
    assert run["results"][0]["properties"]["evidence"] == report["semantic_evidence"]


def test_cli_invalid_bundle_is_machine_readable_exit_30(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(FIXTURES, bundle)
    trace = bundle / "traces" / "clean.jsonl"
    trace.write_bytes(trace.read_bytes() + b"\n")
    json_path = tmp_path / "invalid.json"
    result = _run("--bundle", str(bundle), "--json", str(json_path))
    assert result.returncode == 30
    report = json.loads(json_path.read_text(encoding="utf-8"))
    assert report["decision"] == "invalid-contract"
    assert report["exit_code"] == 30
    assert report["error"]["code"] == "invalid_contract"


def test_optional_sarif_extensions_are_filtered() -> None:
    report = run_fixture("clean", FIXTURES)
    sarif = to_sarif(report, {"confidence": float("nan"), "unexpected": {"oracle_passed": True}})
    result = sarif["runs"][0]["results"][0]
    assert "unexpected" not in result["properties"]
    assert result["properties"]["decision"] == "approve"
