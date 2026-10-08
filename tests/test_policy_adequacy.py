import json
import os
from pathlib import Path

import pytest

from scripts import policy_adequacy as pa

POLICY = "# P\n\nAlways greet.\n\nRules:\n- Never refund.\n- Max two bags.\n\nEnd.\n"


def toy():
    return {"source": {"policy_sha256": pa.sha256(POLICY)},
            "rules": [{"id": "R01", "section": "s", "name": "greet", "lines": [3, 3], "text": "Always greet.",
                       "negation": "Never greet."},
                      {"id": "R02", "section": "s", "name": "refund", "lines": [6, 6], "text": "- Never refund.",
                       "negation": "- Always refund."}],
            "controls": [{"id": "B01", "rewords": "R02", "lines": [6, 6], "text": "- Never refund.",
                          "rewording": "- Refunds are never given."}]}


def test_validate_rejects_drift_and_mismatch():
    pa.validate(toy(), POLICY)
    with pytest.raises(ValueError, match="drift"):
        pa.validate(toy(), POLICY + " ")
    bad = toy(); bad["rules"][0]["text"] = "Greet."
    with pytest.raises(ValueError, match="does not match"):
        pa.validate(bad, POLICY)
    bad = toy(); bad["rules"][1]["lines"] = [3, 3]; bad["rules"][1]["text"] = "Always greet."
    with pytest.raises(ValueError, match="overlaps"):
        pa.validate(bad, POLICY)


def test_variants_change_exactly_one_span():
    v = pa.variants(toy(), POLICY)
    assert set(v) == {"A", "D01", "N01", "D02", "N02", "B01"}
    assert v["D01"] == "# P\n\nRules:\n- Never refund.\n- Max two bags.\n\nEnd.\n"
    assert v["N02"] == POLICY.replace("- Never refund.", "- Always refund.")
    assert v["B01"] == POLICY.replace("- Never refund.", "- Refunds are never given.")
    assert "\n\n\n" not in v["D01"]


def test_build_creates_one_data_root_per_variant(tmp_path):
    tau2 = tmp_path / "tau2"
    air = tau2 / "data/tau2/domains/airline"
    air.mkdir(parents=True)
    (air / "policy.md").write_text(POLICY)
    (air / "tasks.json").write_text("[]")
    (tau2 / "data/tau2/domains/retail").mkdir()
    (tau2 / "data/tau2/user_simulator").mkdir()
    manifest = pa.build(tau2, tmp_path / "out", toy())
    assert len(manifest) == 6
    root = tmp_path / "out/N01"
    assert (root / "tau2/domains/airline/policy.md").read_text().startswith("# P\n\nNever greet.")
    assert (root / "tau2/domains/airline/tasks.json").is_symlink()
    assert (root / "tau2/domains/retail").is_symlink() and (root / "tau2/user_simulator").is_symlink()
    with pytest.raises(FileExistsError):
        pa.build(tau2, tmp_path / "out", toy())


def test_plan_is_seeded_and_staged():
    inv = pa.load_rules()
    p1, p2 = pa.plan(inv), pa.plan(inv)
    assert p1 == p2
    assert [b["variant"] for b in p1[:pa.BASELINE_TRIALS]] == ["A"] * pa.BASELINE_TRIALS
    stages = [b["stage"] for b in p1]
    assert stages == sorted(stages)
    assert sum(b["variant"].startswith("N") for b in p1) == len(inv["rules"])
    assert sum(b["variant"].startswith("D") and b["stage"] == 2 for b in p1) == len(inv["rules"])


def rows(variant, task, rewards):
    return [{"variant": variant, "task_id": task, "reward": r} for r in rewards]


def test_analysis_classes_and_confirmation():
    inv = toy()
    tasks = ["t1", "t2", "t3"]
    data = []
    data += rows("A", "t1", [1, 1, 1, 1]) + rows("A", "t2", [1, 1, 1, 0]) + rows("A", "t3", [1, 0, 0, 0])
    # R01: inversion confirmed on t1, deletion silent -> covered_but_omission_silent
    data += rows("N01", "t1", [0, 0, 1]) + rows("N01", "t2", [1])
    data += rows("D01", "t1", [1]) + rows("D01", "t2", [1])
    # R02: inversion fails once but not confirmed; deletion passes -> uncovered
    data += rows("N02", "t1", [0, 1, 1]) + rows("N02", "t2", [1])
    data += rows("D02", "t1", [1]) + rows("D02", "t2", [1])
    # t3 is ineligible: its failures never count
    data += rows("N02", "t3", [0, 0, 0])
    data += rows("B01", "t1", [1]) + rows("B01", "t2", [1])
    res = pa.analyse(inv, data, tasks)
    assert res["eligible_tasks"] == 2
    by = {p["id"]: p for p in res["per_rule"]}
    assert by["R01"]["class"] == "covered_but_omission_silent"
    assert by["R01"]["negation"]["confirmed_tasks"] == ["t1"]
    assert by["R02"]["class"] == "uncovered"
    assert res["covered_under_negation"] == 1 and res["control_confirmed_detections"] == 0


def test_unconfirmed_failures_are_pending_and_listed_for_reruns():
    inv = toy()
    tasks = ["t1"]
    data = rows("A", "t1", [1, 1, 1, 1]) + rows("N01", "t1", [0]) + rows("D01", "t1", [1])
    data += rows("N02", "t1", [1]) + rows("D02", "t1", [1]) + rows("B01", "t1", [1])
    res = pa.analyse(inv, data, tasks)
    assert {p["id"]: p["class"] for p in res["per_rule"]}["R01"] == "incomplete"
    assert pa.candidates(inv, data, tasks) == [{"variant": "N01", "task_id": "t1", "reruns": pa.CONFIRM_RERUNS}]


def test_baseline_must_be_complete():
    with pytest.raises(ValueError, match="BASELINE_TRIALS"):
        pa.analyse(toy(), rows("A", "t1", [1, 1]), ["t1"])


def test_read_tau2_results(tmp_path):
    f = tmp_path / "r.json"
    f.write_text(json.dumps({"simulations": [
        {"task_id": 3, "trial": 0, "reward_info": {"reward": 1.0}, "termination_reason": "user_stop"},
        {"task_id": "4", "trial": 0, "reward_info": None, "termination_reason": "max_steps"}]}))
    r = pa.read_tau2_results(f, "N01")
    assert r[0] == {"variant": "N01", "task_id": "3", "reward": 1.0, "termination_reason": "user_stop"}
    assert not pa.passed(r[1])


def test_committed_inventory_is_well_formed():
    inv = pa.load_rules()
    assert inv["status"] == "draft_pending_human_review"
    assert len(inv["rules"]) == 32 and len(inv["controls"]) == 5
    starts = [r["lines"][0] for r in inv["rules"]]
    assert starts == sorted(starts)
    for r in inv["rules"]:
        assert r["negation"] != r["text"] and r["text"].strip()


@pytest.mark.skipif(not os.environ.get("TAU2_CHECKOUT"), reason="needs a pinned tau2-bench checkout")
def test_inventory_matches_pinned_policy():
    policy = (Path(os.environ["TAU2_CHECKOUT"]) / "data/tau2/domains/airline/policy.md").read_text()
    pa.validate(pa.load_rules(), policy)
    assert len(pa.variants(pa.load_rules(), policy)) == 70
