from __future__ import annotations

from typing import Mapping


def semantic_risk(provenance_semantic: Mapping[str, int]) -> float:
    if not provenance_semantic.get("constraint_event_present"):
        return 1.0
    if not provenance_semantic.get("constraint_field_count"):
        return 0.5
    burden = sum(
        int(provenance_semantic.get(key, 0))
        for key in (
            "unresolved_reference_count",
            "assumption_count",
            "contradiction_count",
        )
    )
    if burden:
        return min(1.0, 0.25 + burden / max(float(provenance_semantic.get("constraint_count", 1)), 1.0))
    return 0.0
