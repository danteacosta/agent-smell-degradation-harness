import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "four_project_qualify", ROOT / "eval/fixtures/four-project-ui/qualify.py"
)
assert SPEC and SPEC.loader
qualify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qualify)


def report(project: str, assertions: dict) -> dict:
    return {
        "schema_version": "four-project-ui-browser/v1",
        "project_id": project,
        "status": "complete",
        "app_sha256": "a" * 64,
        "assertions": assertions,
        "console_errors": [],
        "screenshot": "final.png",
    }


def test_classify_separates_target_and_non_target_failures() -> None:
    for project, contract in qualify.PROJECT_ASSERTIONS.items():
        values = {key: True for key in contract["target"] | contract["non_target"]}
        assert qualify.classify(report(project, values)) == "pass"
        target = dict(values)
        target[next(iter(contract["target"]))] = False
        assert qualify.classify(report(project, target)) == "target_only_failure"
        non_target = dict(values)
        non_target[next(iter(contract["non_target"]))] = False
        assert qualify.classify(report(project, non_target)) == "non_target_only_failure"


def test_classify_fails_closed_on_schema_or_type_drift() -> None:
    contract = qualify.PROJECT_ASSERTIONS["nextcloud"]
    values = {key: True for key in contract["target"] | contract["non_target"]}
    malformed = report("nextcloud", values)
    malformed["assertions"]["restore_returns_to_all"] = "yes"
    assert qualify.classify(malformed) == "malformed_report"
    malformed = report("nextcloud", values)
    malformed["unexpected"] = True
    assert qualify.classify(malformed) == "malformed_report"


def test_interface_error_requires_closed_operational_shape() -> None:
    value = {
        "schema_version": "four-project-ui-browser/v1",
        "project_id": "kanboard",
        "status": "interface_error",
        "app_sha256": "b" * 64,
        "assertions": {},
        "console_errors": [],
        "error": "ambiguous task identity",
    }
    assert qualify.classify(value) == "interface_error"
    value["assertions"] = {"unrelated_task_unchanged": True}
    assert qualify.classify(value) == "malformed_report"

