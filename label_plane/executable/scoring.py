from __future__ import annotations

from typing import Any

from agent_harness.types import OracleResult


def score_artifact(
    intent_id: str,
    task_family: str,
    artifact: dict[str, Any],
    oracle_spec: dict[str, Any],
) -> OracleResult:
    """Score an artifact against its executable reference specification."""
    checks = {key: artifact.get(key) == expected for key, expected in oracle_spec.items()}
    failed_keys = [key for key, passed in checks.items() if not passed]
    if not failed_keys:
        detail = f"{intent_id}/{task_family}: all oracle keys match"
    else:
        detail = f"{intent_id}/{task_family}: mismatched keys: {', '.join(failed_keys)}"
    return OracleResult(passed=not failed_keys, detail=detail, checks=checks)
