from label_plane.annotation_protocol import BlindedOutputSmellTask, load_annotation_rubric


def test_annotation_rubric_freezes_blinding_missingness_and_irr():
    rubric = load_annotation_rubric()
    assert rubric["rubric_version"] == "rubric-v2"
    assert rubric["missing_label_policy"]["never_impute"] is True
    assert rubric["primary_irr"]["statistic"] == "krippendorff_alpha"
    secondary = rubric["secondary_output_smell_analysis"]
    assert secondary["primary_outcome_independent"] is True
    assert secondary["excluded_from_h1_h2"] is True
    assert secondary["no_automatic_inference_from_requirement_smell"] is True


def test_output_smell_task_exposes_output_but_not_experimental_condition():
    task = BlindedOutputSmellTask.from_record(
        {
            "episode_id": "episode-1",
            "generated_acceptance_criteria": "The order is delayed after some time.",
            "variant": "smelly",
            "defect_family": "missing_condition",
            "oracle_result": False,
        }
    )
    payload = task.to_annotation_payload()
    assert payload["rubric_version"] == "rubric-v2"
    assert "generated_acceptance_criteria" in payload
    assert "variant" not in payload
    assert "oracle_result" not in payload
