import json
from pathlib import Path

import pytest

from scripts import context_cue_panel as panel
from scripts import selected46_report as rep


def test_omitted_span_is_the_removed_text():
    assert panel.omitted_span("Do X. Never do Y. Do Z.", "Do X. Do Z.") == "Never do Y."
    with pytest.raises(ValueError):
        panel.omitted_span("abc", "xyz")


def test_yes_requires_a_literal_quote():
    text = "Requirement:\nOnly active   projects are listed."
    assert panel.parse_vote('{"context_cue": "yes", "quote": "Only active projects"}', text)["context_cue"] == "yes"
    with pytest.raises(ValueError):
        panel.parse_vote('{"context_cue": "yes", "quote": "archived projects are hidden"}', text)
    assert panel.parse_vote('{"context_cue": "no", "quote": null}', text)["context_cue"] == "no"


def test_every_selected_case_yields_a_blind_prompt():
    items = panel.selected_cases()
    assert len(items) == 46
    for item in items:
        prompt = panel.item_prompt(item["omitted"], item["text"])
        assert item["omitted"] and item["omitted"] not in item["text"]
        for word in ("target_only_failure", "gpt-5.6", "memorized", "oracle"):
            assert word not in prompt


class FakeProvider:
    def __init__(self, model, evidence):
        self.model = model

    def complete(self, request):
        text = request.prompt.split("<<<\n", 1)[1].rsplit("\n>>>", 1)[0]
        for quote in ("active projects only", "(at least one)"):
            if quote in text:  # the two authored "yes" controls
                return json.dumps({"context_cue": "yes", "quote": quote})
        return json.dumps({"context_cue": "no", "quote": None})


def test_run_with_fake_panel_and_report_integration(tmp_path):
    out = tmp_path / "packet"
    panel.prepare(out, ["m1", "m2"], "m3", Path("/bin/true"))
    summary = panel.run(out, provider_factory=FakeProvider)
    assert summary["cases"] == 46 and summary["routes"] == {"agreement": 46}
    cues = rep.load_context_cue(out / "results.json")
    assert len(cues) == 46 and set(cues.values()) == {0}
    with pytest.raises(FileExistsError):
        panel.run(out, provider_factory=FakeProvider)
