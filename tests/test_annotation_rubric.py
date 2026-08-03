from label_plane.annotation_protocol import load_annotation_rubric


def test_annotation_rubric_freezes_blinding_missingness_and_irr():
    rubric = load_annotation_rubric()
    assert rubric["rubric_version"] == "rubric-v1"
    assert rubric["missing_label_policy"]["never_impute"] is True
    assert rubric["primary_irr"]["statistic"] == "krippendorff_alpha"
