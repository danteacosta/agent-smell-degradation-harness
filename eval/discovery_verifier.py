"""Leakage-resistant efficacy benchmark for the requirements-smell verifier.

The verifier is deliberately small and transparent because this is a discovery
instrument, not a trained smell detector. It consumes an allowlisted episode
projection and a pre-final trace. Terminal behavior labels are joined only
after decisions have been produced.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from feature_plane import DeployableFeatureInput, extract_deployable_features
from eval.uncertainty import wilson_interval

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE_ROOT = REPO_ROOT / "artifacts" / "experiments" / "runs"
SCHEMA_VERSION = "requirements-smell-verification/v1"
RULE_PACK_VERSION = "transparent-discovery-rules/v1"
DEFAULT_THRESHOLDS = {"warn": 0.50, "block": 0.75}
_CHECKPOINT_ORDER = {"T0": 0, "T1": 1, "T2": 2, "T3": 3}
_ALLOWED_CHECKPOINTS = {
    "input.received",
    "interpretation.completed",
    "plan.completed",
    "execution.started",
    "tool.completed",
    "retrieval.completed",
}
_TERMINAL_NAMES = {
    "artifact.completed",
    "evaluation.completed",
    "oracle_verdict",
    "terminal.validation",
    "label.created",
    "label.assigned",
}
_TERMINAL_KEYS = {
    "artifact",
    "artifacts",
    "oracle",
    "oracle_spec",
    "oracle_passed",
    "terminal",
    "terminal_validation",
    "label",
    "labels",
    "semantic_label",
    "mutation_score",
    "final_artifact",
    "variant",
    "variant_id",
    "smell",
    "defect_family",
    "defect_type",
    "mutation",
    "outcome",
    "ground_truth",
}

_VAGUE_TERMS = {
    "quickly",
    "regularly",
    "many",
    "different",
    "reasonable",
    "sufficient",
    "several",
    "some",
    "appropriate",
    "timely",
    "properly",
}
_CONDITION_MARKERS = re.compile(
    r"\b(?:if|when|unless|until|only when|only if|as long as|provided that)\b",
    re.IGNORECASE,
)
_NUMBER_MARKERS = re.compile(r"\b\d+(?:\.\d+)?\b|\b(?:one|two|three|four|five|six|seven|eight|nine|ten)\b", re.IGNORECASE)
_OUTCOME_MARKERS = re.compile(
    r"\b(?:reject|den(?:y|ied|ies)|block|prevent|restrict|refus|escalat|terminate|fail)\w*\b",
    re.IGNORECASE,
)


class VerificationInputError(ValueError):
    """Raised when the verifier input is missing or crosses the label boundary."""


def _contains_terminal_key(value: Any) -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key).casefold() in _TERMINAL_KEYS:
                return str(key)
            found = _contains_terminal_key(child)
            if found:
                return found
    elif isinstance(value, (list, tuple)):
        for child in value:
            found = _contains_terminal_key(child)
            if found:
                return found
    return None


def _event_name(event: Mapping[str, Any]) -> str:
    return str(event.get("checkpoint", event.get("event_type", event.get("name", ""))))


def load_observable_events(path: str | Path) -> list[dict[str, Any]]:
    """Load and validate a portable pre-final trace, failing closed on labels."""

    target = Path(path)
    if not target.is_file():
        raise VerificationInputError(f"observable trace does not exist: {target}")
    events: list[dict[str, Any]] = []
    previous_order = -1
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise VerificationInputError(f"invalid observable trace JSON: {target}") from exc
        if not isinstance(value, Mapping):
            raise VerificationInputError("observable trace events must be objects")
        if value.get("tier") == "B":
            raise VerificationInputError("label-plane event is not observable")
        for key in value:
            if str(key).casefold() in _TERMINAL_KEYS:
                raise VerificationInputError(f"terminal field {key!r} in observable trace")
        name = _event_name(value)
        if name in _TERMINAL_NAMES or str(value.get("name", "")) in _TERMINAL_NAMES:
            raise VerificationInputError(f"terminal event {name!r} is not observable")
        source_event_name = str((value.get("attributes") or {}).get("source_event_name", ""))
        if source_event_name in _TERMINAL_NAMES:
            raise VerificationInputError(f"terminal source event {source_event_name!r} is not observable")
        for field in ("attributes", "payload", "extensions"):
            found = _contains_terminal_key(value.get(field))
            if found:
                raise VerificationInputError(f"terminal field {found!r} in observable trace")
        if name not in _ALLOWED_CHECKPOINTS:
            raise VerificationInputError(f"non-observable checkpoint {name!r}")
        order = {
            "input.received": 0,
            "interpretation.completed": 1,
            "plan.completed": 2,
            "execution.started": 3,
            "tool.completed": 4,
            "retrieval.completed": 4,
        }[name]
        if order < previous_order:
            raise VerificationInputError("observable checkpoints are out of order")
        previous_order = order
        events.append(dict(value))
    if not events:
        raise VerificationInputError("observable trace is empty")
    return events


def _checkpoint_for_signal(source: str) -> str:
    return {"text": "T0", "interpretation": "T1", "plan": "T2", "execution": "T3"}[source]


def _add_signal(
    signals: list[dict[str, Any]],
    *,
    code: str,
    message: str,
    weight: float,
    source: str,
) -> None:
    signals.append(
        {
            "code": code,
            "message": message,
            "weight": weight,
            "checkpoint": _checkpoint_for_signal(source),
            "source": source,
        }
    )


def derive_observable_signals(
    requirement_text: str,
    features: Mapping[str, Mapping[str, float | int]],
) -> list[dict[str, Any]]:
    """Derive transparent risk signals from text and pre-final features only."""

    text = str(requirement_text)
    lowered = text.casefold()
    signals: list[dict[str, Any]] = []
    vague = sorted({term for term in _VAGUE_TERMS if re.search(rf"\b{re.escape(term)}\b", lowered)})
    if vague:
        _add_signal(
            signals,
            code="vague_language",
            message="vague term(s): " + ", ".join(vague),
            weight=0.45,
            source="text",
        )

    has_number = bool(_NUMBER_MARKERS.search(text))
    if ("refresh" in lowered or ("deploy" in lowered and "operational" in lowered)) and not has_number:
        _add_signal(
            signals,
            code="unbounded_timing",
            message="timing behavior has no measurable boundary",
            weight=0.55,
            source="text",
        )
    if "support" in lowered and not has_number and not re.search(r"\b(?:at most|at least|maximum|minimum|one through)\b", lowered):
        _add_signal(
            signals,
            code="unbounded_cardinality",
            message="support/capacity statement has no measurable cardinality",
            weight=0.45,
            source="text",
        )
    if ("detect" in lowered or "distinguish" in lowered) and not _OUTCOME_MARKERS.search(text):
        _add_signal(
            signals,
            code="missing_response_outcome",
            message="detection/classification is not paired with an enforcement outcome",
            weight=0.60,
            source="text",
        )
    if "retain" in lowered and not re.search(r"\bimmutable\b|cannot be (?:altered|deleted)", lowered):
        _add_signal(
            signals,
            code="mutable_record",
            message="record retention has no immutability protection",
            weight=0.55,
            source="text",
        )
    if "alert" in lowered and "action" in lowered and not re.search(
        r"opted in|authorized|permission|only when|only if", lowered
    ):
        _add_signal(
            signals,
            code="missing_authorization_condition",
            message="alert-triggering action has no authorization/opt-in condition",
            weight=0.55,
            source="text",
        )
    if "movement" in lowered and "rbc" in lowered and not re.search(r"active|supervision", lowered):
        _add_signal(
            signals,
            code="missing_scope_condition",
            message="movement authorization omits the supervision scope",
            weight=0.55,
            source="text",
        )
    if "acknowledg" in lowered and not re.search(r"does not|fail|without|not acknowledge", lowered):
        _add_signal(
            signals,
            code="missing_negative_condition",
            message="acknowledgement response omits the negative case",
            weight=0.55,
            source="text",
        )
    if "voice" in lowered and "communicate" in lowered and not re.search(
        r"initiating|restricted|only", lowered
    ):
        _add_signal(
            signals,
            code="missing_permission_boundary",
            message="voice communication has no speaker-permission boundary",
            weight=0.55,
            source="text",
        )
    if "consider" in lowered and "anticipated" in lowered and not re.search(
        r"\b(?:unanticipated|both|all)\b", lowered
    ):
        _add_signal(
            signals,
            code="incomplete_completeness_scope",
            message="consideration scope omits unanticipated requests",
            weight=0.55,
            source="text",
        )

    provenance = features.get("provenance", {})
    if int(provenance.get("contradiction_count", 0)) > 0:
        _add_signal(
            signals,
            code="pre_final_contradiction",
            message="the observed interpretation contains a contradiction",
            weight=0.80,
            source="interpretation",
        )
    if int(provenance.get("unresolved_reference_count", 0)) > 0:
        _add_signal(
            signals,
            code="unresolved_reference",
            message="the observed interpretation contains unresolved references",
            weight=0.55,
            source="interpretation",
        )
    if int(provenance.get("error_count", 0)) > 0:
        _add_signal(
            signals,
            code="pre_final_execution_error",
            message="pre-final execution evidence contains an error",
            weight=0.80,
            source="execution",
        )
    return signals


def _event_time(event: Mapping[str, Any]) -> str | None:
    value = event.get("ended_at", event.get("ts", event.get("timestamp")))
    return str(value) if isinstance(value, str) and value else None


def _first_signal_time(events: Sequence[Mapping[str, Any]], checkpoint: str | None) -> str | None:
    if checkpoint is None:
        return None
    target_order = _CHECKPOINT_ORDER[checkpoint]
    for event in events:
        name = _event_name(event)
        order = {
            "input.received": 0,
            "interpretation.completed": 1,
            "plan.completed": 2,
            "execution.started": 3,
            "tool.completed": 4,
            "retrieval.completed": 4,
        }.get(name, 99)
        if order >= target_order:
            return _event_time(event)
    return None


def _decision_for_score(score: float, thresholds: Mapping[str, float]) -> str:
    if score >= float(thresholds["block"]):
        return "block"
    if score >= float(thresholds["warn"]):
        return "warn"
    return "approve"


def _opaque_episode_ref(episode_id: str) -> str:
    return "sha256:" + hashlib.sha256(episode_id.encode("utf-8")).hexdigest()


def score_observable_episode(
    episode: Mapping[str, Any],
    trace_path: str | Path,
    *,
    thresholds: Mapping[str, float] = DEFAULT_THRESHOLDS,
) -> dict[str, Any]:
    """Score one episode using only its observable allowlist and pre-final trace."""

    events = load_observable_events(trace_path)
    try:
        feature_input = DeployableFeatureInput(
            intent_id=str(episode["intent_id"]),
            task_family=str(episode["task_family"]),
            requirement_text=str(episode.get("requirement_text", "")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise VerificationInputError("episode lacks the observable requirement input") from exc
    features = extract_deployable_features(feature_input, trace_path)
    signals = derive_observable_signals(feature_input.requirement_text, features)
    score = min(1.0, sum(float(signal["weight"]) for signal in signals))
    first_signal = min(
        (str(signal["checkpoint"]) for signal in signals),
        key=lambda checkpoint: _CHECKPOINT_ORDER[checkpoint],
        default=None,
    )
    decision_projection = {
        "schema_version": SCHEMA_VERSION,
        "rule_pack": RULE_PACK_VERSION,
        "episode_ref": _opaque_episode_ref(str(episode.get("episode_id", ""))),
        "task_family": feature_input.task_family,
        "risk_score": round(score, 6),
        "decision": _decision_for_score(score, thresholds),
        "signal_codes": [str(signal["code"]) for signal in signals],
        "first_signal_checkpoint": first_signal,
        "thresholds": {key: float(value) for key, value in thresholds.items()},
    }
    decision_hash = hashlib.sha256(
        json.dumps(decision_projection, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        **decision_projection,
        "signals": signals,
        "features": features,
        "first_signal_at": _first_signal_time(events, first_signal),
        "decision_hash": decision_hash,
    }


def _empty_confusion() -> dict[str, int]:
    return {"tp": 0, "fp": 0, "tn": 0, "fn": 0}


def _binary_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    confusion = _empty_confusion()
    for row in rows:
        label = int(row["label"])
        alert = str(row.get("decision")) != "approve"
        if alert and label:
            confusion["tp"] += 1
        elif alert and not label:
            confusion["fp"] += 1
        elif not alert and not label:
            confusion["tn"] += 1
        else:
            confusion["fn"] += 1
    tp, fp, tn, fn = (confusion[key] for key in ("tp", "fp", "tn", "fn"))
    positives = tp + fn
    negatives = fp + tn
    alerts = tp + fp
    recall = tp / positives if positives else None
    specificity = tn / negatives if negatives else None
    precision = tp / alerts if alerts else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall
        else None
    )
    accuracy = (tp + tn) / len(rows) if rows else None
    balanced_accuracy = (
        (recall + specificity) / 2
        if recall is not None and specificity is not None
        else None
    )
    return {
        "eligible_count": len(rows),
        "positive_count": positives,
        "negative_count": negatives,
        "alert_count": alerts,
        "confusion": confusion,
        "recall": recall,
        "warning_coverage": recall,
        "specificity": specificity,
        "precision": precision,
        "f1": f1,
        "accuracy": accuracy,
        "balanced_accuracy": balanced_accuracy,
        "false_alert_rate": fp / negatives if negatives else None,
        "alert_rate": alerts / len(rows) if rows else None,
    }


def deduplicate_repeated_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    expected_replications: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Select one representative per case and audit repeated observations."""

    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row.get("intent_id", "")),
            str(row.get("variant", "")),
            str(row.get("task_family", "")),
        )
        groups[key].append(dict(row))

    expected_ids = (
        set(range(expected_replications))
        if expected_replications is not None and expected_replications > 0
        else None
    )
    representatives: list[dict[str, Any]] = []
    observed_ids: set[int] = set()
    missing_by_key: dict[str, list[int]] = {}
    duplicate_by_key: dict[str, list[int]] = {}
    unstable_keys: list[str] = []

    for key, group in groups.items():
        rep_map: dict[int, list[dict[str, Any]]] = defaultdict(list)
        unnumbered: list[dict[str, Any]] = []
        for row in group:
            replication_id = row.get("replication_id")
            if isinstance(replication_id, int) and not isinstance(replication_id, bool):
                rep_map[replication_id].append(row)
                observed_ids.add(replication_id)
            else:
                unnumbered.append(row)

        key_label = "|".join(key)
        duplicate_ids = sorted(replication for replication, items in rep_map.items() if len(items) > 1)
        if duplicate_ids:
            duplicate_by_key[key_label] = duplicate_ids
        observed_for_key = set(rep_map)
        missing_ids = sorted(expected_ids - observed_for_key) if expected_ids is not None else []
        if missing_ids:
            missing_by_key[key_label] = missing_ids

        representative = rep_map.get(0, unnumbered or [group[0]])[0]
        representatives.append(representative)
        comparable = [row for items in rep_map.values() for row in items] + unnumbered
        stable = all(
            (
                row.get("risk_score") == representative.get("risk_score")
                and row.get("decision") == representative.get("decision")
                and row.get("label") == representative.get("label")
            )
            for row in comparable
        )
        if missing_ids or duplicate_ids or not stable:
            unstable_keys.append(key_label)

    missing_replications = (
        sorted(expected_ids - observed_ids) if expected_ids is not None else []
    )
    return representatives, {
        "key_count": len(groups),
        "expected_replications": expected_replications,
        "observed_replications": sorted(observed_ids),
        "missing_replications": missing_replications,
        "missing_replications_by_key": missing_by_key,
        "duplicate_replications": sorted({replication for values in duplicate_by_key.values() for replication in values}),
        "duplicate_replications_by_key": duplicate_by_key,
        "unstable_key_count": len(unstable_keys),
        "unstable_keys": unstable_keys,
        "all_repetitions_agree": not unstable_keys,
    }


