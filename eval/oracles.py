from __future__ import annotations

from typing import Any

from agent_harness.types import OracleResult


def score_artifact(
    intent_id: str,
    task_family: str,
    artifact: dict[str, Any],
    oracle_spec: dict[str, Any],
) -> OracleResult:
    passed = artifact == oracle_spec
    if passed:
        detail = f"{intent_id}/{task_family}: artifact matches oracle_spec"
    else:
        detail = f"{intent_id}/{task_family}: artifact does not match oracle_spec"
    return OracleResult(passed=passed, detail=detail)
