from pathlib import Path
import hashlib
import signal
from xml.etree import ElementTree
import subprocess
import sys

import pytest

from eval import todomvc_escape_qualification as qualification


def checkout(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "todomvc"
    component = root / qualification.COMPONENT
    oracle = root / qualification.ORACLE
    component.parent.mkdir(parents=True)
    oracle.parent.mkdir(parents=True)
    component.write_text(f'<input {qualification.GOLD_BINDING}>', encoding="utf-8")
    oracle.write_text("\n".join(qualification.REQUIRED_ORACLE_ASSERTIONS), encoding="utf-8")
    (root / qualification.ROOT_LOCK).write_text("root-lock", encoding="utf-8")
    vue_lock = root / qualification.VUE_LOCK
    vue_lock.parent.mkdir(parents=True, exist_ok=True)
    vue_lock.write_text("vue-lock", encoding="utf-8")

    def fake_git(_checkout, *args):
        if args == ("rev-parse", "HEAD"):
            return qualification.REVISION
        path = Path(args[1].split(":", 1)[1])
        return qualification.UPSTREAM_BLOBS[path]

    monkeypatch.setattr(qualification, "_git", fake_git)
    return root


def junit(failure=None, name="TodoMVC - vue Editing should cancel edits on escape",
          failure_type="AssertionError", extra=False):
    root = ElementTree.Element("testsuites")
    suite = ElementTree.SubElement(root, "testsuite")
    test = ElementTree.SubElement(suite, "testcase", name=name)
    if failure is not None:
        ElementTree.SubElement(test, "failure", type=failure_type, message=failure)
    if extra:
        ElementTree.SubElement(suite, "testcase", name="another test")
    return ElementTree.tostring(root).decode()


EXPECTED_FAILURE = "Timed out retrying: expected '<li>' to contain 'feed the cat', but the text was 'foo'"


def oracle_command(mutant_report=None, gold_report=None, mutant_exit=1) -> list[str]:
    gold_report = junit() if gold_report is None else gold_report
    mutant_report = junit(EXPECTED_FAILURE) if mutant_report is None else mutant_report
    code = (
        "from pathlib import Path; "
        "text=Path('examples/vue/src/components/TodoItem.vue').read_text(); "
        "gold='cancelEdit' in text; "
        f"Path('todomvc-qualification-junit.xml').write_text({gold_report!r} if gold else {mutant_report!r}); "
        f"raise SystemExit(0 if gold else {mutant_exit})"
    )
    return [sys.executable, "-c", code]


def test_same_command_passes_gold_kills_mutant_and_restores_file(tmp_path, monkeypatch):
    root = checkout(tmp_path, monkeypatch)
    original = (root / qualification.COMPONENT).read_bytes()
    output = tmp_path / "receipt.json"
    receipt = qualification.qualify(root, output, oracle_command())
    assert receipt["gold_passed"] is True
    assert receipt["mutation_killed"] is True
    assert receipt["binding"]["command"] == oracle_command()
    assert receipt["scientific_claim"] == "oracle_rehearsal_only"
    assert len(receipt["receipt_sha256"]) == 64
    assert output.is_file()
    assert (root / qualification.COMPONENT).read_bytes() == original


def test_missing_strengthened_assertion_fails_before_execution(tmp_path, monkeypatch):
    root = checkout(tmp_path, monkeypatch)
    (root / qualification.ORACLE).write_text("partial", encoding="utf-8")
    with pytest.raises(ValueError, match="strengthened oracle"):
        qualification.qualify(root, tmp_path / "receipt.json", oracle_command())


def test_gold_infrastructure_failure_cannot_count_as_mutant_kill(tmp_path, monkeypatch):
    root = checkout(tmp_path, monkeypatch)
    receipt = qualification.qualify(
        root, tmp_path / "receipt.json", [sys.executable, "-c", "raise SystemExit(1)"])
    assert receipt["gold_passed"] is False
    assert receipt["mutant"] is None
    assert receipt["mutation_killed"] is False


def test_wrong_revision_fails_closed(tmp_path, monkeypatch):
    root = checkout(tmp_path, monkeypatch)
    monkeypatch.setattr(qualification, "_git", lambda *_: "0" * 40)
    with pytest.raises(ValueError, match="checkout must be detached"):
        qualification.qualify(root, tmp_path / "receipt.json", oracle_command())


def test_cli_requires_a_command(tmp_path):
    run = subprocess.run(
        [sys.executable, "-m", "eval.todomvc_escape_qualification",
         "--checkout", str(tmp_path), "--output", str(tmp_path / "receipt.json")],
        capture_output=True, text=True)
    assert run.returncode == 2
    assert "oracle command is required" in run.stderr


def test_ci_rebuilds_both_gold_and_mutant_before_browser_oracle():
    workflow = (
        Path(__file__).parents[1]
        / ".github"
        / "workflows"
        / "todomvc-oracle-qualification.yml"
    ).read_text(encoding="utf-8")
    command = workflow.split(
        "name: Qualify gold and mutant with the same build and browser oracle", 1
    )[1]
    assert "npm --prefix examples/vue run build &&" in command
    assert command.index("run build &&") < command.index("start-server-and-test")
    assert "persist-credentials: false" in workflow


@pytest.mark.parametrize('mutant_exit', [-15, 1, 127])
def test_non_oracle_mutant_failure_cannot_count_as_kill(tmp_path, monkeypatch, mutant_exit):
    root = checkout(tmp_path, monkeypatch)
    code = (
        "from pathlib import Path; import os, signal; "
        "gold='cancelEdit' in Path('examples/vue/src/components/TodoItem.vue').read_text(); "
        "Path('todomvc-qualification-junit.xml').write_text("
        "'<testsuites><testsuite><testcase name=\"TodoMVC - vue Editing should cancel edits on escape\"/>'"
        "'</testsuite></testsuites>') if gold else None; "
        f"os.kill(os.getpid(), 15) if not gold and {mutant_exit} < 0 else None; "
        f"raise SystemExit(0 if gold else {mutant_exit})"
    )
    receipt = qualification.qualify(root, tmp_path / 'receipt.json', [sys.executable, '-c', code])
    assert receipt['gold_passed'] is True
    assert receipt['mutation_killed'] is False
    assert qualification.GOLD_BINDING in (root / qualification.COMPONENT).read_text()


@pytest.mark.parametrize("report,exit_code", [
    ("not XML", 1),
    (junit(), 1),
    (junit(EXPECTED_FAILURE, name="unrelated test"), 1),
    (junit("server unavailable", failure_type="Error"), 1),
    (junit("expected '.edit' to exist"), 1),
    (junit(EXPECTED_FAILURE, extra=True), 1),
    (junit(EXPECTED_FAILURE), 127),
    (junit(EXPECTED_FAILURE), 0),
])
def test_only_expected_escape_failure_with_same_test_inventory_qualifies(
        tmp_path, monkeypatch, report, exit_code):
    root = checkout(tmp_path, monkeypatch)
    receipt = qualification.qualify(root, tmp_path / "receipt.json",
                                    oracle_command(report, mutant_exit=exit_code))
    assert receipt["gold_passed"] is True
    assert receipt["mutation_killed"] is False
    assert qualification.GOLD_BINDING in (root / qualification.COMPONENT).read_text()


@pytest.mark.parametrize("report", ["not XML", "<testsuites/>",
                                     junit(name="another test"), junit(EXPECTED_FAILURE)])
def test_zero_exit_without_passing_escape_evidence_blocks_mutation(tmp_path, monkeypatch, report):
    root = checkout(tmp_path, monkeypatch)
    receipt = qualification.qualify(root, tmp_path / "receipt.json",
                                    oracle_command(gold_report=report))
    assert receipt["gold_passed"] is False
    assert receipt["mutation_killed"] is False
    assert receipt["mutant"] is None


def test_preserves_auditable_fresh_reports_and_logs_for_both_arms(tmp_path, monkeypatch):
    root = checkout(tmp_path, monkeypatch)
    output = tmp_path / "receipt.json"
    receipt = qualification.qualify(root, output, oracle_command())
    assert receipt["schema_version"] == "repository-e2e-qualification/v2"
    for arm in ("gold", "mutant"):
        evidence = output.parent / receipt["evidence_directory"] / arm
        for filename, key in [("junit.xml", "junit_sha256"),
                              ("stdout.log", "stdout_sha256"), ("stderr.log", "stderr_sha256")]:
            assert hashlib.sha256((evidence / filename).read_bytes()).hexdigest() == receipt[arm][key]
    assert receipt["gold"]["junit_sha256"] != receipt["mutant"]["junit_sha256"]
    assert not (root / qualification.JUNIT_REPORT).exists()


def test_existing_report_is_rejected_without_overwriting(tmp_path, monkeypatch):
    root = checkout(tmp_path, monkeypatch)
    report = root / qualification.JUNIT_REPORT
    report.write_text(junit(EXPECTED_FAILURE))
    with pytest.raises(ValueError, match="report path must not already exist"):
        qualification.qualify(root, tmp_path / "receipt.json", oracle_command())
    assert report.read_text() == junit(EXPECTED_FAILURE)


def test_restores_component_when_mutant_run_is_interrupted(tmp_path, monkeypatch):
    root = checkout(tmp_path, monkeypatch)
    original = (root / qualification.COMPONENT).read_bytes()
    original_run = qualification._run

    def terminate_mutant(command, checkout, evidence):
        if qualification.MUTANT_BINDING in (checkout / qualification.COMPONENT).read_text():
            signal.raise_signal(signal.SIGTERM)
        return original_run(command, checkout, evidence)

    monkeypatch.setattr(qualification, "_run", terminate_mutant)
    with pytest.raises(KeyboardInterrupt, match="terminated"):
        qualification.qualify(root, tmp_path / "receipt.json", oracle_command())
    assert (root / qualification.COMPONENT).read_bytes() == original
    assert not (tmp_path / "receipt.json").exists()
