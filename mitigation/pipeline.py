from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mitigation.clarify import apply_clarification_answer, build_clarification
from mitigation.detect import detect_smell
from mitigation.rewrite import rewrite_requirement


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

    if policy == "rewrite":
        rewritten = rewrite_requirement(pair["smelly_requirement"], pair)
        detection = detect_smell(pair["smelly_requirement"], pair["smell"])
        return PreparedRequirement(
            text=rewritten.text,
            policy=policy,
            mitigation_meta={
                "rewrite_changed": rewritten.changed,
                "smell_type": detection.smell_type,
            },
            generation_variant="clean",
        )

    if policy == "clarify":
        clarification = build_clarification(pair)
        resolved = apply_clarification_answer(
            pair,
            clarification,
            answer=clarification.simulated_answer,
        )
        detection = detect_smell(pair["smelly_requirement"], pair["smell"])
        return PreparedRequirement(
            text=resolved.text,
            policy=policy,
            mitigation_meta={
                "clarification_question": clarification.question,
                "clarification_answer": clarification.simulated_answer,
                "smell_type": detection.smell_type,
            },
            generation_variant="clean",
        )

    detection = detect_smell(pair["smelly_requirement"], pair["smell"])
    return PreparedRequirement(
        text=pair["smelly_requirement"],
        policy=policy,
        mitigation_meta={"smell_type": detection.smell_type},
        generation_variant="smelly",
    )
