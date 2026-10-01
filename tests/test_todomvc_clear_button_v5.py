"""Browser-observable report contract for the revised Clear completed pilot."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "todomvc_clear_button_v5_qualify",
    ROOT / "eval/fixtures/todomvc-clear-button-v5/qualify.py",
)
qualifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualifier)


def report():
    return {"schema_version": "todomvc-clear-button-browser/v5", "status": "complete",
            "app_sha256": "0" * 64,
            "assertions": {key: True for key in qualifier.TARGET | qualifier.NON_TARGET},
            "console_errors": [], "screenshots": qualifier.SCREENSHOTS}


def test_initial_and_empty_list_visibility_are_target_observations():
    observed = report()
    assert qualifier.classify(observed) == "pass"
    observed["assertions"]["empty_list_button_hidden_4"] = False
    assert qualifier.classify(observed) == "target_only_failure"
    observed["assertions"]["only_active_id_1"] = False
    assert qualifier.classify(observed) == "mixed_failure"


def test_missing_observation_cannot_be_classified_as_a_pass():
    observed = report()
    observed["assertions"].pop("initial_button_visible_1")
    assert qualifier.classify(observed) == "malformed_report"
