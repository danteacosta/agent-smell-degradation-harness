from eval.acceptance_criteria_dimensions import evaluate_dimensions

def test_dimensions_keep_structure_coverage_omission_spurious_and_traceability_separate():
    result = evaluate_dimensions(artifact={"criterion":"The link expires in 15 minutes."}, reference_constraints=["link expires in 15 minutes", "single use"], traceability_valid=True)
    assert result == {"structural_validity": 1, "testable_condition_coverage": 1, "semantic_omission": 1, "spurious_criteria": 0, "external_traceability": 1}
