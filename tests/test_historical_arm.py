import json
import re
from pathlib import Path

import pytest

from scripts import abc_case
from scripts import historical_arm as ha

CLASSIFICATION = ha.ROOT / "data/historical-arm/classification.json"


def test_committed_classification_is_mechanical_and_complete():
    data = json.loads(CLASSIFICATION.read_text())
    assert data["outcomes_read"] is False
    assert len(data["rows"]) == 46
    assert data["counts"] == {"excluded_deletion": 4, "excluded_moved": 2, "panel": 40}
    for row in data["rows"]:
        assert not {"category", "severity", "results"} & set(row)
        if row["class"] == "panel":
            assert row["old_excerpt"].strip() and row["requirement_without_rule"]
            assert row["c_span"].strip() not in row["requirement_without_rule"]


def test_panel_prompts_are_blind():
    data = json.loads(CLASSIFICATION.read_text())
    for item in ha.panel_items(data):
        prompt = ha.panel_prompt(item["feature"], item["rule"], item["old"])
        for word in (r"gpt-5\.6", "target_only_failure", r"\boracle", r"\bviolat", r"\bluna\b", r"\bsol\b"):
            assert not re.search(word, prompt.lower()), word


def test_sentence_bounds_and_h_text():
    a = "Open the page. Deleting a file moves it to the trash (app.trash). You can restore it. Done."
    c = "Open the page. You can restore it. Done."
    assert ha.h_text(a, c, "absent", None) == (c, "absent_h_equals_c")
    h, how = ha.h_text(a, c, "vaguer", "Deleted files go\nto the bin")
    assert how == "vaguer_old_passage_spliced"
    assert h == "Open the page. Deleted files go to the bin. You can restore it. Done."
    # a span that cuts a sentence is widened to the whole sentence
    a2 = "Match the system theme, including contrast settings. Save."
    c2 = "Match the system theme. Save."
    assert ha.sentence_bounds(a2, *ha.omitted_span(a2, c2)) == (0, len("Match the system theme, including contrast settings."))
    h2, how2 = ha.h_text(a2, c2, "vaguer", "OpenProject will match the system theme.")
    assert how2 == "vaguer_old_passage_spliced" and h2 == "OpenProject will match the system theme. Save."
    # an old passage that already survives in C gives H = C
    assert ha.h_text(a2, c2, "vaguer", "match the system theme") == (c2, "vaguer_passage_survives_in_c")


def test_parse_review_requires_literal_quotes():
    old = "Sign up\nChoose a   long password."
    ok = ha.parse_review('{"feature_documented": "yes", "feature_quote": "Sign up", "rule_status": "vaguer", '
                         '"rule_quote": "Choose a long password."}', old)
    assert ok["rule_status"] == "vaguer"
    with pytest.raises(ValueError):
        ha.parse_review('{"feature_documented": "yes", "feature_quote": "Log in", "rule_status": "absent", '
                        '"rule_quote": null}', old)
    with pytest.raises(ValueError):
        ha.parse_review('{"feature_documented": "no", "feature_quote": null, "rule_status": "same", '
                        '"rule_quote": null}', old)
    with pytest.raises(ValueError):
        ha.parse_review('{"feature_documented": "no", "rule_status": "maybe"}', old)


def _block(prompt: str, name: str) -> str:
    return prompt.split(f"{name}:\n<<<\n", 1)[1].split("\n>>>", 1)[0]


class FakeReviewer:
    """Answers the controls as authored; every case gets feature yes and the rule absent."""

    def __init__(self, model, evidence):
        self.model = model

    def complete(self, request):
        old = _block(request.prompt, "OLD DOCUMENTATION")
        for control in ha.PANEL_CONTROLS:
            if old == control["old"]:
                exp = control["expected"]
                quote = None
                if exp["rule_status"] != "absent":
                    quote = old.splitlines()[2] if exp["rule_status"] != "different" else old.splitlines()[1]
                if exp["rule_status"] == "different":
                    quote = "Archived boards stay in the list with a grey Archived label."
                return json.dumps({"feature_documented": exp["feature_documented"],
                                   "feature_quote": old.splitlines()[0] if exp["feature_documented"] == "yes" else None,
                                   "rule_status": exp["rule_status"], "rule_quote": quote})
        first = next(line for line in old.splitlines() if line.strip())
        return json.dumps({"feature_documented": "yes", "feature_quote": first,
                           "rule_status": "absent", "rule_quote": None})


