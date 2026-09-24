"""Strict adapter for trusted RealWorld article-author browser reports."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import uuid

from eval.focus_chain_executor import container_command


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


def _read_bounded_regular(path: Path, maximum: int) -> bytes | None:
    descriptor = None
    try:
        flags = (os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                 | getattr(os, "O_NONBLOCK", 0))
        descriptor = os.open(path, flags)
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > maximum:
            return None
        chunks = []
        remaining = maximum + 1
        while remaining:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        return raw if len(raw) <= maximum else None
    except OSError:
        return None
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass


def _stage_trusted_app(output: Path, raw: bytes) -> Path:
    trusted_input = output / "trusted-input"
    trusted_input.mkdir(mode=0o700)
    app = trusted_input / "app.html"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(app, flags, 0o400)
    try:
        remaining = memoryview(raw)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError("unable to stage trusted app")
            remaining = remaining[written:]
        os.fchmod(descriptor, 0o400)
    finally:
        os.close(descriptor)
    return trusted_input


def _bounded_diagnostic(prefix: str, error: OSError) -> str:
    return f"{prefix}: {error}"[:500]


def _cleanup_container(name: str) -> str | None:
    try:
        subprocess.run(
            ["docker", "rm", "--force", name],
            capture_output=True,
            timeout=30,
            check=False,
        )
        return None
    except subprocess.TimeoutExpired:
        return "docker cleanup timed out"
    except OSError as error:
        return _bounded_diagnostic("docker cleanup failed", error)


def execute(image: str, inputs: Path, output: Path, timeout: int = 90) -> dict:
    """Run one bounded offline HTML artifact and retain its diagnostic evidence."""
    output.mkdir(parents=True, exist_ok=False)
    name = "realworld-author-ui-" + uuid.uuid4().hex
    app = _read_bounded_regular(inputs / "app.html", 200_000)
    if app is None:
        raise ValueError("bounded regular app.html required")
    trusted_input = _stage_trusted_app(output, app)
    command = container_command(image, trusted_input, output, name)
    app_hash = hashlib.sha256(app).hexdigest()
    (output / "container-command.json").write_text(json.dumps(command, indent=2))

    run_outcome = None
    try:
        with (output / "container.log").open("wb") as log:
            try:
                result = subprocess.run(
                    command,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=timeout,
                    check=False,
                )
                returncode = result.returncode
            except subprocess.TimeoutExpired:
                returncode = 124
                run_outcome = {"category": "timeout"}
            except OSError as error:
                returncode = 125
                run_outcome = {
                    "category": "execution_failure",
                    "reason": _bounded_diagnostic("docker execution failed", error),
                }
    finally:
        cleanup_error = _cleanup_container(name)

    if run_outcome is not None:
        outcome = run_outcome
        if cleanup_error is not None:
            outcome["cleanup_error"] = cleanup_error
    elif cleanup_error is not None:
        outcome = {
            "category": "cleanup_failure",
            "cleanup_error": cleanup_error,
        }
    else:
        raw = _read_bounded_regular(output / "report.json", 100_000)
        outcome = classify_report(raw, returncode)

    if outcome["category"] not in {"timeout", "malformed_report"}:
        if outcome["category"] not in {"execution_failure", "cleanup_failure"}:
            report = json.loads(raw)
            if report["app_sha256"] != app_hash:
                outcome = {
                    "category": "browser_failure",
                    "reason": "executed app hash mismatch",
                }

    if outcome["category"] in {
        "pass", "target_only_failure", "target_not_evaluable",
    }:
        expected_png_names = set(report["screenshots"])
        png_names = set()
        unexpected = None
        for path in output.glob("*.png"):
            if path.name not in expected_png_names:
                unexpected = path.name
                break
            png_names.add(path.name)
        if unexpected is not None or png_names != expected_png_names:
            missing = sorted(expected_png_names - png_names)
            reason = (f"unexpected screenshot: {unexpected}" if unexpected else
                      f"invalid screenshot: {missing[0]}")
            outcome = {
                "category": "browser_failure",
                "reason": reason,
            }
        else:
            for screenshot_name in _SCREENSHOTS:
                screenshot = _read_bounded_regular(
                    output / screenshot_name, 4_000_000)
                if screenshot is None or not screenshot.startswith(b"\x89PNG\r\n\x1a\n"):
                    outcome = {
                        "category": "browser_failure",
                        "reason": f"invalid screenshot: {screenshot_name}",
                    }
                    break

    receipt = {
        "image": image,
        "app_sha256": app_hash,
        "returncode": returncode,
        **outcome,
    }
    (output / "executor.json").write_text(json.dumps(receipt, indent=2))
    return receipt
