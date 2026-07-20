from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RewriteResult:
    text: str
    changed: bool


def rewrite_requirement(smelly_text: str, pair: dict[str, Any]) -> RewriteResult:
    clean = pair["clean_requirement"]
    return RewriteResult(text=clean, changed=smelly_text != clean)
