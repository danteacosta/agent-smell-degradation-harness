from eval.acceptance_criteria_dimensions import evaluate_dimensions
from pathlib import Path
import json

FIXTURES = Path(__file__).parent / "fixtures"

def test_dimensions_keep_structure_coverage_omission_spurious_and_traceability_separate():
    result = evaluate_dimensions(
        artifact={"criterion": "The link expires in 15 minutes."},
        reference_constraints=["c_expiry", "c_single_use"],
        constraint_outcomes=[
            {"constraint_id": "c_expiry", "status": "covered"},
            {"constraint_id": "c_single_use", "status": "omitted"},
        ],
        traceability_valid=True,
    )
    assert result == {"structural_validity": 1, "testable_condition_coverage": 1, "semantic_omission": 1, "spurious_criteria": 0, "external_traceability": 1}


def test_semantic_dimensions_never_fall_back_to_substring_matching():
    try:
        evaluate_dimensions(
            artifact={"criterion": "single use"},
            reference_constraints=["c_single_use"],
            constraint_outcomes=[],
        )
    except ValueError as error:
        assert "exactly the reference constraint IDs" in str(error)
    else:
        raise AssertionError("reviewed constraint outcomes must be mandatory")


def test_valid_fixture_is_a_t4_label_plane_contract():
    outcomes = json.loads((FIXTURES / "constraint_outcomes_valid.json").read_text())
    result = evaluate_dimensions(
        artifact={"criterion": "The link expires in 15 minutes."},
        reference_constraints=["c_expiry", "c_single_use"],
        constraint_outcomes=outcomes,
    )
    assert result["testable_condition_coverage"] == 1
    assert result["semantic_omission"] == 1


def test_feature_plane_fixture_is_rejected():
    outcomes = json.loads((FIXTURES / "constraint_outcomes_invalid_feature_plane.json").read_text())
    try:
        evaluate_dimensions(
            artifact={"criterion": "anything"},
            reference_constraints=["c_expiry"],
            constraint_outcomes=outcomes,
        )
    except ValueError as error:
        assert "label plane" in str(error)
    else:
        raise AssertionError("T4 outcome must not enter through the feature plane")
