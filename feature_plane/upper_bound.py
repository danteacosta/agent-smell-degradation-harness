"""Experimental metadata upper-bound feature boundary.

Upper-bound features are useful for diagnosing the ceiling of a detector, but
they must never enter deployable model selection or the primary estimands.
"""

from __future__ import annotations

from typing import Any, Mapping

_UPPER_BOUND_MARKERS = frozenset(
    {
        "upper_bound",
        "metadata-upper-bound",
        "metadata_upper_bound",
        "smell",
        "smell_present",
        "smell_type_code",
        "variant",
        "variant_id",
        "oracle",
        "oracle_passed",
        "label",
        "semantic_label",
    }
)


def _find_marker(value: Any, path: str = "features") -> str | None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).lower()
            if key_text in _UPPER_BOUND_MARKERS:
                return f"{path}.{key}"
            found = _find_marker(item, f"{path}.{key}")
            if found:
                return found
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            found = _find_marker(item, f"{path}[{index}]")
            if found:
                return found
    elif isinstance(value, str) and value.lower() in _UPPER_BOUND_MARKERS:
        return path
    return None


def reject_upper_bound_features(features: Mapping[str, Any]) -> None:
    """Raise when a model-selection payload contains upper-bound metadata."""

    marker = _find_marker(features)
    if marker:
        raise ValueError(f"upper-bound feature is not allowed in deployable analysis: {marker}")


def assert_deployable_features(features: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate and return a deployable feature mapping for fluent callers."""

    reject_upper_bound_features(features)
    return features


def validate_deployable_features(features: Mapping[str, Any]) -> Mapping[str, Any]:
    """Alias used by training/evaluation adapters."""

    return assert_deployable_features(features)


__all__ = (
    "assert_deployable_features",
    "reject_upper_bound_features",
    "validate_deployable_features",
)
