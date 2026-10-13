"""Author frozen label inventories without attaching detector predictions."""
from __future__ import annotations

import copy
import hashlib
import json

from eval.evidence_diagnostic_qualification import FAMILIES, LABEL_FIELDS


def freeze_label_inventory(project_split: dict, labels: list[dict]) -> dict:
    """Return a copied label inventory and its canonical SHA-256 receipt.

    This helper accepts label-plane fields only. Detector outputs must be joined
    later, after review and freezing, so they cannot influence expected labels.
    """
    if not isinstance(project_split, dict) or not project_split:
        raise ValueError("project split required")
    if not all(
        isinstance(project_id, str)
        and project_id
        and split in {"development", "calibration", "evaluation"}
        for project_id, split in project_split.items()
    ):
        raise ValueError("invalid project split")
    if not isinstance(labels, list) or not labels:
        raise ValueError("labels required")

    frozen = copy.deepcopy(labels)
    seen: set[str] = set()
    for label in frozen:
        if not isinstance(label, dict) or set(label) != set(LABEL_FIELDS):
            raise ValueError("labels must contain label-plane fields only")
        if any(not isinstance(label[key], str) or not label[key] for key in LABEL_FIELDS):
            raise ValueError("label fields must be non-empty strings")
        if label["record_id"] in seen:
            raise ValueError("duplicate record_id")
        seen.add(label["record_id"])
        if label["project_id"] not in project_split:
            raise ValueError("label project absent from frozen split")
        if label["family"] not in FAMILIES or label["expected_decision"] != FAMILIES[label["family"]]:
            raise ValueError("family and expected decision disagree")

    canonical = json.dumps(
        {"project_split": project_split, "labels": frozen},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return {
        "frozen_labels": frozen,
        "frozen_labels_sha256": hashlib.sha256(canonical).hexdigest(),
    }
