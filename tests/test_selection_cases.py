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


def test_mp2t_snapshot_preserves_ts_in_all_arms():
    import re
    spec = next(s for s in build_mod.SPECS if s['case'] == 'immich-m2t-upload')
    for arm in ('A', 'B', 'C'):
        extensions = set(re.findall(r'\.[a-z0-9]+', spec['arms'][arm]))
        assert '.ts' in extensions, arm
        assert ('.m2t' in extensions) == (arm != 'C')


@pytest.mark.parametrize('spec', build_mod.SPECS[10:], ids=lambda s: s['case'])
def test_new_case_source_matches_frame_end_snapshot(spec):
    snapshots = json.loads((ROOT / 'data/requirement-selection/current-doc-check.json').read_text())['snapshots']
    assert snapshots[spec['project_id']].startswith(spec['source']['snapshot'])


def test_selection_cases_cover_exactly_the_frozen_selected_candidates():
    selection = json.loads((ROOT / 'data/requirement-selection/selection.json').read_text())
    selected = {row['candidate_id'] for rows in selection['selected'].values() for row in rows}
    cases = [spec['candidate_id'] for spec in build_mod.SPECS]
    assert len(cases) == len(set(cases))
    assert set(cases) == selected


def test_group_permission_basis_invites_a_user_instead_of_a_group():
    spec = next(s for s in build_mod.SPECS if s['case'] == 'openproject-invite-permission-basis')
    fixture = next(f for f in spec['fixtures'] if f['second']['kind'] == 'group')
    principal = next(p for p in fixture['state']['principals'] if p['id'] == fixture['second']['id'])
    assert principal['kind'] == 'user'