def _paired_discrimination(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    pairs: dict[tuple[str, str], dict[str, Mapping[str, Any]]] = defaultdict(dict)
    for row in rows:
        pairs[(str(row.get("intent_id", "")), str(row.get("task_family", "")))][str(row.get("variant", ""))] = row
    complete = [pair for pair in pairs.values() if "clean" in pair and "smelly" in pair]
    wins = sum(float(pair["smelly"]["risk_score"]) > float(pair["clean"]["risk_score"]) for pair in complete)
    deltas = [float(pair["smelly"]["risk_score"]) - float(pair["clean"]["risk_score"]) for pair in complete]
    return {
        "pair_count": len(complete),
        "wins": wins,
        "rate": wins / len(complete) if complete else None,
        "mean_score_delta": sum(deltas) / len(deltas) if deltas else None,
    }


def _strata(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, Any]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        value = row.get(field)
        groups[str(value) if value not in (None, "") else "unknown"].append(row)
    return {key: _binary_metrics(value) for key, value in sorted(groups.items())}


def _mean(rows: Sequence[Mapping[str, Any]], field: str) -> float | None:
    values = [float(row[field]) for row in rows if row.get(field) is not None]
    return sum(values) / len(values) if values else None


def _mean_lead_time_ms(rows: Sequence[Mapping[str, Any]]) -> float | None:
    values: list[float] = []
    for row in rows:
        first = row.get("first_signal_at")
        terminal = row.get("artifact_completed_at")
        if not isinstance(first, str) or not isinstance(terminal, str):
            continue
        try:
            first_dt = datetime.fromisoformat(first.replace("Z", "+00:00"))
            terminal_dt = datetime.fromisoformat(terminal.replace("Z", "+00:00"))
        except ValueError:
            continue
        values.append((terminal_dt - first_dt).total_seconds() * 1000)
    return sum(values) / len(values) if values else None


def compute_efficacy_metrics(
    rows: Sequence[Mapping[str, Any]],
    *,
    leakage_rejections: int = 0,
) -> dict[str, Any]:
    """Aggregate terminal-labeled rows after verifier decisions are frozen."""

    base = _binary_metrics(rows)
    paired = _paired_discrimination(rows)
    both_classes = bool(base["positive_count"] and base["negative_count"])
    criteria = {
        "no_leakage": leakage_rejections == 0,
        "recall_at_least_0_80": base["recall"] is not None and base["recall"] >= 0.80,
        "false_alert_rate_at_most_0_20": base["false_alert_rate"] is not None and base["false_alert_rate"] <= 0.20,
        "paired_discrimination_at_least_0_80": paired["rate"] is not None and paired["rate"] >= 0.80,
    }
    if not both_classes:
        status = "inconclusive"
    elif leakage_rejections:
        status = "fail"
    elif all(criteria.values()):
        status = "descriptive_only"
    else:
        status = "inconclusive"
    provider_costs = [
        float(row["provider_cost_usd"])
        for row in rows
        if row.get("provider_cost_usd") is not None
    ]
    confidence_intervals = {
        "recall": wilson_interval(base["confusion"]["tp"], base["positive_count"]),
        "precision": wilson_interval(base["confusion"]["tp"], base["alert_count"]),
        "specificity": wilson_interval(base["confusion"]["tn"], base["negative_count"]),
        "false_alert_rate": wilson_interval(base["confusion"]["fp"], base["negative_count"]),
        "paired_discrimination": wilson_interval(paired["wins"], paired["pair_count"]),
        "unit": "unique_behavior_case_or_pair",
        "interpretation": "descriptive_until_independent_replications",
    }
    interval_criteria = {
        "recall_lower_at_least_0_80": (
            confidence_intervals["recall"]["lower"] is not None
            and confidence_intervals["recall"]["lower"] >= 0.80
        ),
        "false_alert_upper_at_most_0_20": (
            confidence_intervals["false_alert_rate"]["upper"] is not None
            and confidence_intervals["false_alert_rate"]["upper"] <= 0.20
        ),
        "paired_discrimination_lower_at_least_0_80": (
            confidence_intervals["paired_discrimination"]["lower"] is not None
            and confidence_intervals["paired_discrimination"]["lower"] >= 0.80
        ),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "rule_pack": RULE_PACK_VERSION,
        "status": status,
        **base,
        "paired_discrimination": paired,
        "confidence_intervals": confidence_intervals,
        "interval_criteria": interval_criteria,
        "interval_status": "supported" if all(interval_criteria.values()) else "inconclusive",
        "criteria": criteria,
        "leakage_rejections": int(leakage_rejections),
        "mean_lead_time_ms": _mean_lead_time_ms(rows),
        "mean_verifier_runtime_ms": _mean(rows, "verifier_runtime_ms"),
        "mean_provider_latency_ms": _mean(rows, "provider_latency_ms"),
        "total_provider_cost_usd": sum(provider_costs) if provider_costs else 0.0,
        "alerts_per_detected_failure": (
            base["alert_count"] / base["confusion"]["tp"]
            if base["confusion"]["tp"]
            else None
        ),
        "strata": {
            "project_id": _strata(rows, "project_id"),
            "smell_type": _strata(rows, "smell_type"),
            "task_family": _strata(rows, "task_family"),
            "first_signal_checkpoint": _strata(rows, "first_signal_checkpoint"),
        },
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(dict(row), sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def _resolve_observable_trace(bundle_dir: Path, episode: Mapping[str, Any]) -> Path:
    relative = episode.get("observable_trace_path")
    if isinstance(relative, str) and relative:
        candidate = (bundle_dir / relative).resolve()
        if bundle_dir.resolve() not in candidate.parents:
            raise VerificationInputError("observable trace escapes the bundle")
        return candidate
    local = episode.get("provenance_path")
    if isinstance(local, str) and local:
        return Path(local)
    raise VerificationInputError("episode has no observable trace path")


def _artifact_completed_at(episode: Mapping[str, Any]) -> str | None:
    path_value = episode.get("provenance_path")
    if not isinstance(path_value, str) or not path_value:
        return None
    path = Path(path_value)
    if not path.is_file():
        return None
    for event in _read_jsonl(path):
        if str(event.get("name", "")) == "artifact.completed" or str(event.get("source_event_name", "")) == "artifact.completed":
            return _event_time(event)
        attributes = event.get("attributes")
        if isinstance(attributes, Mapping) and attributes.get("source_event_name") == "artifact.completed":
            return _event_time(event)
    return None


def _behavior_label(episode: Mapping[str, Any]) -> int | None:
    if str(episode.get("task_family", "")) != "behavior_codegen":
        return None
    status = str(episode.get("behavior_status", ""))
    if status == "passed":
        return 0
    if status == "failed_target_condition":
        return 1
    return None


def _verification_readme(metrics: Mapping[str, Any]) -> str:
    intervals = metrics.get("confidence_intervals") or {}
    stability = metrics.get("replication_stability") or {}
    return "\n".join(
        [
            "# Verification efficacy report",
            "",
            "This is a discovery-only, oracle-separated benchmark.",
            "The verifier reads only `decisions.jsonl` inputs derived from pre-final observations;",
            "`labels.jsonl` is written after decisions and contains the independent behavior labels.",
            "Only `behavior_codegen` decisions with a terminal behavior label enter the binary efficacy matrix;",
            "`test_gen` decisions are observability-only and are not efficacy cases.",
            "",
            f"- Status: `{metrics.get('status')}`",
            f"- Raw eligible behavior rows: `{metrics.get('raw_eligible_count', metrics.get('eligible_count'))}`",
            f"- Unique eligible behavior cases: `{metrics.get('unique_eligible_count', metrics.get('eligible_count'))}`",
            f"- Recall/warning coverage: `{metrics.get('recall')}`",
            f"- Clean false-alert rate: `{metrics.get('false_alert_rate')}`",
            f"- Paired discrimination: `{(metrics.get('paired_discrimination') or {}).get('rate')}`",
            f"- Confidence interval method: `{intervals.get('method', 'wilson')}` at `{intervals.get('confidence', 0.95)}`",
            f"- Interval unit: `{intervals.get('unit', 'unique_behavior_case_or_pair')}`",
            f"- Interval support status: `{metrics.get('interval_status')}`",
            f"- Repeated observations agree: `{stability.get('all_repetitions_agree')}`",
            f"- Mean lead time before artifact completion (ms): `{metrics.get('mean_lead_time_ms')}`",
            "",
            "Five offline repetitions of the deterministic stub are pipeline-stability checks,",
            "not independent model samples; their duplicate rows are deduplicated for primary metrics.",
            "On macOS, `trusted_fixture` executes checked-in reference functions in the parent process",
            "with restricted builtins. It is not production subprocess isolation against hostile code.",
            "",
            "The thresholds are frozen in the run output. `descriptive_only` means that this",
            "versioned pilot is reported as a controlled descriptive result; it is not a",
            "population-level claim or evidence of agent effectiveness on new requirements.",
            "",
        ]
    )


def verify_bundle(
    bundle_dir: str | Path,
    *,
    thresholds: Mapping[str, float] = DEFAULT_THRESHOLDS,
) -> dict[str, Any]:
    """Run the oracle-separated verifier over a promoted discovery bundle."""

    root = Path(bundle_dir)
    episodes_path = root / "episodes.jsonl"
    if not episodes_path.is_file():
        raise VerificationInputError(f"bundle is missing {episodes_path}")
    episodes = _read_jsonl(episodes_path)
    run_config: dict[str, Any] = {}
    run_path = root / "run.json"
    if run_path.is_file():
        run_value = json.loads(run_path.read_text(encoding="utf-8"))
        if isinstance(run_value, Mapping):
            run_config = dict(run_value)
    expected_episode_count = run_config.get("expected_episode_count")
    if expected_episode_count is not None and len(episodes) != int(expected_episode_count):
        raise VerificationInputError(
            f"expected {expected_episode_count} episodes, found {len(episodes)}"
        )
    decisions: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []
    labeled_rows: list[dict[str, Any]] = []
    leakage_rejections = 0
    for episode in episodes:
        started = time.perf_counter()
        try:
            trace_path = _resolve_observable_trace(root, episode)
            decision = score_observable_episode(episode, trace_path, thresholds=thresholds)
            decision_row = {
                "schema_version": SCHEMA_VERSION,
                "episode_ref": decision["episode_ref"],
                "task_family": decision["task_family"],
                "risk_score": decision["risk_score"],
                "decision": decision["decision"],
                "signal_codes": decision["signal_codes"],
                "signals": decision["signals"],
                "first_signal_checkpoint": decision["first_signal_checkpoint"],
                "first_signal_at": decision["first_signal_at"],
                "thresholds": decision["thresholds"],
                "decision_hash": decision["decision_hash"],
            }
        except VerificationInputError as exc:
            leakage_rejections += int("terminal" in str(exc) or "label" in str(exc) or "oracle" in str(exc))
            decision_row = {
                "schema_version": SCHEMA_VERSION,
                "episode_ref": _opaque_episode_ref(str(episode.get("episode_id", ""))),
                "task_family": str(episode.get("task_family", "")),
                "risk_score": None,
                "decision": "ineligible",
                "signal_codes": [],
                "signals": [],
                "first_signal_checkpoint": None,
                "first_signal_at": None,
                "thresholds": {key: float(value) for key, value in thresholds.items()},
                "error": str(exc),
                "decision_hash": None,
            }
        decision_row["verifier_runtime_ms"] = (time.perf_counter() - started) * 1000
        decisions.append(decision_row)

        label = _behavior_label(episode)
        if label is None or decision_row["decision"] == "ineligible":
            continue
        provider_meta = episode.get("provider_meta")
        provider_meta = provider_meta if isinstance(provider_meta, Mapping) else {}
        label_row = {
            "episode_id": str(episode.get("episode_id", "")),
            "replication_id": episode.get("replication_id"),
            "intent_id": str(episode.get("intent_id", "")),
            "project_id": episode.get("project_id"),
            "variant": episode.get("variant"),
            "smell_type": (episode.get("smell") or {}).get("type") if isinstance(episode.get("smell"), Mapping) else None,
            "task_family": str(episode.get("task_family", "")),
            "behavior_status": str(episode.get("behavior_status", "")),
            "label": label,
            "risk_score": decision_row["risk_score"],
            "decision": decision_row["decision"],
            "first_signal_checkpoint": decision_row["first_signal_checkpoint"],
            "first_signal_at": decision_row["first_signal_at"],
            "artifact_completed_at": _artifact_completed_at(episode),
            "verifier_runtime_ms": decision_row["verifier_runtime_ms"],
            "provider_latency_ms": provider_meta.get("latency_ms"),
            "provider_cost_usd": provider_meta.get("cost_usd"),
        }
        labels.append(label_row)
        labeled_rows.append(label_row)

    expected_replications = run_config.get("replications")
    if expected_replications is not None:
        expected_replications = int(expected_replications)
    unique_labeled_rows, replication_stability = deduplicate_repeated_rows(
        labeled_rows,
        expected_replications=expected_replications,
    )
    metrics = compute_efficacy_metrics(
        unique_labeled_rows,
        leakage_rejections=leakage_rejections,
    )
    behavior_decision_count = sum(
        str(episode.get("task_family", "")) == "behavior_codegen" for episode in episodes
    )
    metrics.update(
        {
            "decision_count": len(decisions),
            "behavior_decision_count": behavior_decision_count,
            "behavior_ineligible_count": behavior_decision_count - len(labels),
            "non_behavior_decision_count": len(decisions) - behavior_decision_count,
            "raw_eligible_count": len(labeled_rows),
            "unique_eligible_count": len(unique_labeled_rows),
            "replication_stability": replication_stability,
            "analysis_unit": "unique_behavior_case_or_pair",
        }
    )
    verification_dir = root / "verification"
    _write_jsonl(verification_dir / "decisions.jsonl", decisions)
    _write_jsonl(verification_dir / "labels.jsonl", labels)
    (verification_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (verification_dir / "README.md").write_text(_verification_readme(metrics), encoding="utf-8")
    return {
        "schema_version": SCHEMA_VERSION,
        "bundle_dir": str(root),
        "decision_count": len(decisions),
        "labeled_count": len(labels),
        "metrics": metrics,
    }


def latest_bundle(bundle_root: str | Path = DEFAULT_BUNDLE_ROOT) -> Path:
    root = Path(bundle_root)
    candidates = [
        path
        for path in root.glob("*")
        if path.is_dir() and (path / "episodes.jsonl").is_file()
    ]
    if not candidates:
        raise VerificationInputError(f"no discovery bundles found under {root}")
    return max(
        candidates,
        key=lambda path: (path / "run.json").stat().st_mtime,
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-dir", type=Path)
    args = parser.parse_args(argv)
    bundle_dir = args.bundle_dir or latest_bundle()
    result = verify_bundle(bundle_dir)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
