from __future__ import annotations

import json

from label_plane.annotation_protocol import freeze_blinded_tasks


def test_freeze_blinded_tasks_is_outcome_blind_and_reproducible() -> None:
    records = [
        {
            "episode_id": f"episode-{index}",
            "presented_text": f"Visible annotation material {index}.",
            "variant": "smelly",
            "oracle_label": "degraded",
            "model_id": "provider-secret",
            "artifact": {"terminal": True},
        }
        for index in range(10)
    ]

    tasks_a, selection_a = freeze_blinded_tasks(records, fraction=0.2, seed=17)
    tasks_b, selection_b = freeze_blinded_tasks(
        list(reversed(records)),
        fraction=0.2,
        seed=17,
    )

    assert tasks_a == tasks_b
    assert selection_a == selection_b
    assert selection_a["duplicate_item_count"] == 2
    assert all(task["duplicate_subset"] is (task["item_id"] in selection_a["duplicate_item_ids"]) for task in tasks_a)
    for task in tasks_a:
        assert "variant" not in task
        assert "oracle_label" not in task
        assert "model_id" not in task
        assert "artifact" not in task
