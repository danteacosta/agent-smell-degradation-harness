import json

from eval.blinding_audit import audit_packets, main
from label_plane.annotation_protocol import freeze_blinded_tasks

RECORDS = [{"episode_id": f"ep-{i:03d}", "presented_text": f"The system shall export report {i}."} for i in range(10)]


def test_frozen_tasks_pass():
    tasks, _ = freeze_blinded_tasks(RECORDS, seed=3)
    assert audit_packets(tasks) == {"errors": [], "warnings": []}


def test_nested_and_extra_fields_detected():
    tasks, _ = freeze_blinded_tasks(RECORDS, seed=3)
    tasks[0]["meta"] = {"defect_family": "vague"}
    errors = audit_packets(tasks)["errors"]
    assert any("outside the blinded packet schema" in e for e in errors)
    assert any("meta.defect_family" in e for e in errors)


def test_pair_arm_in_item_id_and_duplicates():
    packets = [
        {"item_id": "p1-clean", "presented_text": "a", "rubric_version": "v", "duplicate_subset": False},
        {"item_id": "p1-clean", "presented_text": "b", "rubric_version": "v", "duplicate_subset": False},
    ]
    errors = audit_packets(packets)["errors"]
    assert any("encodes a pair arm" in e for e in errors)
    assert any("duplicate item_id" in e for e in errors)


def test_telltale_text_warns_and_empty_errors():
    packets = [{"item_id": "x1", "presented_text": "This is the defective variant.", "rubric_version": "v", "duplicate_subset": False}]
    assert audit_packets(packets)["warnings"]
    assert audit_packets([])["errors"] == ["no packets supplied"]


def test_cli_exit_codes(tmp_path, capsys):
    tasks, _ = freeze_blinded_tasks(RECORDS, seed=3)
    good = tmp_path / "ok.jsonl"
    good.write_text("\n".join(json.dumps(t) for t in tasks), encoding="utf-8")
    assert main(["--packets", str(good)]) == 0
    tasks[0]["oracle_label"] = 1
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(tasks), encoding="utf-8")
    assert main(["--packets", str(bad)]) == 1
