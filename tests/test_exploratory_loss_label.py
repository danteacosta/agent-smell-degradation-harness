from __future__ import annotations

import pytest

from protocol.labels import exploratory_loss_label


@pytest.mark.parametrize("variant", ["clean", "smelly"])
def test_label_depends_only_on_the_oracle(variant: str) -> None:
    assert exploratory_loss_label({"variant": variant, "oracle_passed": False}) == 1
    assert exploratory_loss_label({"variant": variant, "oracle_passed": True}) == 0


@pytest.mark.parametrize("value", [None, "false", 0])
def test_missing_or_non_boolean_outcome_fails_closed(value: object) -> None:
    with pytest.raises(ValueError):
        exploratory_loss_label({"variant": "smelly", "oracle_passed": value})
