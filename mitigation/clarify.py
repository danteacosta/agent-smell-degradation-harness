from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class Clarification:
    question: str
    signal: str


@dataclass(frozen=True)
class ClarifiedRequirement:
    text: str


def build_clarification(requirement_text: str) -> Clarification:
    """Ask a targeted question using lexical signals from the received text only."""
    lowered = requirement_text.lower()
    numbers = re.findall(r"\b\d+(?:\.\d+)?\b", lowered)
    if any(term in lowered for term in ("significant time", "a while", "reasonable time")):
        return Clarification(
            question="What exact threshold and boundary operator should replace the vague time expression?",
            signal="vague_threshold",
        )
    if "sequential digits" in lowered or "followed by digits" in lowered:
        return Clarification(
            question="What exact number and format of digits must follow the identifier prefix?",
            signal="identifier_format",
        )
    if "antiquity" in lowered:
        return Clarification(
            question="Which field defines age, and should ordering be oldest-to-newest or newest-to-oldest?",
            signal="ordering_ambiguity",
        )
    if any(term in lowered for term in ("sufficient quantity", "several", "some ")):
        return Clarification(
            question="What exact number of items must be selected?",
            signal="cardinality_ambiguity",
        )
    if len(set(numbers)) > 1:
        return Clarification(
            question="The requirement contains multiple numeric limits. Which one governs acceptance?",
            signal="numerical_inconsistency",
        )
    return Clarification(
        question="Which testable condition is missing or unresolved in this requirement?",
        signal="unresolved_condition",
    )


def apply_clarification_answer(
    requirement_text: str,
    clarification: Clarification,
    *,
    answer: str,
) -> ClarifiedRequirement:
    normalized_answer = " ".join(answer.split()).strip()
    if not normalized_answer:
        return ClarifiedRequirement(text=requirement_text)
    return ClarifiedRequirement(
        text=(
            f"{requirement_text.rstrip()}\n"
            f"Clarification question: {clarification.question}\n"
            f"Independent answer: {normalized_answer}"
        )
    )


def oracle_clarification_upper_bound(pair: dict[str, Any]) -> ClarifiedRequirement:
    """Development-only perfect-answer bound; never admissible as RQ3 evidence."""
    return ClarifiedRequirement(text=pair["clean_requirement"])
