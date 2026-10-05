import json
from pathlib import Path

import pytest

from scripts import mutation_adequacy as ma


@pytest.fixture
def source_packet(tmp_path, monkeypatch):
    case = ma.eligible_cases()[0]
    packet = tmp_path / "source"
    source_results = tmp_path / "public" / case["case"]
    source_results.mkdir(parents=True)
    rows = []
    for role, slots in case["roles"].items():
        for slot in slots:
            artifact = packet / "artifacts" / slot / "app.html"
            ma.ta.put(artifact, f"<html>ROLE:{role}</html>")
            report = packet / "execution" / slot / "report.json"
            ma.ta.put(report, {"app_sha256": ma.ta.sha256_file(artifact)})
            rows.append({"slot_id": slot, "arm": "A" if role == "correct" else "C",
                         "category": "target_only_failure" if role == "mutant" else "pass",
                         "execution": {"report_sha256": ma.ta.sha256_file(report)}})
    ma.ta.put(packet / "frozen/manifest.json", {})
    document = {"rows": rows}
    ma.ta.put(packet / "results.json", document)
    ma.ta.put(source_results / "results.json", document)
    ma.ta.put(packet / "receipt.json", {"files": ma.ta.inventory(packet)})
    case = {**case, "results_sha256": ma.ta.sha256_file(packet / "results.json")}
    monkeypatch.setattr(ma, "RESULTS_ROOT", source_results.parent)
    monkeypatch.setattr(ma, "eligible_cases", lambda: [case])
    return case, packet


def prepared_study(tmp_path, source_packet):
    case, packet = source_packet
    out = tmp_path / "study"
    ma.prepare(out, {case["case"]: packet}, "tester", Path("/bin/true"))
    return out


@pytest.mark.parametrize("field", ["script_sha256", "test_anchor_script_sha256", "image"])
def test_rejects_runtime_that_differs_from_frozen_identity(tmp_path, source_packet, field):
    out = prepared_study(tmp_path, source_packet)
    manifest_path = out / "frozen/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest[field] = "unexpected-runtime"
    manifest_path.write_text(json.dumps(manifest))
    receipt = ma.ta.inventory(out / "frozen")
    receipt.pop("receipt.json")
    (out / "frozen/receipt.json").write_text(json.dumps({"files": receipt}))
    with pytest.raises(ValueError, match="drift"):
        ma.verify(out)


def test_rejects_changed_source_artifact_before_freezing_new_prompts(tmp_path, source_packet):
    case, packet = source_packet
    (packet / "artifacts" / case["reference"] / "app.html").write_text("changed since oracle execution")
    with pytest.raises(ValueError, match="source artifact"):
        ma.prepare(tmp_path / "study", {case["case"]: packet}, "tester", Path("/bin/true"))


def test_rejects_suite_changed_after_generation_before_browser_execution(tmp_path, source_packet):
    out = prepared_study(tmp_path, source_packet)

    class Tester:
        def __init__(self, evidence):
            pass

        def complete(self, request):
            return "```js\nmodule.exports = { tests: [{name: 'smoke', run: async () => {}}] };\n```"

    ma.generate(out, provider_factory=Tester)
    suite = next((out / "calls").glob("*/suite.cjs"))
    suite.write_text("module.exports = { tests: [] }; // replaced")
    with pytest.raises(ValueError, match="suite drift"):
        ma.execute(out)
    assert not (out / "execution-started.json").exists()


def test_any_runner_error_makes_suite_unusable_and_unable_to_kill():
    base = {"call_id": "suite", "case": "case", "project_id": "project", "source": "spec_complete"}
    rows = [{**base, "slot_id": "a", "role": "correct", "is_reference": True, "verdict": "quiet"},
            {**base, "slot_id": "c1", "role": "mutant", "is_reference": False, "verdict": "runner_error"},
            {**base, "slot_id": "c2", "role": "mutant", "is_reference": False, "verdict": "assertion_alarm"}]
    score = ma.suite_scores(rows)[0]
    assert score["unusable"] and not score["sound"]
    assert score["killed"] == 0 and score["mutation_score"] == 0


def test_naive_score_counts_unconfirmed_c_without_counting_it_as_confirmed_mutant():
    base = {"call_id": "suite", "case": "case", "project_id": "project", "source": "spec_complete"}
    rows = [{**base, "slot_id": "a", "role": "correct", "is_reference": True, "verdict": "quiet"},
            {**base, "slot_id": "m", "role": "mutant", "is_reference": False, "verdict": "assertion_alarm"},
            {**base, "slot_id": "r", "role": "recovered", "is_reference": False, "verdict": "quiet"},
            {**base, "slot_id": "u", "role": "unconfirmed", "is_reference": False, "verdict": "assertion_alarm"}]
    score = ma.suite_scores(rows)[0]
    assert score["mutants"] == 1 and score["killed"] == 1
    assert score["naive_mutants"] == 3 and score["naive_killed"] == 2


def test_docker_timeout_removes_its_container_before_returning(tmp_path, monkeypatch):
    import subprocess

    artifact, suite = tmp_path / "app.html", tmp_path / "suite.cjs"
    artifact.write_text("<html></html>")
    suite.write_text("module.exports = {tests: []};")
    started, removed = [], []

    def docker_command(command, **options):
        if command[:2] == ["docker", "run"]:
            started.append(command[command.index("--name") + 1])
            raise subprocess.TimeoutExpired(command, options["timeout"])
        if command[:3] == ["docker", "rm", "-f"]:
            removed.append(command[3])
            return subprocess.CompletedProcess(command, 0)
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(subprocess, "run", docker_command)
    with pytest.raises(subprocess.TimeoutExpired):
        ma.ta.docker_execute(artifact, suite, tmp_path / "execution")
    assert removed == started and len(removed) == 1


def test_confirmed_and_naive_scores_use_the_same_requirement_weighting():
    rows = []
    for case, mutants, recovered in [("small", 1, 1), ("large", 3, 7)]:
        base = {"call_id": case, "case": case, "project_id": case, "source": "spec_complete"}
        rows.append({**base, "slot_id": "a", "role": "correct", "is_reference": True, "verdict": "quiet"})
        for n in range(mutants):
            rows.append({**base, "slot_id": f"m{n}", "role": "mutant", "is_reference": False,
                         "verdict": "assertion_alarm"})
        for n in range(recovered):
            rows.append({**base, "slot_id": f"r{n}", "role": "recovered", "is_reference": False,
                         "verdict": "quiet"})
    result = ma.analyse(rows)["by_source"]["spec_complete"]
    assert result["mean_requirement_mutation_score"] == 1
    assert result["naive_mean_requirement_mutation_score"] == pytest.approx(0.4)
    assert result["confirmed_score_pooled"] == 1
    assert result["naive_score_pooled"] == pytest.approx(4 / 12)
