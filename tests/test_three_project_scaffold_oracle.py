import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "three_project_scaffold_qualify",
    ROOT / "eval/fixtures/three-project-scaffold/qualify.py",
)
assert SPEC and SPEC.loader
qualify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qualify)


def report(project: str, assertions: dict[str, bool]) -> dict:
    return {
        "schema_version": "three-project-fixed-scaffold-browser/v1",
        "project_id": project,
        "status": "complete",
        "app_sha256": "a" * 64,
        "assertions": assertions,
        "console_errors": [],
        "screenshot": "final.png",
    }


@pytest.mark.parametrize("project,contract", qualify.PROJECT_ASSERTIONS.items())
def test_classifier_separates_target_and_non_target_failures(project: str, contract: dict) -> None:
    keys = contract["target"] | contract["non_target"]
    passing = {key: True for key in keys}
    assert qualify.classify(report(project, passing)) == "pass"

    target = dict(passing)
    target[next(iter(contract["target"]))] = False
    assert qualify.classify(report(project, target)) == "target_only_failure"

    non_target = dict(passing)
    non_target[next(iter(contract["non_target"]))] = False
    assert qualify.classify(report(project, non_target)) == "non_target_only_failure"

    mixed = dict(target)
    mixed[next(iter(contract["non_target"]))] = False
    assert qualify.classify(report(project, mixed)) == "mixed_failure"


def test_classifier_fails_closed_on_schema_and_assertion_drift() -> None:
    assertions = {key: True for groups in qualify.PROJECT_ASSERTIONS["paperless-ngx"].values() for key in groups}
    malformed = report("paperless-ngx", assertions)
    malformed["extra"] = True
    assert qualify.classify(malformed) == "malformed_report"
    malformed = report("paperless-ngx", assertions)
    malformed["assertions"].pop("drop_creates_document")
    assert qualify.classify(malformed) == "malformed_report"


def test_assembly_changes_only_the_single_behavior_marker(tmp_path: Path) -> None:
    scaffold = "before\n/* MODEL_BEHAVIOR */\nafter\n"
    assembled = qualify.assemble(scaffold, "app.onSave(run);")
    assert assembled == "before\napp.onSave(run);\nafter\n"
    with pytest.raises(ValueError, match="marker mismatch"):
        qualify.assemble("no marker", "logic")


def test_docker_command_requires_an_immutable_image(tmp_path: Path) -> None:
    command = qualify.docker_command("sha256:" + "1" * 64, tmp_path, tmp_path)
    assert command[0:2] == ["docker", "run"]
    assert "--network" in command and "none" in command
    with pytest.raises(ValueError, match="immutable"):
        qualify.docker_command("latest", tmp_path, tmp_path)
