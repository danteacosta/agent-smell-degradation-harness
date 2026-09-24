"""Strict adapter for trusted RealWorld article-author browser reports."""
from __future__ import annotations

import json
import re


SCHEMA_VERSION = "realworld-author-ui-browser/v1"
ASSERTION_IDS = (
    "author_sees_delete_article",
    "non_author_does_not_see_delete_article",
)
FIXTURE_IDS = ("article-alice", "article-bob")
CONTEXT_IDS = ("author", "non-author")
REASON_IDS = (
    "route_mismatch",
    "title_missing",
    "body_missing",
    "article_author_missing",
)

_FINAL_URL = "http://fixture.invalid/article/bounded-ui-case"
_PAIRS = tuple((fixture_id, context_id)
               for fixture_id in FIXTURE_IDS for context_id in CONTEXT_IDS)
_SCREENSHOTS = tuple(f"{fixture_id}-{context_id}.png"
                     for fixture_id, context_id in _PAIRS)
_COMMON_FIELDS = {
    "schema_version", "status", "app_sha256", "runner_version",
    "browser_sandbox", "isolation",
}
_COMPLETE_FIELDS = _COMMON_FIELDS | {
    "browser_version", "viewport", "sample_grid", "observations",
    "target_failed", "target_not_evaluable", "not_evaluable_reasons",
    "screenshots",
}
_OPERATIONAL_FIELDS = _COMMON_FIELDS | {"error", "browser_started"}
_OBSERVATION_FIELDS = {
    "fixture_id", "context_id", "final_url", "title", "body",
    "article_author", "delete_buttons", "runtime_errors", "screenshot",
}
_COUNT_FIELDS = {"matched", "perceptible"}
_RUNTIME_ERROR_FIELDS = {"kind", "message"}
_REASON_FIELDS = {"assertion_id", "fixture_id", "context_id", "reason"}


def _invalid() -> dict:
    return {
        "category": "malformed_report",
        "reason": "incomplete or inconsistent trusted report",
    }


def _unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def _bounded_string(value: object, maximum: int, *, nonempty: bool = False) -> bool:
    return (isinstance(value, str) and len(value) <= maximum
            and (not nonempty or bool(value)))


def _valid_common(value: dict) -> bool:
    return (
        value.get("schema_version") == SCHEMA_VERSION
        and value.get("status") in {"complete", "interface_failure", "browser_failure"}
        and isinstance(value.get("app_sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", value["app_sha256"]) is not None
        and value.get("runner_version") == "1"
        and value.get("browser_sandbox") is False
        and _bounded_string(value.get("isolation"), 500, nonempty=True)
    )


def _valid_count(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != _COUNT_FIELDS:
        return False
    matched = value["matched"]
    perceptible = value["perceptible"]
    return (
        type(matched) is int
        and type(perceptible) is int
        and 0 <= matched <= 20
        and 0 <= perceptible <= matched
    )


def _valid_runtime_errors(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) <= 20
        and all(
            isinstance(item, dict)
            and set(item) == _RUNTIME_ERROR_FIELDS
            and item["kind"] in {"console", "page"}
            and _bounded_string(item["message"], 500)
            for item in value
        )
    )


def _valid_viewport(value: object) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"width", "height"}
        and type(value["width"]) is int
        and value["width"] == 1000
        and type(value["height"]) is int
        and value["height"] == 720
    )


def _valid_sample_grid(value: object) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"dimension", "inset_ratio"}
        and type(value["dimension"]) is int
        and value["dimension"] == 5
        and type(value["inset_ratio"]) is float
        and value["inset_ratio"] == 0.08
    )


def _valid_observations(value: object) -> bool:
    if not isinstance(value, list) or len(value) != len(_PAIRS):
        return False
    for observation, (fixture_id, context_id), screenshot in zip(
            value, _PAIRS, _SCREENSHOTS):
        if (
            not isinstance(observation, dict)
            or set(observation) != _OBSERVATION_FIELDS
            or observation["fixture_id"] != fixture_id
            or observation["context_id"] != context_id
            or not isinstance(observation["final_url"], str)
            or observation["screenshot"] != screenshot
            or not all(_valid_count(observation[field]) for field in (
                "title", "body", "article_author", "delete_buttons"))
            or not _valid_runtime_errors(observation["runtime_errors"])
        ):
            return False
    return True


def _valid_target_set(value: object) -> bool:
    return (
        isinstance(value, list)
        and all(isinstance(item, str) and item in ASSERTION_IDS for item in value)
        and value == sorted(set(value))
    )


