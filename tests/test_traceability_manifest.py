from __future__ import annotations

import json
from pathlib import Path

from eval.task_adapters import load_traceability_manifest


def test_traceability_manifest_is_versioned_and_contains_adversarial_cases() -> None:
    manifest = json.loads(
        (Path(__file__).parents[1] / "tasks" / "traceability.json").read_text()
    )

    assert manifest["schema_version"] == "traceability/v1"
    assert {case["expected"] for case in manifest["cases"]} >= {
        "pass",
        "missing",
        "stale",
        "tampered",
        "self_reported",
    }
    assert all(case["oracle_independent"] for case in manifest["cases"])
    assert load_traceability_manifest()["schema_version"] == "traceability/v1"
