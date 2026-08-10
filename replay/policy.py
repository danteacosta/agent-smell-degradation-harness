from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GatePolicy:
    version: str
    block_when: tuple[str, ...]
    warn_when: tuple[str, ...]


DEFAULT_POLICY = GatePolicy(
    version="constraint-gate/v1",
    block_when=("missing_constraints", "contradiction", "execution_error", "missing_validation"),
    warn_when=("unresolved_reference", "missing_coverage"),
)


def load_failure_cases(path: str | Path | None = None) -> list[dict[str, Any]]:
    target = Path(path) if path else Path(__file__).with_name("failure_cases.json")
    value = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("failure case registry must be an array")
    for case in value:
        if not isinstance(case, dict) or not case.get("case_id") or case.get("confirmatory") is not False:
            raise ValueError("failure case registry entries must be explicit non-confirmatory cases")
    return value
