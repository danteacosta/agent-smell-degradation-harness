"""Offline qualification of obligation-level evidence diagnostics.

This module evaluates already frozen decisions.  It does not fit thresholds,
call a provider, or create scientific labels.  Expected decisions belong to
the label plane and must never be exposed to a detector under evaluation.
"""
from __future__ import annotations

import hashlib
import json
import math
import re


FAMILIES = {
    "wrong_binding": "reject",
    "valid_alternative": "support",
    "insufficient_evidence": "abstain",
}
DECISIONS = frozenset(FAMILIES.values())
SHA256 = re.compile(r"^[0-9a-f]{64}$")
LABEL_FIELDS = ("record_id", "pair_id", "project_id", "constraint_id", "family", "expected_decision")


def _rate(correct: int, total: int) -> float:
    return correct / total


def assess_evidence_diagnostic(packet: dict) -> dict:
    """Validate a frozen packet and score its evaluation-project decisions."""
    if not isinstance(packet, dict) or packet.get("schema_version") != "evidence-diagnostic-qualification/v1":
        raise ValueError("wrong evidence qualification schema")
    split = packet.get("project_split")
    if not isinstance(split, dict) or not split:
        raise ValueError("project split required")
    if not all(isinstance(k, str) and k and v in {"development", "calibration", "evaluation"}
               for k, v in split.items()):
        raise ValueError("invalid project split")
    threshold = packet.get("diagnostic_threshold")
    if (type(threshold) not in (int, float) or not math.isfinite(threshold)
            or not 0 <= threshold <= 1
            or packet.get("threshold_selected_on") != "calibration"):
        raise ValueError("diagnostic threshold must be frozen on calibration projects")

    review = packet.get("label_review")
    if not isinstance(review, dict):
        raise ValueError("label review manifest required")
    reviewers = review.get("reviewer_ids")
    if (not isinstance(reviewers, list) or len(reviewers) < 2
            or any(not isinstance(value, str) or not value for value in reviewers)
            or len(set(reviewers)) != len(reviewers)):
        raise ValueError("at least two distinct label reviewers required")
    if (review.get("predictions_hidden_during_review") is not True
            or review.get("completed_before_scoring") is not True):
        raise ValueError("label review must be blind and frozen before scoring")
    for key in ("rubric_sha256", "frozen_labels_sha256"):
        if not isinstance(review.get(key), str) or not SHA256.fullmatch(review[key]):
            raise ValueError(f"valid {key} required")

    frozen_labels = packet.get("frozen_labels")
    if not isinstance(frozen_labels, list) or not frozen_labels:
        raise ValueError("frozen label inventory required")
    scheduled = {}
    for label in frozen_labels:
        if (not isinstance(label, dict) or set(label) != set(LABEL_FIELDS)
                or any(not isinstance(label[key], str) or not label[key] for key in LABEL_FIELDS)):
            raise ValueError("invalid frozen label identity")
        if label["record_id"] in scheduled:
            raise ValueError("duplicate frozen record_id")
        scheduled[label["record_id"]] = label
    canonical_labels = json.dumps(
        {"project_split": split, "labels": frozen_labels},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")
    if hashlib.sha256(canonical_labels).hexdigest() != review["frozen_labels_sha256"]:
        raise ValueError("frozen label inventory does not match its SHA-256 receipt")

    records = packet.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("records required")
    seen: set[str] = set()
    evaluation = []
    for row in records:
        if not isinstance(row, dict):
            raise ValueError("record must be an object")
        required = ("record_id", "pair_id", "project_id", "constraint_id", "family",
                    "expected_decision", "diagnostic_decision", "baseline_decision")
        if any(not isinstance(row.get(key), str) or not row[key] for key in required):
            raise ValueError("record identity and decisions must be non-empty strings")
        if row["record_id"] in seen:
            raise ValueError("duplicate record_id")
        label = {key: row[key] for key in LABEL_FIELDS}
        if scheduled.get(row["record_id"]) != label:
            raise ValueError("record differs from frozen label identity")
        seen.add(row["record_id"])
        if row["project_id"] not in split:
            raise ValueError("record project absent from frozen split")
        family = row["family"]
        if family not in FAMILIES or row["expected_decision"] != FAMILIES[family]:
            raise ValueError("family and expected decision disagree")
        if row["diagnostic_decision"] not in DECISIONS or row["baseline_decision"] not in DECISIONS:
            raise ValueError("invalid detector decision")
        if split[row["project_id"]] == "evaluation":
            evaluation.append(row)

    if seen != set(scheduled):
        raise ValueError("results do not exactly cover the frozen label inventory")

    if not evaluation or {row["family"] for row in evaluation} != set(FAMILIES):
        raise ValueError("evaluation projects must contain every qualification family")

    pair_projects: dict[str, set[str]] = {}
    pair_constraints: dict[str, set[str]] = {}
    for row in records:
        pair_projects.setdefault(row["pair_id"], set()).add(row["project_id"])
        pair_constraints.setdefault(row["pair_id"], set()).add(row["constraint_id"])
    if any(len(projects) != 1 for projects in pair_projects.values()):
        raise ValueError("pair_id must not cross projects")
    if any(len(constraints) != 1 for constraints in pair_constraints.values()):
        raise ValueError("pair_id must identify one frozen constraint")

    systems = {}
    for key in ("baseline_decision", "diagnostic_decision"):
        by_family = {}
        total_correct = 0
        for family, expected in FAMILIES.items():
            subset = [row for row in evaluation if row["family"] == family]
            correct = sum(row[key] == expected for row in subset)
            total_correct += correct
            by_family[family] = {"correct": correct, "total": len(subset), "rate": _rate(correct, len(subset))}
        systems[key.removesuffix("_decision")] = {
            "scheduled_denominator": len(evaluation),
            "strict_correct": total_correct,
            "strict_accuracy": _rate(total_correct, len(evaluation)),
            "by_family": by_family,
        }

    diagnostic = systems["diagnostic"]
    baseline = systems["baseline"]
    return {
        "schema_version": "evidence-diagnostic-qualification-report/v1",
        "confirmatory_eligible": False,
        "evaluation_projects": sorted({row["project_id"] for row in evaluation}),
        "label_review": {
            "reviewer_count": len(reviewers),
            "predictions_hidden_during_review": True,
            "completed_before_scoring": True,
            "rubric_sha256": review["rubric_sha256"],
            "frozen_labels_sha256": review["frozen_labels_sha256"],
        },
        "systems": systems,
        "diagnostic_minus_baseline": {
            "strict_accuracy": diagnostic["strict_accuracy"] - baseline["strict_accuracy"],
            **{
                family: diagnostic["by_family"][family]["rate"] - baseline["by_family"][family]["rate"]
                for family in FAMILIES
            },
        },
        "limitations": [
            "This report qualifies a product diagnostic; it does not test H1 or H2.",
            "The manifest records independent blind review but cannot prove reviewer independence.",
            "A positive delta on authored controls does not establish field utility.",
            "The receipt binds supplied labels; external custody must establish who froze it and when.",
        ],
    }
