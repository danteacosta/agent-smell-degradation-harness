from __future__ import annotations

import json

import pytest


def test_blinded_task_redacts_experimental_metadata_and_keeps_duplicate_metadata():
    from label_plane.annotation_protocol import BlindedAnnotationTask

    task = BlindedAnnotationTask.from_record(
        {
            "episode_id": "e-1",
            "requirement_text": "Implement a parser",
            "variant": "smelly",
            "defect_family": "hidden-state",
            "oracle_label": "degraded",
            "model_id": "gpt-test",
            "artifact": {"secret": "terminal output"},
        },
        duplicate_subset=True,
        rubric_version="rubric-1",
    )
    payload = task.to_annotation_payload()

    assert payload["item_id"] == "e-1"
    assert payload["duplicate_subset"] is True
    assert payload["rubric_version"] == "rubric-1"
    for forbidden in ("variant", "defect_family", "oracle_label", "model_id", "artifact"):
        assert forbidden not in payload


def test_missing_label_requires_reason_and_exports_disagreement_and_adjudication(tmp_path):
    from label_plane.adjudication import adjudicate, export_adjudications, find_disagreements
    from label_plane.human_annotation import HumanAnnotation, export_annotations

    annotations = [
        HumanAnnotation(item_id="e-1", annotator_id="a", label="clean"),
        HumanAnnotation(item_id="e-1", annotator_id="b", label="smelly"),
        HumanAnnotation(item_id="e-2", annotator_id="a", label=None, missing_reason="not-visible"),
    ]
    disagreements = find_disagreements(annotations)
    assert [row.item_id for row in disagreements] == ["e-1"]
    with pytest.raises(ValueError, match="tie"):
        adjudicate(annotations[:2])

    raw_path = tmp_path / "raw.json"
    export_annotations(raw_path, annotations)
    rows = json.loads(raw_path.read_text(encoding="utf-8"))
    assert rows[2]["missing_reason"] == "not-visible"
    adjudicated = adjudicate(
        [
            HumanAnnotation(item_id="e-1", annotator_id="a", label="clean"),
            HumanAnnotation(item_id="e-1", annotator_id="b", label="clean"),
        ],
        adjudicator_id="chair",
        rationale="unambiguous rubric example",
    )
    output = tmp_path / "adjudicated.json"
    export_adjudications(output, [adjudicated])
    assert json.loads(output.read_text(encoding="utf-8"))[0]["adjudicator_id"] == "chair"


def test_secondary_judgement_cannot_be_adjudicated_as_primary():
    from label_plane.adjudication import adjudicate
    from label_plane.human_annotation import HumanAnnotation

    secondary = HumanAnnotation(
        item_id="e-1", annotator_id="llm", label="clean", source="llm_judge_secondary"
    )
    with pytest.raises(ValueError, match="secondary"):
        adjudicate([secondary])


def test_duplicate_subset_is_reproducible_and_must_be_double_coded():
    from label_plane.annotation_protocol import select_duplicate_subset, validate_duplicate_subset
    from label_plane.human_annotation import HumanAnnotation

    selected = select_duplicate_subset(["e-1", "e-2", "e-3", "e-4"], fraction=0.5, seed=9)
    assert selected == select_duplicate_subset(["e-4", "e-3", "e-2", "e-1"], fraction=0.5, seed=9)
    with pytest.raises(ValueError, match="double-coded"):
        validate_duplicate_subset([HumanAnnotation(item_id=selected[0], annotator_id="a", label="ok")], selected)
