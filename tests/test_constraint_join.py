from label_plane.constraint_join import join_constraint_lineage_at_t4
def test_t4_join_is_explicitly_label_plane_only():
    rows=join_constraint_lineage_at_t4([{"constraint_id":"c1","status":"covered","plane":"feature"}],{"c1":"check"},{"c1":"must check"})
    assert rows[0]["plane"]=="label" and rows[0]["final_criterion"]=="check"
