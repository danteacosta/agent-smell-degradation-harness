from __future__ import annotations

import csv
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


def load_annotations(path: Path | str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with Path(path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"episode_id", "mode", "severity"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            missing = required - set(reader.fieldnames or [])
            raise ValueError(f"annotation file missing columns: {sorted(missing)}")
        for row in reader:
            rows.append({key: row[key] for key in required})
    return rows


def percent_agreement(y1: list[Any], y2: list[Any]) -> float:
    if len(y1) != len(y2):
        raise ValueError("label lists must have equal length")
    if not y1:
        return 0.0
    matches = sum(a == b for a, b in zip(y1, y2, strict=True))
    return matches / len(y1)


def cohens_kappa(y1: list[Any], y2: list[Any]) -> float:
    if len(y1) != len(y2):
        raise ValueError("label lists must have equal length")
    n = len(y1)
    if n == 0:
        return 0.0

    categories = sorted(set(y1) | set(y2))
    observed = sum(a == b for a, b in zip(y1, y2, strict=True)) / n
    expected = 0.0
    for category in categories:
        p1 = y1.count(category) / n
        p2 = y2.count(category) / n
        expected += p1 * p2

    if expected == 1.0:
        return 1.0 if observed == 1.0 else 0.0
    return (observed - expected) / (1.0 - expected)


def compare_annotations(
    path_a: Path | str,
    path_b: Path | str,
) -> dict[str, Any]:
    ann_a = load_annotations(path_a)
    ann_b = load_annotations(path_b)

    by_id_a = {row["episode_id"]: row for row in ann_a}
    by_id_b = {row["episode_id"]: row for row in ann_b}
    common_ids = sorted(set(by_id_a) & set(by_id_b))

    modes_a = [by_id_a[eid]["mode"] for eid in common_ids]
    modes_b = [by_id_b[eid]["mode"] for eid in common_ids]
    severities_a = [by_id_a[eid]["severity"] for eid in common_ids]
    severities_b = [by_id_b[eid]["severity"] for eid in common_ids]

    return {
        "n_items": len(common_ids),
        "mode_kappa": cohens_kappa(modes_a, modes_b),
        "mode_agreement": percent_agreement(modes_a, modes_b),
        "severity_kappa": cohens_kappa(severities_a, severities_b),
        "severity_agreement": percent_agreement(severities_a, severities_b),
        "mode_alpha": krippendorff_alpha([modes_a, modes_b], level_of_measurement="nominal"),
        "severity_alpha": krippendorff_alpha([severities_a, severities_b], level_of_measurement="ordinal"),
    }


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return isinstance(value, str) and not value.strip()


def _as_matrix(data: Any) -> list[list[Any]]:
    """Normalize annotator×unit, mapping, or HumanAnnotation input."""
    if isinstance(data, Mapping):
        rows = list(data.values())
    else:
        rows = list(data)
    if not rows:
        return []
    if all(hasattr(row, "item_id") and hasattr(row, "label") for row in rows):
        grouped: dict[str, dict[str, Any]] = {}
        annotators: list[str] = []
        for row in rows:
            annotator = str(row.annotator_id)
            if annotator not in annotators:
                annotators.append(annotator)
            grouped.setdefault(str(row.item_id), {})[annotator] = row.label
        items = sorted(grouped)
        return [[grouped[item].get(annotator) for item in items] for annotator in annotators]
    matrix = [list(row) if not isinstance(row, Mapping) else list(row.values()) for row in rows]
    width = len(matrix[0]) if matrix else 0
    if any(len(row) != width for row in matrix):
        raise ValueError("annotation rows must have equal length")
    return matrix


def _distance(left: Any, right: Any, level: str, ranks: dict[Any, int]) -> float:
    if level == "nominal":
        return 0.0 if left == right else 1.0
    span = max(len(ranks) - 1, 1)
    return ((ranks[left] - ranks[right]) / span) ** 2


def _ordinal_categories(values: list[Any], ordinal_order: Sequence[Any] | None) -> list[Any]:
    if ordinal_order is not None:
        return list(ordinal_order)
    unique = set(values)
    # Common rubric vocabularies get their declared semantic order.  Unknown
    # labels remain deterministic and should use an explicit order in a
    # preregistration when their semantics are not obvious.
    vocabularies = (
        ("none", "low", "medium", "moderate", "high", "critical"),
        ("clean", "minor", "moderate", "degraded", "severe"),
    )
    for vocabulary in vocabularies:
        if unique <= set(vocabulary):
            return [label for label in vocabulary if label in unique]
    if all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in values):
        return sorted(unique)
    return sorted(unique, key=lambda value: (type(value).__name__, str(value)))


def krippendorff_alpha(
    data: Any,
    *,
    level_of_measurement: str = "nominal",
    ordinal_order: Sequence[Any] | None = None,
) -> float:
    """Compute Krippendorff's alpha for annotator×unit labels.

    Missing labels (``None``, empty strings, and NaN) are omitted.  Ordinal
    disagreement uses squared normalized rank distance; callers may provide an
    explicit ``ordinal_order`` to avoid lexical ordering of labels.
    """
    level = level_of_measurement.casefold()
    if level not in {"nominal", "ordinal"}:
        raise ValueError("measurement level must be nominal or ordinal")
    matrix = _as_matrix(data)
    if not matrix:
        return 0.0
    observed_units = [[row[index] for row in matrix if index < len(row) and not _is_missing(row[index])] for index in range(len(matrix[0]))]
    observed_units = [unit for unit in observed_units if len(unit) >= 2]
    all_values = [value for row in matrix for value in row if not _is_missing(value)]
    if not all_values:
        return 0.0
    categories = _ordinal_categories(all_values, ordinal_order)
    if any(value not in categories for value in all_values):
        raise ValueError("ordinal_order must include every observed label")
    ranks = {value: index for index, value in enumerate(categories)}
    if level == "nominal":
        ranks = {value: index for index, value in enumerate(categories)}

    observed_pairs = [(left, right) for unit in observed_units for index, left in enumerate(unit) for right in unit[index + 1 :]]
    if not observed_pairs:
        return 1.0
    do = sum(_distance(left, right, level, ranks) for left, right in observed_pairs) / len(observed_pairs)
    expected_pairs = [(left, right) for index, left in enumerate(all_values) for right in all_values[index + 1 :]]
    if not expected_pairs:
        return 1.0
    de = sum(_distance(left, right, level, ranks) for left, right in expected_pairs) / len(expected_pairs)
    if de == 0.0:
        return 1.0
    return max(-1.0, min(1.0, 1.0 - do / de))


@dataclass(frozen=True, slots=True)
class IRRDecision:
    alpha: float
    target: float = 0.70
    adjudication_threshold: float = 0.60
    adjudication_required: bool = False
    claim_narrowing_required: bool = False

    @property
    def status(self) -> str:
        if self.claim_narrowing_required:
            return "adjudicate_and_narrow_claims"
        if self.adjudication_required:
            return "adjudicate_before_confirmatory_claim"
        return "acceptable"


def irr_decision(alpha: float, *, target: float = 0.70, adjudication_threshold: float = 0.60) -> IRRDecision:
    if not 0 <= target <= 1 or not 0 <= adjudication_threshold <= target:
        raise ValueError("IRR thresholds must satisfy 0 <= adjudication_threshold <= target <= 1")
    return IRRDecision(
        alpha=float(alpha), target=target, adjudication_threshold=adjudication_threshold,
        adjudication_required=alpha < target,
        claim_narrowing_required=alpha < adjudication_threshold,
    )


def _percentile(values: list[float], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def bootstrap_krippendorff_alpha(
    data: Any,
    *,
    level_of_measurement: str = "nominal",
    ordinal_order: Sequence[Any] | None = None,
    n_bootstrap: int = 1000,
    seed: int = 0,
) -> dict[str, float | int]:
    """Resample annotation units with a deterministic local RNG."""
    if n_bootstrap < 1:
        raise ValueError("n_bootstrap must be positive")
    matrix = _as_matrix(data)
    alpha = krippendorff_alpha(matrix, level_of_measurement=level_of_measurement, ordinal_order=ordinal_order)
    width = len(matrix[0]) if matrix else 0
    if width == 0:
        return {"alpha": alpha, "lower": alpha, "upper": alpha, "n_bootstrap": 0}
    rng = random.Random(seed)
    samples: list[float] = []
    for _ in range(n_bootstrap):
        indices = [rng.randrange(width) for _ in range(width)]
        sampled = [[row[index] for index in indices] for row in matrix]
        samples.append(krippendorff_alpha(sampled, level_of_measurement=level_of_measurement, ordinal_order=ordinal_order))
    return {
        "alpha": alpha,
        "lower": _percentile(samples, 0.025),
        "upper": _percentile(samples, 0.975),
        "n_bootstrap": n_bootstrap,
    }


# Concise aliases used by analysis notebooks and preregistration templates.
krippendorff_alpha_bootstrap = bootstrap_krippendorff_alpha
alpha_bootstrap_ci = bootstrap_krippendorff_alpha
