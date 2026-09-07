"""Strict JSON syntax shared by the experimental response and audit boundaries."""
import json
from typing import Any


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _reject_constant(_):
    raise ValueError("non-JSON constant")


def load_json(raw: str) -> Any:
    """Reject duplicate keys and nonstandard constants; callers own size limits."""
    return json.loads(raw, object_pairs_hook=_unique_keys, parse_constant=_reject_constant)
