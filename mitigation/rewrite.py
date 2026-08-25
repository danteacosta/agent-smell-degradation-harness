from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mitigation.templates import rewrite_from_oracle_spec


@dataclass(frozen=True)
class RewriteResult:
    text: str
    changed: bool


def rewrite_requirement(
    requirement_text: str,
) -> RewriteResult:
    """Structure a requirement without recovering facts from an oracle.

    The transformation preserves the supplied text and adds a verification
    contract. It must never inspect the clean pair or oracle specification.
    Missing values remain unresolved and should trigger clarification.
    """
    normalized = " ".join(requirement_text.split()).strip()
    if normalized and normalized[-1] not in ".!?":
        normalized += "."
    text = (
        f"Requirement: {normalized}\n"
        "Verification checklist: preserve every explicit threshold, boundary, "
        "ordering direction, cardinality, and identifier format; do not invent "
        "missing values; request clarification for unresolved conditions."
    )
    return RewriteResult(text=text, changed=text != requirement_text)


def oracle_rewrite_upper_bound(
    smelly_text: str,
    pair: dict[str, Any],
    *,
    mode: str = "clean_pair",
    task_family: str = "codegen",
) -> RewriteResult:
    """Development-only upper bound that is inadmissible as RQ3 evidence."""
    if mode == "clean_pair":
        clean = pair["clean_requirement"]
        return RewriteResult(text=clean, changed=smelly_text != clean)
    if mode == "oracle_template":
        smell_type = pair["smell"]["type"]
        oracle_spec = pair["oracle_spec"][task_family]
        text = rewrite_from_oracle_spec(smell_type, oracle_spec, task_family=task_family)
        return RewriteResult(text=text, changed=smelly_text != text)
    raise ValueError(f"unknown oracle upper-bound rewrite mode: {mode}")
