from __future__ import annotations

from enum import Enum


class Decision(str, Enum):
    APPROVE = "approve"
    WARN = "warn"
    CLARIFY = "clarify"

    def __str__(self) -> str:
        return self.value
