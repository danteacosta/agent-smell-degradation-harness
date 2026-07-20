from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SmellDetection:
    detected: bool
    smell_type: str


def detect_smell(text: str, smell_meta: dict[str, Any]) -> SmellDetection:
    smell_type = smell_meta.get("type", "")
    detected = bool(smell_type)
    return SmellDetection(detected=detected, smell_type=smell_type)
