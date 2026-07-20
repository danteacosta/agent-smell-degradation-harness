from __future__ import annotations

from typing import Any

from pairs.schema import (
    REQUIRED_SMELL_KEYS,
    REQUIRED_TASK_FAMILIES,
    REQUIRED_TOP_LEVEL_KEYS,
)


def validate_pair(pair: dict[str, Any], *, source: str = "pair") -> None:
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in pair:
            raise ValueError(f"{source}: missing required key '{key}'")

    smell = pair["smell"]
    if not isinstance(smell, dict):
        raise ValueError(f"{source}: 'smell' must be an object")
    for key in REQUIRED_SMELL_KEYS:
        if key not in smell:
            raise ValueError(f"{source}: smell missing required key '{key}'")

    oracle_spec = pair["oracle_spec"]
    if not isinstance(oracle_spec, dict):
        raise ValueError(f"{source}: 'oracle_spec' must be an object")
    for family in REQUIRED_TASK_FAMILIES:
        if family not in oracle_spec:
            raise ValueError(f"{source}: oracle_spec missing task family '{family}'")
        if not isinstance(oracle_spec[family], dict):
            raise ValueError(f"{source}: oracle_spec['{family}'] must be an object")
