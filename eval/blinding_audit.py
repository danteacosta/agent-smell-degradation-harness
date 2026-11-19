"""Offline audit of frozen annotator-facing packets for condition/outcome leakage.

``label_plane.annotation_protocol.validate_blinded_payload`` only inspects the
top-level keys of each packet. This audit adds what the pre-pilot readiness flag
``blinding_verified`` implicitly assumes: nested keys, extra fields, pair-arm
hints in item ids and tell-tale phrases in the presented text. It is a
heuristic screen, not proof of blinding. It does NOT set ``blinding_verified``
in any plan and approves nothing; that remains a human decision.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

ALLOWED_FIELDS = frozenset({"item_id", "presented_text", "rubric_version", "duplicate_subset"})
_FORBIDDEN_KEY = re.compile(
    r"(variant|defect|oracle|model|provider|arm|condition|clean|label|trace|t[1-4]_|outcome|"
    r"ground_?truth|expected|baseline|smell|artifact|run_id|replication)",
    re.I,
)
_ARM_IN_ID = re.compile(r"(^|[-_.:/])(clean|defective|defect|control|treated|b0|b3)([-_.:/]|$)", re.I)
_TELLTALE_TEXT = re.compile(
    r"(clean variant|defective variant|ground truth|oracle label|injected (defect|smell)|"
    r"smell[- ]injected|this requirement (is|was) (clean|defective))",
    re.I,
)


def _walk_keys(value: Any, path: str = "") -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            here = f"{path}.{key}" if path else str(key)
            yield here
            yield from _walk_keys(child, here)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_keys(child, f"{path}[{index}]")


def audit_packets(packets: Iterable[Mapping[str, Any]]) -> dict[str, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()
    rows = list(packets)
    if not rows:
        errors.append("no packets supplied")
    for position, packet in enumerate(rows):
        if not isinstance(packet, Mapping):
            errors.append(f"packet {position} is not an object")
            continue
        item_id = str(packet.get("item_id", ""))
        tag = item_id or f"#{position}"
        if not item_id:
            errors.append(f"packet {position} has no item_id")
        elif item_id in seen:
            errors.append(f"duplicate item_id {item_id!r}")
        seen.add(item_id)
        for extra in sorted(set(packet) - ALLOWED_FIELDS):
            errors.append(f"{tag}: field {extra!r} is outside the blinded packet schema")
        for key_path in _walk_keys(packet):
            leaf = re.split(r"[.\[]", key_path)[-1].rstrip("]")
            if _FORBIDDEN_KEY.search(leaf):
                errors.append(f"{tag}: key {key_path!r} looks like experimental metadata")
        if _ARM_IN_ID.search(item_id):
            errors.append(f"{tag}: item_id encodes a pair arm or condition")
        text = packet.get("presented_text")
        if not isinstance(text, str) or not text.strip():
            errors.append(f"{tag}: presented_text is empty or not a string")
        elif _TELLTALE_TEXT.search(text):
            warnings.append(f"{tag}: presented_text contains a condition/label phrase")
    return {"errors": sorted(set(errors)), "warnings": sorted(set(warnings))}


def _load(path: Path) -> list[Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    return data if isinstance(data, list) else [data]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--packets", type=Path, required=True, help="JSON list or JSONL of annotator packets")
    args = p.parse_args(argv)
    report = audit_packets(_load(args.packets))
    print(json.dumps(report, indent=2))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
