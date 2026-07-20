from __future__ import annotations

from typing import Any

from agent_harness.types import OracleResult


def score_artifact(
    intent_id: str,
    task_family: str,
    artifact: dict[str, Any],
    oracle_spec: dict[str, Any],
) -> OracleResult:
    checks: dict[str, bool] = {}
    for key, expected in oracle_spec.items():
        actual = artifact.get(key)
        checks[key] = actual == expected

    passed = all(checks.values())
    failed_keys = [key for key, ok in checks.items() if not ok]
    if passed:
        detail = f"{intent_id}/{task_family}: all oracle keys match"
    elif failed_keys:
        detail = (
            f"{intent_id}/{task_family}: mismatched keys: {', '.join(failed_keys)}"
        )
    else:
        detail = f"{intent_id}/{task_family}: artifact does not match oracle_spec"

    return OracleResult(passed=passed, detail=detail, checks=checks)
