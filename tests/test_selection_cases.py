import json
from pathlib import Path
import runpy

import pytest

from scripts import build_selection_cases as build_mod
from scripts.abc_case import Case
from scripts.selection_cases import templates

ROOT = Path(build_mod.ROOT)
NAMES = [s["case"] for s in build_mod.SPECS]


def test_committed_fixtures_match_the_specs(tmp_path):
    build_mod.build(tmp_path)
    for name in NAMES:
        for rel in (f"eval/fixtures/{name}/page.html", f"eval/fixtures/{name}/runner.cjs",
                    f"eval/fixtures/{name}/qualify.py", f"data/abc-cases/{name}.json"):
            assert (tmp_path / rel).read_text() == (ROOT / rel).read_text(), rel


@pytest.mark.parametrize("name", NAMES)
def test_case_loads_and_admits_its_reference(name):
    case = Case.load(name)
    qualifier = runpy.run_path(str(ROOT / case.config["fixture"] / "qualify.py"))
    page = (case.fixture / "page.html").read_text()
    reference = page.replace(templates.MARKER, qualifier["CONTROLS"]["reference"][0])
    assert case.admit(reference) == reference.encode()
    for arm in "ABC":
        assert case.config["arms"][arm] in case.prompt(arm)
    with pytest.raises(ValueError):
        case.admit(page.replace("<main>", "<main><p>changed</p>"))


@pytest.mark.parametrize("name", NAMES)
def test_arm_c_removes_one_span_of_a(name):
    arms = json.loads((ROOT / f"data/abc-cases/{name}.json").read_text())["arms"]
    a, c = arms["A"], arms["C"]
    prefix = 0
    while prefix < len(c) and a[prefix] == c[prefix]:
        prefix += 1
    suffix = 0
    while suffix < len(c) - prefix and a[-1 - suffix] == c[-1 - suffix]:
        suffix += 1
    assert prefix + suffix == len(c), "C must equal A with one contiguous span removed"


@pytest.mark.parametrize("name", NAMES)
def test_classifier_separates_target_and_control_failures(name):
    q = runpy.run_path(str(ROOT / f"eval/fixtures/{name}/qualify.py"))
    base = {"schema_version": q["SCHEMA"], "status": "complete", "app_sha256": "0" * 64,
            "console_errors": [], "screenshots": q["SCREENSHOTS"]}
    keys = q["TARGET"] | q["NON_TARGET"]
    assert q["classify"]({**base, "assertions": {k: True for k in keys}}) == "pass"
    one_target = next(iter(q["TARGET"]))
    assert q["classify"]({**base, "assertions": {k: k != one_target for k in keys}}) == "target_only_failure"
    one_control = next(iter(q["NON_TARGET"]))
    assert q["classify"]({**base, "assertions": {k: k != one_control for k in keys}}) == "non_target_only_failure"
    assert q["classify"]({**base, "assertions": {}}) == "malformed_report"


def test_controls_cover_every_outcome_class():
    for spec in build_mod.SPECS:
        expected = {e for _, e in spec["controls"].values()}
        assert {"pass", "target_only_failure", "non_target_only_failure"} <= expected, spec["case"]


@pytest.mark.parametrize("name", NAMES)
def test_model_prompt_does_not_disclose_the_research_case_identifier(name):
    case = Case.load(name)
    for arm in "ABC":
        assert name not in case.prompt(arm), "research metadata must stay outside model-visible input"
