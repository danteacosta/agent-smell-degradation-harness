import json
from pathlib import Path

import pytest

from scripts import mutation_adequacy as ma


def test_eligibility_is_mechanical_and_stable():
    cases = ma.eligible_cases()
    assert len(cases) == 25 and len({c["project_id"] for c in cases}) == 8
    for c in cases:
        assert c["roles"]["correct"] and c["roles"]["mutant"] and c["reference"] in c["roles"]["correct"]
    assert [c["reference"] for c in cases] == [c["reference"] for c in ma.eligible_cases()]


def _row(call, case, project, source, slot, role, verdict, ref=False):
    return {"call_id": call, "case": case, "project_id": project, "source": source, "suite_index": 1,
            "slot_id": slot, "role": role, "is_reference": ref, "verdict": verdict}


def test_soundness_kills_and_naive_score():
    rows = [
        _row("s1", "c", "p", "spec_complete", "a1", "correct", "quiet", ref=True),
        _row("s1", "c", "p", "spec_complete", "m1", "mutant", "assertion_alarm"),
        _row("s1", "c", "p", "spec_complete", "m2", "mutant", "quiet"),
        _row("s1", "c", "p", "spec_complete", "r1", "recovered", "assertion_alarm"),
        # unsound: alarms on the reference, so its alarm on the mutant is not a kill
        _row("s2", "c", "p", "spec_incomplete", "a1", "correct", "assertion_alarm", ref=True),
        _row("s2", "c", "p", "spec_incomplete", "m1", "mutant", "assertion_alarm"),
        _row("s2", "c", "p", "spec_incomplete", "m2", "mutant", "assertion_alarm"),
        _row("s2", "c", "p", "spec_incomplete", "r1", "recovered", "quiet"),
    ]
    s1, s2 = ma.suite_scores(rows)
    assert s1["sound"] and s1["mutation_score"] == 0.5 and s1["naive_killed"] == 2 and s1["naive_mutants"] == 3
    assert s1["recovered_alarms"] == 1
    assert not s2["sound"] and s2["killed"] == 0


def test_project_sign_flip_is_exact_and_grouped():
    # three projects, all positive: only the all-plus and all-minus assignments reach the observed mean
    assert ma.project_sign_flip({"a": [0.5, 0.5], "b": [0.25], "c": [1.0]}) == 2 / 8
    assert ma.project_sign_flip({"a": [0.5], "b": [-0.5]}) == 1.0
    assert ma.project_sign_flip({}) is None


def test_end_to_end_with_fakes(tmp_path: Path, monkeypatch):
    cases = ma.eligible_cases()[:3]
    evidence = tmp_path / "evidence"
    packets = {}
    public = tmp_path / "public"
    for c in cases:
        packet = evidence / "abc" / c["case"]
        (packet / "frozen").mkdir(parents=True)
        (packet / "frozen/manifest.json").write_text("{}")
        src = ma.RESULTS_ROOT / c["case"] / "results.json"
        source_results = json.loads(src.read_text())
        by_slot = {r["slot_id"]: r for r in source_results["rows"]}
        for role, slots in c["roles"].items():
            for slot in slots:
                (packet / "artifacts" / slot).mkdir(parents=True)
                artifact = packet / "artifacts" / slot / "app.html"
                artifact.write_text(f"<html>ROLE:{role}</html>")
                report = packet / "execution" / slot / "report.json"
                ma.ta.put(report, {"app_sha256": ma.ta.sha256_file(artifact)})
                by_slot[slot]["execution"] = {"report_sha256": ma.ta.sha256_file(report)}
        ma.ta.put(packet / "results.json", source_results)
        ma.ta.put(public / c["case"] / "results.json", source_results)
        ma.ta.put(packet / "receipt.json", {"files": ma.ta.inventory(packet)})
        c["results_sha256"] = ma.ta.sha256_file(packet / "results.json")
        packets[c["case"]] = str(packet)
    monkeypatch.setattr(ma, "RESULTS_ROOT", public)
    found = ma.locate(evidence, cases)
    assert found == packets

    complete = {c["case"]: json.loads((ma.CASES_DIR / f"{c['case']}.json").read_text())["arms"]["A"] for c in cases}

    class Tester:
        def __init__(self, evidence):
            pass

        def complete(self, request):
            knows_rule = any(text in request.prompt for text in complete.values())
            return "```js\nmodule.exports = { tests: [{name: 'check', run: async () => {}}] }; // " + ("KILL" if knows_rule else "SOFT") + "\n```"

    def executor(artifact, suite, output):
        role = artifact.read_text().split("ROLE:")[1].split("<")[0]
        kills = "KILL" in suite.read_text()
        return {"status": "complete", "tests": [{"outcome": "assertion_failure" if role == "mutant" and kills else "pass"}]}

    monkey_cases = cases
    out = tmp_path / "study"
    orig = ma.eligible_cases
    ma.eligible_cases = lambda *a, **k: monkey_cases
    try:
        summary = ma.prepare(out, {k: Path(v) for k, v in packets.items()}, "tester", Path("/bin/true"))
        assert summary["calls"] == 3 * len(ma.SOURCES) * ma.SUITES_PER_SOURCE
        ma.generate(out, provider_factory=Tester)
        analysis = ma.execute(out, executor=executor)
    finally:
        ma.eligible_cases = orig
    assert analysis["by_source"]["spec_complete"]["mean_requirement_mutation_score"] == 1.0
    assert analysis["by_source"]["spec_incomplete"]["mean_requirement_mutation_score"] == 0.0
    assert analysis["primary"]["requirements_higher"] == 3
    with pytest.raises(FileExistsError):
        ma.execute(out, executor=executor)
