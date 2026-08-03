from __future__ import annotations

import pytest


def test_krippendorff_alpha_supports_nominal_and_ordinal_levels_with_missing_values():
    from protocol.irr import krippendorff_alpha

    assert krippendorff_alpha([["a", "b", "c"], ["a", "b", "c"]]) == 1.0
    assert krippendorff_alpha([[1, 2, 3], [1, 2, 2]], level_of_measurement="ordinal") > 0.0
    assert krippendorff_alpha([["a", None, "c"], ["a", "b", "c"]]) == 1.0


def test_bootstrap_ci_is_deterministic_and_decision_narrows_claims_when_alpha_is_low():
    from protocol.irr import bootstrap_krippendorff_alpha, irr_decision

    data = [["a", "a", "b", "b"], ["a", "b", "a", "b"]]
    first = bootstrap_krippendorff_alpha(data, n_bootstrap=200, seed=7)
    second = bootstrap_krippendorff_alpha(data, n_bootstrap=200, seed=7)
    assert first == second
    assert first["lower"] <= first["alpha"] <= first["upper"]
    decision = irr_decision(first["alpha"])
    assert decision.adjudication_required is True
    assert decision.claim_narrowing_required is True


def test_alpha_rejects_unknown_measurement_level():
    from protocol.irr import krippendorff_alpha

    with pytest.raises(ValueError, match="measurement"):
        krippendorff_alpha([["a"], ["b"]], level_of_measurement="interval")

