"""Optional secondary LLM-judge evidence; never the primary executable label."""

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True, slots=True)
class SecondaryJudgement:
    label: str
    source: str = "llm_judge_secondary"


def secondary_judge(
    judge: Callable[[dict[str, Any]], str], artifact: dict[str, Any]
) -> SecondaryJudgement:
    return SecondaryJudgement(label=judge(artifact))


__all__ = ["SecondaryJudgement", "secondary_judge"]
