from label_plane.constraint_join import join_constraint_lineage_at_t4


def test_t4_join_is_explicitly_label_plane_only():
    rows = join_constraint_lineage_at_t4(
        [
            {"constraint_id": "c1", "status": "covered", "plane": "feature"},
            {"constraint_id": "c2", "status": "omitted", "plane": "feature"},
        ],
        {"c1": "check one", "c2": "check two"},
        {"c1": "must check one", "c2": "must check two"},
    )
    assert rows == [
        {
            "constraint_id": "c1",
            "pre_final_status": "covered",
            "final_criterion": "check one",
            "reference_constraint": "must check one",
            "plane": "label",
        },
        {
            "constraint_id": "c2",
            "pre_final_status": "omitted",
            "final_criterion": "check two",
            "reference_constraint": "must check two",
            "plane": "label",
        },
    ]
