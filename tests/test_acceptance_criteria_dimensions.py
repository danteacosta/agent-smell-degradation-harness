from eval.acceptance_criteria_dimensions import evaluate_dimensions

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
