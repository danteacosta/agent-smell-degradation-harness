from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from mitigation.templates import rewrite_from_oracle_spec


@dataclass(frozen=True)
class RewriteResult:
    text: str
    changed: bool


def rewrite_requirement(
    smelly_text: str,
    pair: dict[str, Any],
    *,
    mode: Literal["oracle", "template"] = "oracle",
    task_family: str = "codegen",
) -> RewriteResult:
    if mode == "oracle":
        clean = pair["clean_requirement"]
        return RewriteResult(text=clean, changed=smelly_text != clean)

    smell_type = pair["smell"]["type"]
    oracle_spec = pair["oracle_spec"][task_family]
    text = rewrite_from_oracle_spec(smell_type, oracle_spec, task_family=task_family)
    return RewriteResult(text=text, changed=smelly_text != text)
