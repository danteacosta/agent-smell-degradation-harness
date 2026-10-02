from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import llm_screening_panel as panel

ADMIT = {"decision": "admit", "reason": "admit", "target_rule": "R", "pass_observation": "P",
         "fail_observation": "F", "numeric": False, "derived_state": True, "probe_question": "Q?"}
EXCLUDE = {"decision": "exclude", "reason": "operations_or_configuration", "target_rule": None,
           "pass_observation": None, "fail_observation": None, "numeric": False,
           "derived_state": False, "probe_question": None}


class _Provider:
    """Admits candidates whose text mentions 'automatically' or 'cannot', except model 'contrary'."""

    def __init__(self, model: str, evidence: Path) -> None:
        self.model = model

    def complete(self, request) -> str:
        text = request.prompt.split("Candidate:", 1)[1]
        admit = any(w in text for w in ("automatically", "cannot", "moves it", "Done"))
        if "admin/requirements" in text or "--album" in text or "**Save**" in text:
            admit = False
        if self.model == "contrary" and "Project: alpha" in text:
            admit = not admit
        return "```json\n" + json.dumps(ADMIT if admit else EXCLUDE) + "\n```"


@pytest.fixture()
def screening(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    data = {"candidates": [
        {"candidate_id": "rc-a", "project": "alpha", "file": "docs/a.md", "removed": [],
         "added": ["Closed tasks are automatically archived."], "suggestion": "admit"},
        {"candidate_id": "rc-b", "project": "beta", "file": "docs/b.md", "removed": ["Old."],
         "added": ["Requires Redis 7."], "suggestion": "exclude"},
        {"candidate_id": "rc-f7aa63a16f88", "project": "paperless", "file": "docs/usage.md", "removed": [],
         "added": ["Suggestions are requested automatically for inbox documents."], "suggestion": "exclude"},
    ]}
    path = tmp_path / "screening.json"
    path.write_text(json.dumps(data))
    monkeypatch.setattr(panel, "SCREENING", path)
    return path


def test_prompts_are_blind_to_the_pre_screen(tmp_path: Path, screening: Path) -> None:
    out = tmp_path / "run"
    panel.prepare(out, ["m1", "m2"], "m3", Path("/bin/sh"))
    for prompt in (out / "frozen/prompts").iterdir():
        text = prompt.read_text()
        assert "suggestion" not in text and "pilot" not in text.lower()
    manifest = json.loads((out / "frozen/manifest.json").read_text())
    assert all("suggestion" not in c for c in manifest["candidates"])


def test_consensus_tiebreak_and_mechanical_pilot_exclusion(tmp_path: Path, screening: Path) -> None:
    out = tmp_path / "run"
    panel.prepare(out, ["m1", "contrary"], "m3", Path("/bin/sh"))
    summary = panel.run(out, provider_factory=_Provider)
    rows = {r["candidate_id"]: r for r in json.loads((out / "results.json").read_text())["rows"]}
    assert rows["rc-a"]["route"] == "tiebreaker" and rows["rc-a"]["consensus"] == "admit"
    assert rows["rc-a"]["derived_state"] is True and rows["rc-a"]["probe_question"] == "Q?"
    assert rows["rc-b"]["consensus"] == "exclude" and rows["rc-b"]["route"] == "agreement"
    assert rows["rc-f7aa63a16f88"]["consensus"] == "exclude"
    assert rows["rc-f7aa63a16f88"]["route"] == "pilot_case_mechanical"
    assert summary["admitted_by_project"] == {"alpha": 1}
    with pytest.raises(FileExistsError):
        panel.run(out, provider_factory=_Provider)


def test_failed_controls_stop_before_any_candidate(tmp_path: Path, screening: Path) -> None:
    class AlwaysAdmit(_Provider):
        def complete(self, request) -> str:
            return json.dumps(ADMIT)

    out = tmp_path / "run"
    panel.prepare(out, ["m1", "m2"], "m3", Path("/bin/sh"))
    result = panel.run(out, provider_factory=AlwaysAdmit)
    assert result["status"] == "stopped_controls_failed"
    assert not (out / "calls" / "m1" / "rc-a").exists()


def test_parse_vote_rejects_inconsistent_answers() -> None:
    assert panel.parse_vote(json.dumps(ADMIT))["decision"] == "admit"
    for bad in ({**ADMIT, "reason": "no_rule_change"}, {**ADMIT, "probe_question": ""},
                {**EXCLUDE, "decision": "maybe"}):
        with pytest.raises(ValueError):
            panel.parse_vote(json.dumps(bad))
    with pytest.raises(ValueError):
        panel.parse_vote("no json here")


def test_kappa() -> None:
    assert panel.cohen_kappa(["a", "b", "a", "b"], ["a", "b", "a", "b"]) == 1.0
    assert panel.cohen_kappa([], []) is None


def test_unqualified_tiebreaker_stops_before_candidates(tmp_path: Path, screening: Path) -> None:
    class UnqualifiedTiebreaker(_Provider):
        def complete(self, request) -> str:
            if self.model == "m3":
                return json.dumps(ADMIT)
            return super().complete(request)

    out = tmp_path / "run"
    panel.prepare(out, ["m1", "m2"], "m3", Path("/bin/sh"))
    result = panel.run(out, provider_factory=UnqualifiedTiebreaker)
    assert result["status"] == "stopped_controls_failed"
    assert not (out / "calls" / "m1" / "rc-a").exists()
    controls = json.loads((out / "controls.json").read_text())
    assert all(set(row["decisions"]) == {"m1", "m2", "m3"} for row in controls["rows"])
