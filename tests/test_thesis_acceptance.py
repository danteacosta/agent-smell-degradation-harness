from __future__ import annotations

from pathlib import Path

import pytest

from feature_plane import DeployableFeatureInput, extract_deployable_features
from protocol.paired_stats import (
    clustered_bootstrap_ci,
    ordinal_paired_delta,
    paired_permutation_pvalue,
)


def test_deployable_features_do_not_accept_injected_defect_metadata(tmp_path: Path) -> None:
    trace = tmp_path / "events.jsonl"
    trace.write_text(
        '{"event_type":"interpretation.completed","checkpoint":"interpretation.completed","attributes":{"constraint_count":2},"sequence_number":1}\n',
        encoding="utf-8",
    )

    feature_input = DeployableFeatureInput(
        intent_id="I-1",
        task_family="acceptance_criteria",
        requirement_text="Refund orders after 15 minutes.",
    )

    features = extract_deployable_features(feature_input, trace)

    assert "smell_present" not in str(features)
    assert "variant" not in str(features)
    assert features["provenance"]["constraint_count"] == 2


def test_deployable_input_rejects_terminal_oracle_fields() -> None:
    with pytest.raises(TypeError):
        DeployableFeatureInput(
            intent_id="I-1",
            task_family="acceptance_criteria",
            requirement_text="Refund orders.",
            oracle_passed=True,  # type: ignore[call-arg]
        )


def test_ordinal_delta_and_clustered_interval_are_reproducible() -> None:
    clean = [2, 3, 2, 1]
    defective = [1, 1, 2, 0]
    assert ordinal_paired_delta(clean, defective) == 1.0
    values = {"i1": [1.0, 1.0], "i2": [0.0, 1.0]}
    first = clustered_bootstrap_ci(values, n_boot=200, seed=7)
    assert first == clustered_bootstrap_ci(values, n_boot=200, seed=7)
    assert first[0] <= 0.75 <= first[1]


def test_paired_permutation_returns_probability_for_no_effect() -> None:
    assert paired_permutation_pvalue([0.0, 0.0], seed=2) == 1.0
