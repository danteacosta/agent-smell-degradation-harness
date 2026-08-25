"""Validation for the thesis-specific conditional-requirement annotation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

CONDITIONAL_SEMANTICS_SCHEMA_VERSION = "conditional-semantics/v1"
_ITEM_KEYS = {
    "antecedent",
    "consequent",
    "necessity_status",
    "temporal_relation",
    "negative_case",
}
_NEGATIVE_CASE_KEYS = {"status", "description"}
_NECESSITY_STATUSES = {"sufficient_only", "also_necessary", "undetermined"}
_TEMPORAL_RELATIONS = {"during", "next_state", "eventually", "irrelevant", "undetermined"}
_NEGATIVE_CASE_STATUSES = {"specified", "not_specified", "not_applicable"}


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path} must be a non-empty string")
    return value.strip()


def validate_conditional_semantics(
    value: Any,
    *,
    path: str = "conditional_semantics",
) -> list[dict[str, Any]]:
    """Validate and normalize conditional interpretation evidence.

    The annotation is deliberately bounded and descriptive. It contains no
    smell, label, oracle, or terminal-output field and therefore can be used in
    the pre-final feature plane without importing the outcome.
    """

    if not isinstance(value, list):
        raise ValueError(f"{path} must be an array")
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        if not isinstance(item, Mapping) or set(item) != _ITEM_KEYS:
            raise ValueError(f"{item_path} must contain exactly {sorted(_ITEM_KEYS)}")
        necessity = _text(item["necessity_status"], f"{item_path}.necessity_status")
        if necessity not in _NECESSITY_STATUSES:
            raise ValueError(f"{item_path}.necessity_status is invalid")
        temporal = _text(item["temporal_relation"], f"{item_path}.temporal_relation")
        if temporal not in _TEMPORAL_RELATIONS:
            raise ValueError(f"{item_path}.temporal_relation is invalid")
        negative = item["negative_case"]
        if not isinstance(negative, Mapping) or set(negative) != _NEGATIVE_CASE_KEYS:
            raise ValueError(f"{item_path}.negative_case must contain status and description")
        status = _text(negative["status"], f"{item_path}.negative_case.status")
        if status not in _NEGATIVE_CASE_STATUSES:
            raise ValueError(f"{item_path}.negative_case.status is invalid")
        description = negative["description"]
        if status == "specified":
            description = _text(description, f"{item_path}.negative_case.description")
        elif description is not None:
            raise ValueError(
                f"{item_path}.negative_case.description must be null when status is {status}"
            )
        normalized.append(
            {
                "antecedent": _text(item["antecedent"], f"{item_path}.antecedent"),
                "consequent": _text(item["consequent"], f"{item_path}.consequent"),
                "necessity_status": necessity,
                "temporal_relation": temporal,
                "negative_case": {"status": status, "description": description},
            }
        )
    return normalized


__all__ = (
    "CONDITIONAL_SEMANTICS_SCHEMA_VERSION",
    "validate_conditional_semantics",
)
