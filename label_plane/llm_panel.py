"""Blinded annotation contract for an independent model panel.

The protocol deliberately does not depend on a vendor.  Historical v1
artifacts used the identifiers ``kimi``, ``gpt`` and ``claude``; new runs may
provide arbitrary judge identifiers through their private runtime config.
Model-panel consensus is exploratory until human audit/adjudication is done.
"""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping

from baselines.natural_smell import SUPPORTED_FAMILIES

PANEL_VERSION = "llm-panel/v1"
PANEL_PROVIDERS = ("kimi", "gpt", "claude")
PANEL_LABELS = ("clean", "smelly", "uncertain", "not_visible")
_FORBIDDEN_FIELDS = frozenset(
    {
        "source_label",
        "source_smell_markers",
        "candidate_kind",
        "project_id",
        "project_name",
        "project_split",
        "split",
        "oracle_result",
        "model_provider",
    }
)


def build_panel_prompt(*, item_id: str, requirement_text: str, target_family: str) -> str:
    """Build the identical blinded prompt sent independently to each model."""

    if not item_id.strip() or not requirement_text.strip():
        raise ValueError("panel prompt requires an item ID and requirement text")
    if target_family not in SUPPORTED_FAMILIES:
        raise ValueError(f"unsupported target family: {target_family}")
    return (
        "You are annotating one natural-language software requirement.\n"
        "Judge only whether the stated requirement exhibits the requested smell "
        "family in its own wording and available context. Do not infer hidden "
        "project metadata.\n\n"
        f"Item ID: {item_id}\n"
        f"Target smell family: {target_family}\n"
        f"Requirement: {requirement_text}\n\n"
        "Do not use or request source_label, source_smell_markers, project_id, "
        "project_split, model_provider, oracle_result, or candidate_kind.\n"
        "Return exactly one JSON object with these fields: label (one of "
        "clean, smelly, uncertain, not_visible), target_family, evidence_span, "
        "rationale, confidence (number from 0 to 1). Use uncertain when the "
        "context is insufficient or the judgment depends on an undocumented "
        "assumption."
    )


