import copy
import json
from pathlib import Path

import pytest

from scripts import mutation_alarm_sensitivity as audit


def packet():
    calls = [dict(call_id=f"{source}-{i}", case="r", project_id="p", source=source,
                  suite_index=i, targets=["a", "m", "other"])
             for source in audit.ma.SOURCES for i in (1, 2)]
    manifest = dict(model="fixture", cases=[dict(case="r", project_id="p", reference="a",
                    roles=dict(correct=["a", "other"], mutant=["m"], recovered=[], unconfirmed=[]))],
                    schedule=calls)
    rows = [dict(call_id=c["call_id"], case="r", project_id="p", source=c["source"],
                 suite_index=c["suite_index"], slot_id=slot, role="mutant" if slot == "m" else "correct",
                 is_reference=slot == "a", verdict="error_alarm" if slot == "m" else "quiet")
            for c in calls for slot in c["targets"]]
    return dict(rows=rows, analysis=audit.ma.analyse(rows)), manifest


def test_error_kill_is_not_an_assertion_kill_and_does_not_mutate_original():
    data, manifest = packet()
    before = copy.deepcopy(data)
    source = audit.analyse(data, manifest)["by_source"]["spec_complete"]
    assert source["registered_score"] == 1
    assert source["assertion_only_score"] == source["assertion_kills"] == 0
    assert source["error_kills"] == 2
    assert data == before


def test_duplicate_pair_is_rejected_before_aggregate_analysis_can_mask_it():
    data, manifest = packet()
    data["rows"].append(copy.deepcopy(data["rows"][2]))
    with pytest.raises(ValueError, match="duplicate or unexpected pair"):
        audit.validate(data["rows"], manifest)


def test_assertion_score_preserves_reference_gate_and_failure_denominator():
    data, manifest = packet()
    for row in data["rows"]:
        if row["source"] == "spec_complete":
            if row["suite_index"] == 2:
                row["verdict"] = "generation_failed"
            elif row["role"] == "mutant":
                row["verdict"] = "assertion_alarm"
        if row["source"] == "spec_incomplete":
            row["verdict"] = "assertion_alarm"  # reference rejects: no kill credit
    data["analysis"] = audit.ma.analyse(data["rows"])
    report = audit.analyse(data, manifest)
    source = report["by_source"]["spec_complete"]
    assert source["planned_mutant_pairs"] == 2
    assert source["eligible_mutant_pairs"] == 1
    assert source["assertion_only_score"] == 0.5
    assert report["by_source"]["spec_incomplete"]["assertion_only_score"] == 0
    assert report["target_specificity"] == "not_established_by_aggregate_verdicts"


@pytest.mark.parametrize("change", ["missing", "duplicate", "role", "project", "reference",
                                   "verdict", "mixed_failure", "design", "targets", "analysis"])
def test_corrupted_public_grid_is_refused(change):
    data, manifest = packet()
    if change == "missing":
        data["rows"].pop()
    elif change == "duplicate":
        data["rows"].append(data["rows"][0])
    elif change in ("role", "project", "verdict"):
        key = "project_id" if change == "project" else change
        data["rows"][0][key] = "invalid"
    elif change == "reference":
        data["rows"][0]["is_reference"] = 1
    elif change == "mixed_failure":
        data["rows"][0]["verdict"] = "generation_failed"
    elif change == "design":
        manifest["schedule"][0]["suite_index"] = 2
    elif change == "targets":
        manifest["schedule"][0]["targets"].pop()
    else:
        data["analysis"]["by_source"]["spec_complete"]["sound"] = 99
    with pytest.raises(ValueError):
        audit.analyse(data, manifest)


@pytest.mark.parametrize("path", ["v1", "claude-evaluation-v1/claude-sonnet-4-6",
                                  "claude-evaluation-v1/claude-opus-4-6"])
def test_published_packets_reproduce_and_assertion_score_is_bounded(path):
    root = Path(__file__).resolve().parents[1] / "data/shared-omission-e2e" / path
    data = json.loads((root / "results.json").read_text())
    manifest = json.loads((root / "frozen-manifest-public.json").read_text())
    report = audit.analyse(data, manifest)
    assert report["requirements"] == 25 and report["projects"] == 8
    for source in report["by_source"].values():
        assert source["planned_suites"] == 50
        assert source["planned_mutant_pairs"] == 162
        assert 0 <= source["assertion_only_score"] <= source["registered_score"]
