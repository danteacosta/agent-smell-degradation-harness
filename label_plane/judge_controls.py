"""Synthetic evaluator diagnostics. Never a source of confirmatory labels."""

from __future__ import annotations

import hashlib
import json
from collections import Counter

from label_plane.exploratory_judge import (
    JudgeRequest, ReferenceConstraint, parse_judge_response, serialize_judge_request,
)


def fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def build_controls() -> dict:
    """Original toy cases with explicit, local construction oracles; no corpus input."""
    seeds = (
        ("When an account is locked, the system rejects login.",
         "When an account is locked, the system accepts login."),
        ("When inventory is zero, the system rejects purchase.",
         "When inventory is zero, the system accepts purchase."),
        ("When a token has expired, the system rejects access.",
         "When a token has expired, the system accepts access."),
    )
    cases = []
    for index, (reference, opposite) in enumerate(seeds):
        unrelated = "The system displays a blue header."
        for operation, criteria, expected in (
            ("literal", reference + "\n" + unrelated, True),
            ("reordered", unrelated + "\n" + reference, True),
            ("deleted", unrelated, False),
            ("contradicted", opposite + "\n" + unrelated, False),
        ):
            opaque = fingerprint(["judge-controls/v1", index, operation])[:24]
            request = JudgeRequest(opaque, criteria, (ReferenceConstraint("c1", reference),))
            cases.append({"request": serialize_judge_request(request),
                          "oracle": {"seed_id": index, "operation": operation,
                                     "covered": expected}})
    body = {"schema_version": "judge-controls/v1", "evidence_scope": "synthetic_diagnostic",
            "cases": cases}
    return {**body, "pack_sha256": fingerprint(body)}


def score_controls(rows: list[dict], configurations: list[str], repetitions: int = 3) -> dict:
    """Score raw responses against a fixed plan, retaining missing/error denominators.

    Configuration IDs must be frozen SHA-256 fingerprints of model, prompt,
    decoding settings and rubric; they are supplied by the operator.
    """
    if (not configurations or len(set(configurations)) != len(configurations)
            or any(not isinstance(c, str) or len(c) != 64
                   or any(ch not in "0123456789abcdef" for ch in c) for c in configurations)):
        raise ValueError("unique lowercase configuration SHA-256 values are required")
    if type(repetitions) is not int or not 1 <= repetitions <= 100:
        raise ValueError("repetitions must be an integer between 1 and 100")
    pack = build_controls()
    cases = {c["request"]["occurrence_id"]: c for c in pack["cases"]}
    indexed = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "pack_sha256", "configuration_sha256", "replication_id", "occurrence_id", "raw_response"
        }:
            raise ValueError("invalid result fields")
        if (not isinstance(row["configuration_sha256"], str)
                or not isinstance(row["occurrence_id"], str)
                or type(row["replication_id"]) is not int):
            raise ValueError("invalid result identifiers")
        key = (row["configuration_sha256"], row["replication_id"], row["occurrence_id"])
        if (row["pack_sha256"] != pack["pack_sha256"]
                or key[0] not in configurations or type(key[1]) is not int
                or not 0 <= key[1] < repetitions or key[2] not in cases or key in indexed):
            raise ValueError("result does not match the frozen plan or is duplicated")
        if row["raw_response"] is not None and not isinstance(row["raw_response"], str):
            raise ValueError("raw_response must be a string or null for a failed call")
        indexed[key] = row["raw_response"]
    reports = {}
    for config in configurations:
        counts = Counter(planned=len(cases) * repetitions, completed=0, missing=0,
                         invalid_or_failed=0, abstained=0, correct=0, false_covered=0,
                         contradictory_response=0)
        by_operation = {op: Counter(planned=3 * repetitions, correct=0) for op in
                        ("literal", "reordered", "deleted", "contradicted")}
        outcomes = {}
        for rep in range(repetitions):
            for identifier, case in cases.items():
                key = (config, rep, identifier)
                if key not in indexed:
                    counts["missing"] += 1
                    continue
                try:
                    response = parse_judge_response(indexed[key], case["request"])
                except (ValueError, TypeError):
                    counts["invalid_or_failed"] += 1
                    continue
                counts["completed"] += 1
                status = response.constraint_assessments[0].status
                oracle = case["oracle"]
                outcomes[(rep, oracle["seed_id"], oracle["operation"])] = (response.label, status)
                abstained = status == "uncertain" or response.label == "not_visible"
                counts["abstained"] += abstained
                inconsistent = response.label == "clean" and status != "covered"
                counts["contradictory_response"] += inconsistent
                counts["false_covered"] += (not oracle["covered"] and status == "covered")
                correct = (not abstained and not inconsistent and (
                    (oracle["covered"] and status == "covered" and response.label == "clean")
                    or (not oracle["covered"] and status == "omitted" and response.label != "clean")))
                counts["correct"] += correct
                by_operation[oracle["operation"]]["correct"] += correct
        paired = switches = 0
        for rep in range(repetitions):
            for seed in range(3):
                a, b = outcomes.get((rep, seed, "literal")), outcomes.get((rep, seed, "reordered"))
                if a is not None and b is not None:
                    paired += 1
                    switches += a != b
        reports[config] = {**dict(counts), "correct_over_planned": counts["correct"] / counts["planned"],
                           "by_operation": {k: dict(v) for k, v in by_operation.items()},
                           "order_pairs_planned": 3 * repetitions, "order_pairs_completed": paired,
                           "order_switches": switches,
                           "order_switch_rate": switches / paired if paired else None}
    return {"schema_version": "judge-controls-report/v1", "pack_sha256": pack["pack_sha256"],
            "evidence_scope": "synthetic_diagnostic", "confirmatory_eligible": False,
            "human_calibration": "absent", "configurations": reports}
