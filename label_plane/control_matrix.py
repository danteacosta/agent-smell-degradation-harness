"""Private experimental-condition contract for natural smell screening.

The condition is carried as private metadata for analysis, but is never put in
the blinded prompt.  This module deliberately does not accept an expected
label: the condition matrix describes what was constructed, not the answer a
judge is supposed to return.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from typing import Any

CONTROL_MATRIX_SCHEMA_VERSION = "requirements-smell-control-matrix/v1"
CONTROL_CONDITIONS = (
    "clear_clean_control",
    "surface_only_control",
    "real_defect_control",
    "lexically_discreet_defect_control",
)
_FORBIDDEN_LABEL_FIELDS = frozenset(
    {"expected_label", "oracle_label", "source_label", "gold_label", "ground_truth"}
)


def validate_control_matrix(
    records: Iterable[Mapping[str, Any]],
    *,
    required_conditions: Iterable[str] = CONTROL_CONDITIONS,
    min_per_condition: int = 1,
) -> dict[str, Any]:
    """Validate private control metadata without assigning smell labels."""

    required = tuple(str(value).strip() for value in required_conditions if str(value).strip())
    if not required or len(set(required)) != len(required):
        raise ValueError("control matrix requires unique, non-empty conditions")
    if isinstance(min_per_condition, bool) or min_per_condition < 1:
        raise ValueError("min_per_condition must be positive")
    materialized = [dict(record) for record in records]
    if not materialized:
        raise ValueError("control matrix cannot be empty")
    seen_items: set[str] = set()
    by_family: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for index, record in enumerate(materialized):
        leaked = _FORBIDDEN_LABEL_FIELDS.intersection(record)
        if leaked:
            raise ValueError(f"control matrix row {index} contains label-like fields: {sorted(leaked)}")
        item_id = str(record.get("item_id", "")).strip()
        family = str(record.get("target_family", "")).strip()
        condition = str(record.get("control_condition", "")).strip()
        if not item_id or not family:
            raise ValueError(f"control matrix row {index} requires item_id and target_family")
        if condition not in required:
            raise ValueError(f"unsupported control condition: {condition!r}")
        if item_id in seen_items:
            raise ValueError(f"duplicate control matrix item_id: {item_id}")
        seen_items.add(item_id)
        by_family[family][condition] += 1
    missing: dict[str, list[str]] = {}
    for family, counts in sorted(by_family.items()):
        absent = [condition for condition in required if counts[condition] < min_per_condition]
        if absent:
            missing[family] = absent
    if missing:
        raise ValueError(f"control matrix is incomplete by family: {missing}")
    return {
        "schema_version": CONTROL_MATRIX_SCHEMA_VERSION,
        "item_count": len(materialized),
        "families": sorted(by_family),
        "conditions": list(required),
        "counts_by_family": {
            family: {condition: counts[condition] for condition in required}
            for family, counts in sorted(by_family.items())
        },
    }


__all__ = ("CONTROL_CONDITIONS", "CONTROL_MATRIX_SCHEMA_VERSION", "validate_control_matrix")
