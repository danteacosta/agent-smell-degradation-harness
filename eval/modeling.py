"""Dependency-free train-only rankers for confirmatory H2 feature families."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class StandardizedMeanDifferenceRanker:
    feature_names: tuple[str, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]
    fit_n: int
    positive_n: int

    @classmethod
    def fit(
        cls,
        rows: Sequence[Mapping[str, float | int]],
        labels: Sequence[int],
    ) -> "StandardizedMeanDifferenceRanker":
        if len(rows) != len(labels) or not rows:
            raise ValueError("training features and labels must be non-empty and aligned")
        if not {0, 1}.issubset(set(labels)):
            raise ValueError("training labels must contain both classes")
        feature_names = tuple(sorted(set().union(*(row.keys() for row in rows))))
        if not feature_names:
            raise ValueError("training features cannot be empty")
        matrix: list[list[float]] = []
        for row in rows:
            values: list[float] = []
            for name in feature_names:
                value = float(row.get(name, 0.0))
                if not math.isfinite(value):
                    raise ValueError(f"training feature {name} must be finite")
                values.append(value)
            matrix.append(values)
        means = tuple(sum(row[index] for row in matrix) / len(matrix) for index in range(len(feature_names)))
        scales = tuple(
            max(
                math.sqrt(sum((row[index] - means[index]) ** 2 for row in matrix) / len(matrix)),
                1e-12,
            )
            for index in range(len(feature_names))
        )
        standardized = [
            [(row[index] - means[index]) / scales[index] for index in range(len(feature_names))]
            for row in matrix
        ]
        positive = [row for row, label in zip(standardized, labels) if label == 1]
        negative = [row for row, label in zip(standardized, labels) if label == 0]
        weights = tuple(
            sum(row[index] for row in positive) / len(positive)
            - sum(row[index] for row in negative) / len(negative)
            for index in range(len(feature_names))
        )
        return cls(feature_names, means, scales, weights, len(rows), sum(labels))

    def score(self, row: Mapping[str, float | int]) -> float:
        values: list[float] = []
        for index, name in enumerate(self.feature_names):
            value = float(row.get(name, 0.0))
            if not math.isfinite(value):
                raise ValueError(f"feature {name} must be finite")
            values.append((value - self.means[index]) / self.scales[index])
        return sum(value * weight for value, weight in zip(values, self.weights))

    def to_dict(self) -> dict[str, object]:
        return {
            "model": "standardized_mean_difference/v1",
            "feature_names": list(self.feature_names),
            "means": list(self.means),
            "scales": list(self.scales),
            "weights": list(self.weights),
            "fit_split": "train",
            "fit_n": self.fit_n,
            "positive_n": self.positive_n,
            "negative_n": self.fit_n - self.positive_n,
        }


__all__ = ["StandardizedMeanDifferenceRanker"]
