"""Content-bound locations in private artifacts, not semantic support judgments."""
from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA = "artifact-segments/v1"
POLICY = "utf8-newline-window-400/v1"
MAX_TEXT_CHARS = 20_000
MAX_SEGMENTS = 256
WINDOW_CHARS = 400


class EvidenceContractError(ValueError):
    """A fixed error code safe for redacted reports; never include input text."""


def build_snapshot(text: str) -> dict[str, Any]:
    """Partition original UTF-8 bytes; identical text and policy give identical IDs."""
    if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT_CHARS:
        raise EvidenceContractError("invalid_artifact")
    try:
        encoded = text.encode("utf-8")
    except UnicodeError as exc:
        raise EvidenceContractError("invalid_artifact") from exc
    artifact_hash = hashlib.sha256(encoded).hexdigest()
    segments = []
    start_char = start_byte = 0
    while start_char < len(text):
        end_char = min(start_char + WINDOW_CHARS, len(text))
        if end_char < len(text):
            newline = text.rfind("\n", start_char, end_char)
            if newline >= start_char:
                end_char = newline + 1
        span = text[start_char:end_char]
        end_byte = start_byte + len(span.encode("utf-8"))
        identity = f"{POLICY}:{artifact_hash}:{start_byte}:{end_byte}"
        identifier = "seg-" + hashlib.sha256(identity.encode("ascii")).hexdigest()[:24]
        segments.append({"id": identifier, "start_byte": start_byte,
                         "end_byte": end_byte, "text": span})
        start_char, start_byte = end_char, end_byte
    if len(segments) > MAX_SEGMENTS or len({s["id"] for s in segments}) != len(segments):
        raise EvidenceContractError("invalid_artifact")
    return {"schema_version": SCHEMA, "policy": POLICY, "text": text,
            "artifact_sha256": artifact_hash, "byte_length": len(encoded),
            "segments": segments}


def validate_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Return a fresh canonical copy only when all serialized fields are exact."""
    fields = {"schema_version", "policy", "text", "artifact_sha256", "byte_length", "segments"}
    if not isinstance(snapshot, dict) or set(snapshot) != fields:
        raise EvidenceContractError("invalid_snapshot")
    spans = snapshot["segments"]
    if not isinstance(spans, list) or not 1 <= len(spans) <= MAX_SEGMENTS:
        raise EvidenceContractError("invalid_snapshot")
    if type(snapshot["byte_length"]) is not int:
        raise EvidenceContractError("invalid_snapshot")
    for span in spans:
        if (not isinstance(span, dict) or set(span) != {"id", "start_byte", "end_byte", "text"}
                or type(span["start_byte"]) is not int or type(span["end_byte"]) is not int
                or not isinstance(span["id"], str) or len(span["id"]) > 64
                or not isinstance(span["text"], str) or len(span["text"]) > WINDOW_CHARS):
            raise EvidenceContractError("invalid_snapshot")
    expected = build_snapshot(snapshot["text"])
    # Equality alone would accept bool/float offsets as integers. Types above
    # and exact canonical serialization jointly enforce the wire contract.
    try:
        same = json.dumps(snapshot, sort_keys=True, allow_nan=False) == json.dumps(expected, sort_keys=True)
    except (TypeError, ValueError, RecursionError) as exc:
        raise EvidenceContractError("invalid_snapshot") from exc
    if not same:
        raise EvidenceContractError("invalid_snapshot")
    return expected


def resolve_segments(snapshot: dict[str, Any], ids: list[str]) -> list[dict[str, Any]]:
    """Resolve only this artifact's IDs; no reference lookup, retrieval, or repair."""
    canonical = validate_snapshot(snapshot)
    if (not isinstance(ids, list) or len(ids) > MAX_SEGMENTS
            or any(not isinstance(identifier, str) or len(identifier) > 64 for identifier in ids)):
        raise EvidenceContractError("invalid_segment_inventory")
    if len(set(ids)) != len(ids):
        raise EvidenceContractError("duplicate_segment")
    by_id = {span["id"]: span for span in canonical["segments"]}
    if any(identifier not in by_id for identifier in ids):
        raise EvidenceContractError("unknown_segment")
    return [by_id[identifier] for identifier in ids]
