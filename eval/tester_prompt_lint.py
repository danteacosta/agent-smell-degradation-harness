"""Offline lint: tester prompts must not contain generated implementation code.

Decision 5 of docs/preregistration/2026-11-07-pending-human-decisions.md (not
adopted) proposes that review-test authors see the requirement source only.  A
tester session that sees the generated implementation is *coupled* (see the
2026-10-29 literature-matrix entry on Konstantinou et al., arXiv 2607.05139).
This module makes that rule checkable if it is adopted.  It is descriptive and
non-gating: it makes no provider calls and changes no estimand.

Detection is deliberately conservative and literal: a prompt is flagged when a
non-trivial line of a supplied implementation source appears verbatim (after
whitespace normalisation) inside the prompt.  A fenced code block is reported
separately as a weaker signal because requirement text may legitimately quote
snippets.  A clean report does not prove the prompt is code-blind (paraphrased
or summarised code is not detected).
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

MIN_LINE_CHARS = 24
_FENCE = re.compile(r"```")
_WS = re.compile(r"\s+")
_TRIVIAL = re.compile(r"^[\W_]*$")


def _norm(text: str) -> str:
    return _WS.sub(" ", text).strip()


def _signature_lines(source: str, min_chars: int) -> list[str]:
    lines = []
    for raw in source.splitlines():
        line = _norm(raw)
        if len(line) >= min_chars and not _TRIVIAL.match(line):
            lines.append(line)
    return lines


def lint_tester_prompt(
    prompt: str,
    implementation_sources: Sequence[str] = (),
    *,
    min_line_chars: int = MIN_LINE_CHARS,
) -> dict[str, Any]:
    """Return findings for one prompt; ``coupled`` is True on a verbatim line match."""

    if not isinstance(prompt, str):
        raise ValueError("prompt must be a string")
    if min_line_chars < 1:
        raise ValueError("min_line_chars must be >= 1")
    normalised = _norm(prompt)
    matched = sorted(
        {
            line
            for source in implementation_sources
            for line in _signature_lines(source, min_line_chars)
            if line in normalised
        }
    )
    fences = len(_FENCE.findall(prompt)) // 2
    findings = []
    if matched:
        findings.append("verbatim_implementation_line")
    if fences:
        findings.append("fenced_code_block")
    return {
        "coupled": bool(matched),
        "findings": findings,
        "matched_line_count": len(matched),
        "fenced_block_count": fences,
    }


def lint_tester_prompts(
    records: Sequence[Mapping[str, Any]],
    *,
    min_line_chars: int = MIN_LINE_CHARS,
) -> dict[str, Any]:
    """Lint ``{"prompt_id", "prompt", "implementation_sources"}`` records.

    Rejects missing or duplicate ids so a prompt cannot be silently dropped.
    """

    seen: set[str] = set()
    results: dict[str, dict[str, Any]] = {}
    for record in records:
        prompt_id = str(record.get("prompt_id", "")).strip()
        if not prompt_id:
            raise ValueError("record without prompt_id")
        if prompt_id in seen:
            raise ValueError(f"duplicate prompt_id {prompt_id}")
        seen.add(prompt_id)
        results[prompt_id] = lint_tester_prompt(
            record.get("prompt", ""),
            tuple(record.get("implementation_sources", ())),
            min_line_chars=min_line_chars,
        )
    coupled = sorted(pid for pid, res in results.items() if res["coupled"])
    return {
        "n_prompts": len(results),
        "coupled_prompt_ids": coupled,
        "any_coupled": bool(coupled),
        "results": results,
        "limits": "literal-match lint; paraphrased or summarised code is not detected",
    }
