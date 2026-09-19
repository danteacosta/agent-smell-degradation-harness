from pathlib import Path
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


def oracle_command() -> list[str]:
    code = (
        "from pathlib import Path; "
        "text=Path('examples/vue/src/components/TodoItem.vue').read_text(); "
        "raise SystemExit(0 if 'cancelEdit' in text else 1)"
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
    calls = []

    def fail(_command, _checkout):
        calls.append("gold")
        return {"returncode": 1, "stdout_sha256": "a" * 64,
                "stderr_sha256": "b" * 64}

    monkeypatch.setattr(qualification, "_run", fail)
    receipt = qualification.qualify(
        root, tmp_path / "receipt.json", ["unavailable-browser"])
    assert calls == ["gold"]
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
