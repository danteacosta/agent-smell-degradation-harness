from __future__ import annotations

import pytest

from protocol.conditional_semantics import validate_conditional_semantics


def _item() -> dict[str, object]:
    return {
        "antecedent": "the request exceeds five minutes",
        "consequent": "the request is rejected",
        "necessity_status": "sufficient_only",
        "temporal_relation": "next_state",
        "negative_case": {
            "status": "specified",
            "description": "the request is at or below five minutes",
        },
    }


def test_conditional_semantics_normalizes_valid_items() -> None:
    assert validate_conditional_semantics([_item()]) == [_item()]
    assert validate_conditional_semantics([]) == []


@pytest.mark.parametrize(
    "mutation, message",
    [
        (lambda item: item.update(necessity_status="invalid"), "necessity_status"),
        (lambda item: item["negative_case"].update(status="not_specified"), "description"),
        (lambda item: item.update(smell="missing-condition"), "exactly"),
        (lambda item: item.update(antecedent=""), "antecedent"),
    ],
)
def test_conditional_semantics_rejects_malformed_items(mutation, message: str) -> None:
    item = _item()
    mutation(item)
    with pytest.raises(ValueError, match=message):
        validate_conditional_semantics([item])
