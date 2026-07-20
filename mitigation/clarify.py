from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Clarification:
    question: str
    simulated_answer: str


@dataclass(frozen=True)
class ClarifiedRequirement:
    text: str


_QUESTION_TEMPLATES: dict[str, str] = {
    "vague_threshold": "What exact minute threshold defines the delay?",
    "identifier_format": "How many digits must follow the P- prefix?",
    "ordering_ambiguity": "Should cards be ordered oldest-to-newest by elapsed time?",
    "cardinality_ambiguity": "How many oldest active orders should be displayed?",
}

_SIMULATED_ANSWERS: dict[str, str] = {
    "vague_threshold": "More than 5 minutes.",
    "identifier_format": "Exactly three digits after P-, e.g. P-014.",
    "ordering_ambiguity": "Oldest to newest by elapsed time.",
    "cardinality_ambiguity": "Exactly 5 oldest active orders.",
}


def build_clarification(pair: dict[str, Any]) -> Clarification:
    smell_type = pair["smell"]["type"]
    question = _QUESTION_TEMPLATES.get(
        smell_type,
        f"Please clarify the requirement affected by {smell_type}.",
    )
    simulated_answer = _SIMULATED_ANSWERS.get(smell_type, pair["clean_requirement"])
    return Clarification(question=question, simulated_answer=simulated_answer)


def apply_clarification_answer(
    pair: dict[str, Any],
    clarification: Clarification,
    *,
    answer: str,
) -> ClarifiedRequirement:
    if answer != clarification.simulated_answer:
        return ClarifiedRequirement(text=pair["smelly_requirement"])
    return ClarifiedRequirement(text=pair["clean_requirement"])