def test_panel_build_and_collect_schedule(tmp_path: Path):
    out = tmp_path / "panel"
    assert ha.prepare_panel(out, CLASSIFICATION, ["m1", "m2"], "m3", Path("/bin/true"))["cases"] == 40
    summary = ha.run_panel(out, provider_factory=FakeReviewer)
    assert summary["cases"] == 40 and summary["routes"] == {"agreement": 40}
    with pytest.raises(FileExistsError):
        ha.run_panel(out, provider_factory=FakeReviewer)
    cases_out = tmp_path / "cases"
    admission = ha.build(CLASSIFICATION, out / "results.json", cases_out)
    assert admission["counts"]["admitted"] == 40
    assert admission["counts"]["constructions"] == {"absent_h_equals_c": 40}
    assert admission["counts"]["planned_calls"] == 40 * 8
    config = json.loads((cases_out / "nextcloud-delete-folder-trash.json").read_text())
    assert config["arms"]["H"] == config["arms"]["C"]
    case = abc_case.Case(config)
    rows = case.schedule()
    assert len(rows) == 8 and {r["arm"] for r in rows} == {"A", "H"}
    original = abc_case.Case.load("nextcloud-delete-folder-trash")
    assert not {r["slot_id"] for r in rows} & {r["slot_id"] for r in original.schedule()}
    assert case.prompt("H") == original.prompt("C")


def test_panel_stops_when_a_control_fails(tmp_path: Path):
    class Lenient(FakeReviewer):
        def complete(self, request):
            answer = json.loads(super().complete(request))
            if answer["rule_status"] == "vaguer":
                answer.update(rule_status="absent", rule_quote=None)
            return json.dumps(answer)

    out = tmp_path / "panel"
    ha.prepare_panel(out, CLASSIFICATION, ["m1", "m2"], "m3", Path("/bin/true"))
    result = ha.run_panel(out, provider_factory=Lenient)
    assert result["status"] == "stopped_controls_failed"
    with pytest.raises(ValueError):
        ha.build(CLASSIFICATION, out / "results.json", tmp_path / "cases")


def test_abc_case_default_arms_unchanged():
    config = json.loads((abc_case.CASES_DIR / "nextcloud-delete-folder-trash.json").read_text())
    with_h = abc_case.Case({**config, "arms": {**config["arms"], "H": "old"}})
    assert [r["slot_id"] for r in with_h.schedule()] == [r["slot_id"] for r in abc_case.Case(config).schedule()]
    with pytest.raises(ValueError):
        abc_case.Case({**config, "collect_arms": ["A", "H"]})
    with pytest.raises(ValueError):
        abc_case.Case({**config, "arms": {**config["arms"], "Z": "x"}})


def test_analyse_pairs_a_and_h(tmp_path: Path):
    config = json.loads((abc_case.CASES_DIR / "nextcloud-delete-folder-trash.json").read_text())
    cases = tmp_path / "cases"
    cases.mkdir()
    for name, project in (("c1", "p1"), ("c2", "p2")):
        (cases / f"{name}.json").write_text(json.dumps({**config, "case": name, "project_id": project,
                                                        "arms": {**config["arms"], "H": config["arms"]["C"]},
                                                        "historical": {"construction": "absent_h_equals_c"}}))
        rows = [{"model": m, "replication": r, "arm": arm,
                 "category": "target_only_failure" if arm == "H" else "pass"}
                for m in config["models"] for r in (1, 2) for arm in ("A", "H")]
        (tmp_path / "res" / name).mkdir(parents=True)
        (tmp_path / "res" / name / "results.json").write_text(json.dumps({"rows": rows}))
    previous = tmp_path / "prev" / "c1"
    previous.mkdir(parents=True)
    previous.joinpath("results.json").write_text(json.dumps({"rows": [
        {"arm": "A", "category": "pass"}, {"arm": "C", "category": "target_only_failure"}]}))
    report = ha.analyse(tmp_path / "res", cases, previous_root=tmp_path / "prev")
    assert report["finished_cases"] == 2
    assert report["h_vs_a"]["drop"]["estimate"] == 1.0
    assert report["h_vs_a_by_construction"]["absent_h_equals_c"]["cases"] == 2
    assert report["diagnostics"] == {"c1": {"A_now": {"violated": 0, "held": 4, "unknown": 0},
                                            "A_then": {"violated": 0, "held": 1, "unknown": 0},
                                            "H_now": {"violated": 4, "held": 0, "unknown": 0},
                                            "C_then": {"violated": 1, "held": 0, "unknown": 0}}}
