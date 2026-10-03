from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from scripts import abc_case

# Only migrated configs have a legacy collector to compare with; new selection
# cases are covered by tests/test_selection_cases.py.
CASES = sorted(p.stem for p in abc_case.CASES_DIR.glob("*.json")
               if "migrated_from" in json.loads(p.read_text()))


@pytest.mark.parametrize("name", CASES)
def test_generic_case_reproduces_the_legacy_collector(name: str) -> None:
    case = abc_case.Case.load(name)
    legacy = importlib.import_module(case.config["migrated_from"])
    for arm in abc_case.ARMS:
        assert case.prompt(arm) == legacy.prompt(arm)
    behavior = "app.noop && app.noop();"
    page = (case.fixture / "page.html").read_text()
    good = page.replace(case.marker, behavior)
    assert case.admit(good) == legacy.admit(good)
    for bad in ("<html></html>", page.replace(case.marker, ""), page.replace(case.marker, "</script>")):
        with pytest.raises(ValueError):
            case.admit(bad)
        with pytest.raises(ValueError):
            legacy.admit(bad)
    assert len(case.schedule()) == 18


def test_prepare_and_run_with_fakes(tmp_path: Path) -> None:
    case = abc_case.Case.load("openproject-invalid-remaining")
    page = (case.fixture / "page.html").read_text()

    class Provider:
        def __init__(self, model, evidence):
            pass

        def complete(self, request):
            if "cannot be saved" in request.prompt:
                return page.replace(case.marker, "app.onSave(v=>{if(+v.remaining>+v.work)return;app.persist(v)});")
            return page.replace(case.marker, "app.onSave(v=>app.persist(v));")

    def executor(inputs: Path, output: Path) -> dict:
        lost = "return;" not in (inputs / "app.html").read_text()
        return {"category": "target_only_failure" if lost else "pass"}

    packet = tmp_path / "packet"
    assert abc_case.prepare(case, packet, Path("/bin/sh")) == {"case": case.name, "planned_slots": 18}
    result = abc_case.run(packet, provider_factory=Provider, executor=executor)
    for model in case.config["models"]:
        assert result["counts"][model]["C"] == {"target_only_failure": 3}
        assert result["counts"][model]["A"] == {"pass": 3}
    with pytest.raises(FileExistsError):
        abc_case.run(packet, provider_factory=Provider, executor=executor)


def test_a_config_missing_fields_or_arms_is_rejected(tmp_path: Path) -> None:
    config = json.loads((abc_case.CASES_DIR / "openproject-invalid-remaining.json").read_text())
    with pytest.raises(ValueError):
        abc_case.Case({k: v for k, v in config.items() if k != "seed"})
    with pytest.raises(ValueError):
        abc_case.Case({**config, "arms": {"A": "x", "C": "y"}})