def _valid_reasons(value: object) -> bool:
    if not isinstance(value, list):
        return False
    keys = []
    for item in value:
        if (
            not isinstance(item, dict)
            or set(item) != _REASON_FIELDS
            or item["assertion_id"] not in ASSERTION_IDS
            or item["fixture_id"] not in FIXTURE_IDS
            or item["context_id"] not in CONTEXT_IDS
            or item["reason"] not in REASON_IDS
        ):
            return False
        keys.append((item["assertion_id"], item["fixture_id"],
                     item["context_id"], item["reason"]))
    return keys == sorted(set(keys))


def _recompute(observations: list[dict]) -> tuple[list[str], list[str], list[dict]]:
    failed = set()
    reasons = []
    for observation in observations:
        context_id = observation["context_id"]
        assertion_id = (ASSERTION_IDS[0] if context_id == "author" else ASSERTION_IDS[1])
        violated = []
        if observation["final_url"] != _FINAL_URL:
            violated.append("route_mismatch")
        for field, reason in (
            ("title", "title_missing"),
            ("body", "body_missing"),
            ("article_author", "article_author_missing"),
        ):
            if observation[field]["perceptible"] < 1:
                violated.append(reason)
        if violated:
            reasons.extend({
                "assertion_id": assertion_id,
                "fixture_id": observation["fixture_id"],
                "context_id": context_id,
                "reason": reason,
            } for reason in violated)
        elif context_id == "author":
            if observation["delete_buttons"]["perceptible"] == 0:
                failed.add(assertion_id)
        elif observation["delete_buttons"]["perceptible"] >= 1:
            failed.add(assertion_id)
    reasons.sort(key=lambda item: (
        item["assertion_id"], item["fixture_id"], item["context_id"], item["reason"]
    ))
    not_evaluable = sorted({item["assertion_id"] for item in reasons})
    return sorted(failed), not_evaluable, reasons


def _classify_complete(value: dict, returncode: int) -> dict:
    if (
        set(value) != _COMPLETE_FIELDS
        or not _bounded_string(value["browser_version"], 200, nonempty=True)
        or not _valid_viewport(value["viewport"])
        or not _valid_sample_grid(value["sample_grid"])
        or not _valid_observations(value["observations"])
        or not _valid_target_set(value["target_failed"])
        or not _valid_target_set(value["target_not_evaluable"])
        or not _valid_reasons(value["not_evaluable_reasons"])
        or value["screenshots"] != list(_SCREENSHOTS)
    ):
        return _invalid()

    failed, not_evaluable, reasons = _recompute(value["observations"])
    if (
        value["target_failed"] != failed
        or value["target_not_evaluable"] != not_evaluable
        or value["not_evaluable_reasons"] != reasons
    ):
        return _invalid()

    category = ("target_not_evaluable" if not_evaluable else
                "target_only_failure" if failed else "pass")
    expected_returncode = {
        "pass": 0,
        "target_only_failure": 10,
        "target_not_evaluable": 11,
    }[category]
    if type(returncode) is not int or returncode != expected_returncode:
        return _invalid()
    return {
        "category": category,
        "target_failed": failed,
        "target_not_evaluable": not_evaluable,
        "not_evaluable_reasons": reasons,
    }


def _classify_operational(value: dict, returncode: int) -> dict:
    if (
        set(value) != _OPERATIONAL_FIELDS
        or not _bounded_string(value["error"], 1500)
        or type(value["browser_started"]) is not bool
        or type(returncode) is not int
    ):
        return _invalid()
    status = value["status"]
    if status == "interface_failure":
        if value["browser_started"] is not False or returncode != 20:
            return _invalid()
    elif status == "browser_failure":
        if returncode != 21:
            return _invalid()
    else:
        return _invalid()
    return {"category": status, "reason": value["error"]}


def classify_report(raw: bytes | None, returncode: int) -> dict:
    """Validate and classify one closed trusted-runner report."""
    try:
        if not isinstance(raw, bytes) or not raw or len(raw) > 100_000:
            return _invalid()
        value = json.loads(raw, object_pairs_hook=_unique_fields)
        if not isinstance(value, dict) or not _valid_common(value):
            return _invalid()
        if value["status"] == "complete":
            return _classify_complete(value, returncode)
        return _classify_operational(value, returncode)
    except (KeyError, RecursionError, TypeError, ValueError):
        return _invalid()
