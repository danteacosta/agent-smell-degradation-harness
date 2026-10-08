"""Offline continuity check for provenance traces and an out-of-band receipt.

A trace file written inside the agent's own host can be truncated or emptied by
the agent (Qin et al., arXiv 2609.30266, preprint). Structural checks catch gaps
and re-linking in the middle of a file; they cannot detect deletion of a suffix
or of the whole file. That requires a receipt held outside the agent's control.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def trace_receipt(path: Path | str) -> dict[str, Any]:
    """Return the event count and SHA-256 of the trace bytes for out-of-band storage."""
    data = Path(path).read_bytes()
    return {
        "event_count": len([line for line in data.splitlines() if line.strip()]),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def verify_trace_continuity(
    path: Path | str, *, receipt: dict[str, Any] | None = None
) -> list[str]:
    """Return a list of integrity problems; an empty list means none were found."""
    problems: list[str] = []
    try:
        data = Path(path).read_bytes()
    except FileNotFoundError:
        return ["trace file is missing"]
    seen: set[str] = set()
    previous_id: str | None = None
    count = 0
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return ["trace is not valid UTF-8"]
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            problems.append(f"line {line_no}: not valid JSON")
            continue
        if not isinstance(record, dict):
            problems.append(f"line {line_no}: record is not an object")
            continue
        event_id = record.get("event_id")
        if not isinstance(event_id, str) or not event_id.strip():
            problems.append(f"line {line_no}: nonempty string event_id required")
            count += 1
            continue
        if event_id in seen:
            problems.append(f"line {line_no}: duplicate event_id {event_id}")
        seen.add(event_id)
        if type(record.get("sequence_number")) is not int or record.get("sequence_number") != count:
            problems.append(
                f"line {line_no}: sequence_number {record.get('sequence_number')!r}, expected {count}"
            )
        if record.get("parent_event_id") != previous_id:
            problems.append(f"line {line_no}: parent_event_id does not match the previous event")
        previous_id = event_id
        count += 1
    if receipt is not None:
        if count != receipt.get("event_count"):
            problems.append(f"event count {count} differs from receipt {receipt.get('event_count')}")
        if hashlib.sha256(data).hexdigest() != receipt.get("sha256"):
            problems.append("SHA-256 differs from receipt")
    return problems
