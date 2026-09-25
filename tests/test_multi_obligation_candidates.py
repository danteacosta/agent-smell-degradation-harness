import json

import pytest

from scripts import multi_obligation_candidates as candidates


def _copy_register(tmp_path):
    payload = json.loads(candidates.REGISTER_PATH.read_text())
    path = tmp_path / "candidates.json"
    path.write_text(json.dumps(payload))
    return path


def test_canonical_register_has_two_candidates_per_project() -> None:
    assert candidates.validate(candidates.REGISTER_PATH) == {
        "projects": 6,
        "candidates": 12,
        "planned_positions": 216,
    }


def test_register_rejects_source_hash_drift(tmp_path) -> None:
    path = _copy_register(tmp_path)
    payload = json.loads(path.read_text())
    payload["candidates"][0]["source"]["sha256"] = "0" * 64
    path.write_text(json.dumps(payload))

    with pytest.raises(ValueError, match="source hash drift"):
        candidates.validate(path)


def test_register_rejects_duplicate_candidate_id(tmp_path) -> None:
    path = _copy_register(tmp_path)
    payload = json.loads(path.read_text())
    payload["candidates"][1]["candidate_id"] = payload["candidates"][0]["candidate_id"]
    path.write_text(json.dumps(payload))

    with pytest.raises(ValueError, match="candidate identity drift"):
        candidates.validate(path)


def test_register_rejects_excerpt_not_present_in_source(tmp_path) -> None:
    path = _copy_register(tmp_path)
    payload = json.loads(path.read_text())
    payload["candidates"][0]["source"]["exact_excerpt"] = "not in the source"
    path.write_text(json.dumps(payload))

    with pytest.raises(ValueError, match="source excerpt drift"):
        candidates.validate(path)


def test_register_rejects_excerpt_outside_declared_lines(tmp_path) -> None:
    path = _copy_register(tmp_path)
    payload = json.loads(path.read_text())
    payload["candidates"][0]["source"]["line_start"] = 1
    payload["candidates"][0]["source"]["line_end"] = 1
    path.write_text(json.dumps(payload))

    with pytest.raises(ValueError, match="source locator drift"):
        candidates.validate(path)


def test_canonical_screening_preserves_unanimity_gate() -> None:
    assert candidates.validate_screening(candidates.SCREENING_PATH) == {
        "reviewers": 3,
        "candidates": 12,
        "unanimously_accepted": 3,
        "deferred": 9,
        "eligible_positions": 54,
    }


def test_screening_rejects_consensus_drift(tmp_path) -> None:
    payload = json.loads(candidates.SCREENING_PATH.read_text())
    payload["consensus"][0]["verdict"] = "ACCEPT"
    path = tmp_path / "screening.json"
    path.write_text(json.dumps(payload))

    with pytest.raises(ValueError, match="screening consensus drift"):
        candidates.validate_screening(path)
