from __future__ import annotations

from typing import Mapping


def semantic_risk(provenance_semantic: Mapping[str, int]) -> float:
    if not provenance_semantic.get("constraint_event_present"):
        return 1.0
    if not provenance_semantic.get("constraint_field_count"):
        return 0.5
    return 0.0
