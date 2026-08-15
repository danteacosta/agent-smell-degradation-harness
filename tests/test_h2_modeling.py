from __future__ import annotations

import pytest

from eval.modeling import StandardizedMeanDifferenceRanker


def test_ranker_fits_scaling_and_direction_on_training_rows_only() -> None:
    model = StandardizedMeanDifferenceRanker.fit(
        [{"loss": 0, "errors": 0}, {"loss": 1, "errors": 0}, {"loss": 5, "errors": 2}, {"loss": 6, "errors": 3}],
        [0, 0, 1, 1],
    )

    assert model.score({"loss": 6, "errors": 2}) > model.score({"loss": 0, "errors": 0})
    assert model.to_dict()["fit_split"] == "train"
    assert model.to_dict()["fit_n"] == 4


def test_ranker_fails_closed_on_one_class_or_non_finite_training_data() -> None:
    with pytest.raises(ValueError, match="both classes"):
        StandardizedMeanDifferenceRanker.fit([{"x": 1}, {"x": 2}], [0, 0])
    with pytest.raises(ValueError, match="finite"):
        StandardizedMeanDifferenceRanker.fit([{"x": 1}, {"x": float("nan")}], [0, 1])
