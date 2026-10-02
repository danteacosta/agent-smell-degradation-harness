from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import memorization_probe as probe


def _panel(tmp_path: Path) -> Path:
    path = tmp_path / "panel.json"
    path.write_text(json.dumps({"status": "complete", "rows": [
        {"candidate_id": "rc-known", "project": "kanboard", "consensus": "admit",
         "target_rule": "Closing a task marks its open subtasks done.",
         "probe_question": "What happens to open subtasks when a task is closed?"},
        {"candidate_id": "rc-unknown", "project": "wekan", "consensus": "admit",
         "target_rule": "Duplicating a board starts a new activity history.",
         "probe_question": "What activity does a duplicated board show?"},
        {"candidate_id": "rc-out", "project": "x", "consensus": "exclude"},
    ]}))
    return path


class _Provider:
    def __init__(self, model: str, evidence: Path) -> None:
        self.model = model

    def complete(self, request) -> str:
        prompt = request.prompt
        if prompt.startswith("Decide whether"):
            rule, answer = prompt.split("Rule: ", 1)[1].split("\n\nAnswer: ", 1)
            states = "KNOWN" in answer or ("set to done" in answer and "subtasks" in rule) \
                or ("merged" in answer and "combines" in rule)
            return json.dumps({"states_rule": "yes" if states else "no"})
        return "KNOWN: open subtasks become done." if "subtasks" in prompt else "I do not know."


def test_probe_marks_memorized_rules_per_coder(tmp_path: Path) -> None:
    out = tmp_path / "run"
    plan = probe.prepare(out, _panel(tmp_path), ["coder-a"], ["judge-1", "judge-2"], Path("/bin/sh"))
    assert plan["rules"] == 2 and plan["probe_calls"] == 6
    for prompt in (out / "frozen/probes").iterdir():
        assert "activity history" not in prompt.read_text() and "marks its open" not in prompt.read_text()
    summary = probe.run(out, provider_factory=_Provider)
    rows = {r["candidate_id"]: r for r in json.loads((out / "results.json").read_text())["rows"]}
    assert rows["rc-known"]["memorized"] == 1 and rows["rc-known"]["yes"] == 3
    assert rows["rc-unknown"]["memorized"] == 0
    assert summary["memorized_by_coder"] == {"coder-a": {1: 1, 0: 1}}


def test_unqualified_judges_stop_the_probe(tmp_path: Path) -> None:
    class Yes(_Provider):
        def complete(self, request) -> str:
            return json.dumps({"states_rule": "yes"})

    out = tmp_path / "run"
    probe.prepare(out, _panel(tmp_path), ["coder-a"], ["judge-1", "judge-2"], Path("/bin/sh"))
    result = probe.run(out, provider_factory=Yes)
    assert result["status"] == "stopped_judge_controls_failed"
    assert not (out / "calls/probes").exists()


def test_a_question_that_states_the_rule_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "panel.json"
    path.write_text(json.dumps({"status": "complete", "rows": [
        {"candidate_id": "rc-leak", "project": "p", "consensus": "admit", "target_rule": "Saving is blocked",
         "probe_question": "Is it true that saving is blocked?"}]}))
    with pytest.raises(ValueError, match="contains the rule"):
        probe.prepare(tmp_path / "run", path, ["c"], ["j1", "j2"], Path("/bin/sh"))
