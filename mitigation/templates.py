from __future__ import annotations

from typing import Any


def rewrite_from_oracle_spec(
    smell_type: str,
    oracle_spec: dict[str, Any],
    task_family: str = "codegen",
) -> str:
    if smell_type == "vague_threshold":
        minutes = oracle_spec.get("delay_threshold_minutes", 5)
        comparator = oracle_spec.get("comparator", ">")
        relation = "strictly greater than" if comparator == ">" else "greater than or equal to"
        return (
            f"Oracle constraint: mark orders as delayed when wait time is "
            f"{relation} {minutes} minutes."
        )

    if smell_type == "identifier_format":
        return (
            "Order ID must follow P- plus exactly three digits "
            "(pattern enforced in oracle specification)."
        )

    if smell_type == "ordering_ambiguity":
        sort_key = oracle_spec.get("required_sort_key") or oracle_spec.get("sort_key")
        return f"Cards must be ordered using sort key '{sort_key}' from oldest to newest."

    if smell_type == "cardinality_ambiguity":
        count = oracle_spec.get("exact_cardinality") or oracle_spec.get("cardinality", 5)
        selection = oracle_spec.get("selection", "oldest_active")
        return f"Display exactly {count} items with selection policy '{selection}'."

    criterion = oracle_spec.get("criterion", "specified constraints")
    return f"Requirement must satisfy: {criterion}."
