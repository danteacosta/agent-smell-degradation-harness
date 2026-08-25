from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mitigation.clarify import (
    apply_clarification_answer,
    build_clarification,
    oracle_clarification_upper_bound,
)
from mitigation.detect import detect_smell
from mitigation.rewrite import oracle_rewrite_upper_bound, rewrite_requirement


@dataclass(frozen=True)
class PreparedRequirement:
    text: str
    policy: str
    mitigation_meta: dict[str, Any] = field(default_factory=dict)
    generation_variant: str = "clean"


def prepare_requirement(
    pair: dict[str, Any],
    variant: str,
    policy: str,
    clarification_answer: str | None = None,
) -> PreparedRequirement:
    if variant == "clean":
        return PreparedRequirement(
            text=pair["clean_requirement"],
            policy=policy,
            generation_variant="clean",
        )

    if policy == "direct":
        return PreparedRequirement(
            text=pair["smelly_requirement"],
            policy=policy,
            generation_variant="smelly",
        )

    if policy == "structured_rewrite":
        rewritten = rewrite_requirement(pair["smelly_requirement"])
        detection = detect_smell(pair["smelly_requirement"], pair["smell"])
        return PreparedRequirement(
            text=rewritten.text,
            policy=policy,
            mitigation_meta={
                "rewrite_changed": rewritten.changed,
                "rewrite_char_delta": len(rewritten.text) - len(pair["smelly_requirement"]),
                "evidence_class": "rq3_admissible",
                "oracle_access": False,
                "smell_type": detection.smell_type,
            },
            generation_variant="smelly",
        )

    if policy == "targeted_clarification":
        clarification = build_clarification(pair["smelly_requirement"])
        resolved = (
            apply_clarification_answer(
                pair["smelly_requirement"],
                clarification,
                answer=clarification_answer,
            )
            if clarification_answer is not None
            else None
        )
        detection = detect_smell(pair["smelly_requirement"], pair["smell"])
        return PreparedRequirement(
            text=resolved.text if resolved else pair["smelly_requirement"],
            policy=policy,
            mitigation_meta={
                "clarification_question": clarification.question,
                "clarification_signal": clarification.signal,
                "interaction_resolved": resolved is not None,
                "answer_source": "independent" if resolved else None,
                "evidence_class": "rq3_admissible",
                "oracle_access": False,
                "smell_type": detection.smell_type,
            },
            generation_variant="smelly",
        )

    if policy == "oracle_rewrite_upper_bound":
        rewritten = oracle_rewrite_upper_bound(pair["smelly_requirement"], pair)
        return PreparedRequirement(
            text=rewritten.text,
            policy=policy,
            mitigation_meta={
                "rewrite_changed": rewritten.changed,
                "rewrite_char_delta": len(rewritten.text) - len(pair["smelly_requirement"]),
                "evidence_class": "development_upper_bound",
                "oracle_access": True,
                "rq3_admissible": False,
            },
            generation_variant="clean",
        )

    if policy == "oracle_clarification_upper_bound":
        resolved = oracle_clarification_upper_bound(pair)
        return PreparedRequirement(
            text=resolved.text,
            policy=policy,
            mitigation_meta={
                "evidence_class": "development_upper_bound",
                "oracle_access": True,
                "rq3_admissible": False,
            },
            generation_variant="clean",
        )

    if policy in {"rewrite", "clarify"}:
        raise ValueError(
            f"legacy policy '{policy}' is ambiguous; use an explicit oracle-free "
            "policy or *_upper_bound"
        )

    raise ValueError(f"unknown mitigation policy: {policy}")
