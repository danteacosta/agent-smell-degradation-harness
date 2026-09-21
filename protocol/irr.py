from __future__ import annotations

import csv
import math
import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


def load_annotations(path: Path | str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with Path(path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"episode_id", "mode", "severity"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            missing = required - set(reader.fieldnames or [])
            raise ValueError(f"annotation file missing columns: {sorted(missing)}")
        seen: set[str] = set()
        for line, row in enumerate(reader, start=2):
            if any(row[key] is None or not row[key].strip() for key in required):
                raise ValueError(f"annotation row {line} has blank or missing required values")
            episode_id = row["episode_id"]
            if episode_id in seen:
                raise ValueError(f"duplicate episode_id in annotation row {line}")
            seen.add(episode_id)
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
        values = list(data.values())
        if values and all(isinstance(value, Mapping) for value in values):
            # Convenient interchange form: item_id -> annotator_id -> label.
            items = list(data)
            annotators = list(dict.fromkeys(annotator for value in values for annotator in value))
            return [[data[item].get(annotator) for item in items] for annotator in annotators]
        rows = values
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
            judgments = grouped.setdefault(str(row.item_id), {})
            if annotator in judgments:
                raise ValueError("duplicate annotation for the same item and annotator")
            judgments[annotator] = row.label
        items = sorted(grouped)
        return [[grouped[item].get(annotator) for item in items] for annotator in annotators]
    matrix = [list(row) if not isinstance(row, Mapping) else list(row.values()) for row in rows]
    width = len(matrix[0]) if matrix else 0
    if any(len(row) != width for row in matrix):
        raise ValueError("annotation rows must have equal length")
    return matrix


def _ordinal_categories(values: list[Any], ordinal_order: Sequence[Any] | None) -> list[Any]:
    if ordinal_order is not None:
        categories = list(ordinal_order)
        if len(set(categories)) != len(categories):
            raise ValueError("ordinal_order must contain unique labels")
        return categories
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


class _UndefinedAlpha(ValueError):
    """An estimand unavailable for a valid but degenerate sample."""


def krippendorff_alpha(
    data: Any,
    *,
    level_of_measurement: str = "nominal",
    ordinal_order: Sequence[Any] | None = None,
) -> float:
    """Compute nominal/ordinal alpha from pairable annotator×unit labels.

    None, empty strings and NaN are missing. Singleton units contribute to
    neither disagreement term. Ordinal distances use marginal midranks; pass
    the rubric's explicit order for nonnumeric labels. Raise ValueError when
    no pairs exist or expected disagreement is zero (alpha is undefined).
    """
    level = level_of_measurement.casefold()
    if level not in {"nominal", "ordinal"}:
        raise ValueError("measurement level must be nominal or ordinal")
    matrix = _as_matrix(data)
    units = [
        [value for value in column if not _is_missing(value)]
        for column in zip(*matrix)
    ]
    units = [unit for unit in units if len(unit) >= 2]
    counts = Counter(value for unit in units for value in unit)
    n = sum(counts.values())
    if not n:
        raise _UndefinedAlpha("alpha is undefined: no pairable annotations")
    categories = (
        _ordinal_categories(list(counts), ordinal_order)
        if level == "ordinal" else list(counts)
    )
    if any(value not in categories for value in counts):
        raise ValueError("ordinal_order must include every pairable label")
    midpoints: dict[Any, float] = {}
    cumulative = 0
    for value in categories:
        midpoints[value] = cumulative + counts[value] / 2
        cumulative += counts[value]

    def distance(left: Any, right: Any) -> float:
        if level == "nominal":
            return float(left != right)
        return (midpoints[left] - midpoints[right]) ** 2

    # Unordered pairs occur twice in both disagreement terms, so the common
    # factor 2/n cancels. Within-unit weights remain essential when m varies.
    observed = sum(
        sum(distance(left, right) for i, left in enumerate(unit) for right in unit[i + 1:])
        / (len(unit) - 1)
        for unit in units
    )
    expected = sum(
        counts[left] * counts[right] * distance(left, right)
        for i, left in enumerate(categories) for right in categories[i + 1:]
    )
    if expected == 0:
        raise _UndefinedAlpha("alpha is undefined: zero expected disagreement")
    return 1.0 - (n - 1) * observed / expected


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
    if not math.isfinite(alpha) or not -1 <= alpha <= 1:
        raise ValueError("alpha must be finite and between -1 and 1")
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
) -> dict[str, float | int | None]:
    """Unit bootstrap; disclose undefined draws and conditional percentiles."""
    if n_bootstrap < 1:
        raise ValueError("n_bootstrap must be positive")
    matrix = _as_matrix(data)
    alpha = krippendorff_alpha(matrix, level_of_measurement=level_of_measurement, ordinal_order=ordinal_order)
    width = len(matrix[0]) if matrix else 0
    rng = random.Random(seed)
    samples: list[float] = []
    for _ in range(n_bootstrap):
        indices = [rng.randrange(width) for _ in range(width)]
        sampled = [[row[index] for index in indices] for row in matrix]
        try:
            samples.append(krippendorff_alpha(sampled, level_of_measurement=level_of_measurement, ordinal_order=ordinal_order))
        except _UndefinedAlpha:
            pass
    return {
        "alpha": alpha,
        "lower": _percentile(samples, 0.025) if samples else None,
        "upper": _percentile(samples, 0.975) if samples else None,
        "n_bootstrap": n_bootstrap,
        "n_valid": len(samples),
        "n_undefined": n_bootstrap - len(samples),
    }


# Concise aliases used by analysis notebooks and preregistration templates.
krippendorff_alpha_bootstrap = bootstrap_krippendorff_alpha
alpha_bootstrap_ci = bootstrap_krippendorff_alpha
