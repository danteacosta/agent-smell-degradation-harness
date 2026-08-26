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

    generation_contract = pair["generation_contract"]
    if not isinstance(generation_contract, dict):
        raise ValueError(f"{source}: 'generation_contract' must be an object")

    oracle_spec = pair["oracle_spec"]
    if not isinstance(oracle_spec, dict):
        raise ValueError(f"{source}: 'oracle_spec' must be an object")
    families = set(REQUIRED_TASK_FAMILIES) | set(generation_contract) | set(oracle_spec)
    for family in sorted(families):
        if family not in oracle_spec:
            raise ValueError(f"{source}: oracle_spec missing task family '{family}'")
        if not isinstance(oracle_spec[family], dict):
            raise ValueError(f"{source}: oracle_spec['{family}'] must be an object")
        contract = generation_contract.get(family)
        if not isinstance(contract, dict):
            raise ValueError(f"{source}: generation_contract missing task family '{family}'")
        output_keys = contract.get("output_keys")
        if (
            not isinstance(output_keys, list)
            or not output_keys
            or not all(isinstance(key, str) and key.strip() for key in output_keys)
            or len(set(output_keys)) != len(output_keys)
        ):
            raise ValueError(
                f"{source}: generation_contract['{family}'].output_keys must be unique non-empty strings"
            )
        if family == "behavior_codegen":
            if set(output_keys) != {"source_code"} or set(oracle_spec[family]) != {"_execution"}:
                raise ValueError(
                    f"{source}: behavior_codegen requires source_code and private _execution metadata"
                )
            continue
        oracle_fields = {
            key for key in oracle_spec[family] if not str(key).startswith("_")
        }
        if set(output_keys) != oracle_fields:
            raise ValueError(
                f"{source}: generation contract and oracle fields disagree for '{family}'"
            )