def validate_panel_annotation(
    annotation: Mapping[str, Any],
    *,
    allowed_providers: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Validate one model response before it can enter consensus."""

    leaked = _FORBIDDEN_FIELDS.intersection(annotation)
    if leaked:
        raise ValueError(f"panel annotation contains forbidden fields: {sorted(leaked)}")
    required = {"item_id", "provider_id", "model_id", "target_family", "label", "evidence_span", "rationale", "confidence"}
    missing = required - set(annotation)
    if missing:
        raise ValueError(f"panel annotation is missing fields: {sorted(missing)}")
    provider = str(annotation["provider_id"]).strip()
    allowed = tuple(PANEL_PROVIDERS if allowed_providers is None else allowed_providers)
    allowed = tuple(str(value).strip() for value in allowed if str(value).strip())
    if not allowed:
        raise ValueError("panel annotation requires at least one configured judge")
    if provider not in allowed:
        raise ValueError(f"panel annotation provider must be one of {allowed}")
    label = str(annotation["label"])
    if label not in PANEL_LABELS:
        raise ValueError(f"panel annotation label must be one of {PANEL_LABELS}")
    family = str(annotation["target_family"])
    if family not in SUPPORTED_FAMILIES:
        raise ValueError(f"panel annotation target_family is unsupported: {family}")
    confidence = annotation["confidence"]
    if isinstance(confidence, bool):
        raise ValueError("panel annotation confidence must be numeric")
    try:
        confidence = float(confidence)
    except (TypeError, ValueError) as exc:
        raise ValueError("panel annotation confidence must be numeric") from exc
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("panel annotation confidence must be between 0 and 1")
    result = dict(annotation)
    result["item_id"] = str(annotation["item_id"]).strip()
    result["provider_id"] = provider
    result["model_id"] = str(annotation["model_id"]).strip()
    result["target_family"] = family
    result["label"] = label
    result["evidence_span"] = str(annotation["evidence_span"])
    result["rationale"] = str(annotation["rationale"])
    result["confidence"] = confidence
    if not result["item_id"] or not result["model_id"] or not result["rationale"].strip():
        raise ValueError("panel annotation requires non-empty item, model, and rationale")
    return result


def select_human_audit_subset(
    item_ids: Iterable[str], *, fraction: float = 0.20, seed: int = 0
) -> tuple[str, ...]:
    """Select a reproducible human audit subset without looking at labels."""

    if not 0.0 < fraction <= 1.0:
        raise ValueError("human audit fraction must be in (0, 1]")
    unique = sorted({str(item_id) for item_id in item_ids if str(item_id).strip()})
    if not unique:
        return ()
    count = max(1, round(len(unique) * fraction))
    chooser = random.Random(seed)
    return tuple(sorted(chooser.sample(unique, min(count, len(unique)))))


def select_stratified_human_audit_subset(
    consensus_rows: Iterable[Mapping[str, Any]], *, fraction: float = 0.20, seed: int = 0
) -> tuple[dict[str, str], ...]:
    """Select a reproducible audit that covers meaningful panel failure modes.

    This is an audit sample, not ground truth.  Cases already requiring human
    review remain mandatory; the additional sample is stratified by family,
    consensus outcome and apparent difficulty (low agreement / uncertainty).
    """

    if not 0.0 < fraction <= 1.0:
        raise ValueError("human audit fraction must be in (0, 1]")
    rows = [dict(row) for row in consensus_rows]
    by_id = {str(row.get("item_id", "")): row for row in rows if str(row.get("item_id", "")).strip()}
    if len(by_id) != len(rows):
        raise ValueError("consensus rows require unique, non-empty item_id values")
    if not rows:
        return ()
    target = max(1, round(len(rows) * fraction))
    selected: dict[str, str] = {
        item_id: "mandatory_disagreement_or_uncertainty"
        for item_id, row in by_id.items()
        if bool(row.get("human_review_required"))
    }
    buckets: defaultdict[tuple[str, str, str], list[str]] = defaultdict(list)
    for item_id, row in by_id.items():
        agreement = float(row.get("agreement", 0))
        difficulty = "low_agreement" if agreement < 1 else "unanimous"
        bucket = (str(row.get("target_family", "unknown")), str(row.get("status", "unknown")), difficulty)
        buckets[bucket].append(item_id)
    chooser = random.Random(seed)
    # One representative per eligible stratum, then a seeded fill to target.
    for bucket in sorted(buckets):
        candidates = [item_id for item_id in sorted(buckets[bucket]) if item_id not in selected]
        if candidates and len(selected) < target:
            selected[chooser.choice(candidates)] = "stratified_family_outcome_difficulty"
    remaining = [item_id for item_id in sorted(by_id) if item_id not in selected]
    chooser.shuffle(remaining)
    for item_id in remaining[: max(0, target - len(selected))]:
        selected[item_id] = "seeded_random_fill"
    return tuple({"item_id": item_id, "audit_reason": selected[item_id]} for item_id in sorted(selected))


def build_panel_tasks(
    candidates: Iterable[Mapping[str, Any]],
    *,
    judge_ids: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Expand candidates into one identical, judge-tagged task per judge.

    ``PANEL_PROVIDERS`` remains the default solely for compatibility with the
    historical v1 task file.  A new execution should pass judge IDs from its
    private panel configuration instead of using vendor names.
    """

    judges = tuple(PANEL_PROVIDERS if judge_ids is None else judge_ids)
    judges = tuple(str(value).strip() for value in judges if str(value).strip())
    if not judges or len(set(judges)) != len(judges):
        raise ValueError("panel tasks require unique, non-empty judge IDs")

    tasks: list[dict[str, Any]] = []
    for candidate in candidates:
        item_id = str(candidate["candidate_id"])
        text = str(candidate["requirement_text"])
        family = str(candidate["target_family"])
        prompt = build_panel_prompt(item_id=item_id, requirement_text=text, target_family=family)
        prompt_hash = sha256(prompt.encode("utf-8")).hexdigest()
        for provider in judges:
            tasks.append(
                {
                    "panel_version": PANEL_VERSION,
                    "item_id": item_id,
                    "provider_id": provider,
                    "target_family": family,
                    "prompt_sha256": prompt_hash,
                    "prompt": prompt,
                }
            )
    tasks.sort(key=lambda task: (str(task["item_id"]), str(task["provider_id"])))
    return tasks


def build_consensus(
    annotations: Iterable[Mapping[str, Any]],
    *,
    expected_providers: Iterable[str] | None = None,
    consensus_required: int = 2,
) -> dict[str, Any]:
    """Apply a configured majority rule to one item.

    With no explicit configuration this preserves the historical v1 2-of-3
    rule.  The runtime passes arbitrary judge IDs and the same rule explicitly
    so the scientific protocol stays stable while providers remain swappable.
    """

    expected = tuple(PANEL_PROVIDERS if expected_providers is None else expected_providers)
    expected = tuple(str(value).strip() for value in expected if str(value).strip())
    if not expected or len(set(expected)) != len(expected):
        raise ValueError("panel consensus requires unique, non-empty configured judges")
    if not 1 <= consensus_required <= len(expected):
        raise ValueError("consensus_required must be between 1 and the number of judges")
    validated = [
        validate_panel_annotation(annotation, allowed_providers=expected)
        for annotation in annotations
    ]
    if not validated:
        raise ValueError("panel consensus requires annotations")
    item_ids = {str(annotation["item_id"]) for annotation in validated}
    families = {str(annotation["target_family"]) for annotation in validated}
    providers = {str(annotation["provider_id"]) for annotation in validated}
    if len(item_ids) != 1 or len(families) != 1:
        raise ValueError("panel consensus requires one item and one target family")
    if providers != set(expected) or len(validated) != len(expected):
        raise ValueError(
            "panel consensus requires exactly one annotation from all configured providers/judges"
        )
    labels = Counter(str(annotation["label"]) for annotation in validated)
    label, votes = labels.most_common(1)[0]
    has_majority = votes >= consensus_required
    final_label = label if has_majority else "uncertain"
    status = "panel_consensus" if has_majority and final_label in {"clean", "smelly"} else "uncertain"
    all_agree = len(labels) == 1
    return {
        "panel_version": PANEL_VERSION,
        "item_id": next(iter(item_ids)),
        "target_family": next(iter(families)),
        "label": final_label,
        "status": status,
        "agreement": votes / len(validated),
        "votes": dict(sorted(labels.items())),
        "provider_labels": {
            str(annotation["provider_id"]): str(annotation["label"])
            for annotation in sorted(validated, key=lambda row: str(row["provider_id"]))
        },
        "human_review_required": (not all_agree) or final_label == "uncertain",
        "human_review_reason": "provider_disagreement_or_uncertainty" if (not all_agree or final_label == "uncertain") else "audit_sample_only",
    }


def build_consensus_batch(
    annotations: Iterable[Mapping[str, Any]],
    *,
    expected_providers: Iterable[str] | None = None,
    consensus_required: int = 2,
) -> list[dict[str, Any]]:
    grouped: defaultdict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for annotation in annotations:
        item_id = str(annotation.get("item_id", ""))
        if not item_id:
            raise ValueError("panel batch annotation requires item_id")
        grouped[item_id].append(annotation)
    results = [
        build_consensus(
            rows,
            expected_providers=expected_providers,
            consensus_required=consensus_required,
        )
        for _, rows in sorted(grouped.items())
    ]
    results.sort(key=lambda row: str(row["item_id"]))
    return results


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at line {line_number}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"JSONL row {line_number} must be an object")
            rows.append(value)
    return rows


__all__ = [
    "PANEL_LABELS",
    "PANEL_PROVIDERS",
    "PANEL_VERSION",
    "build_consensus",
    "build_consensus_batch",
    "build_panel_prompt",
    "build_panel_tasks",
    "load_jsonl",
    "select_human_audit_subset",
    "select_stratified_human_audit_subset",
    "validate_panel_annotation",
]
