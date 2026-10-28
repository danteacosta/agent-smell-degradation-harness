"""Tests for scripts/omitted_mention_triage.py."""
from scripts import omitted_mention_triage as om


def test_words_split_camel_and_snake():
    assert om.words("remainingWork max_value 10") == ["remaining", "work", "max", "value", "10"]


def test_omitted_tokens_ignore_words_in_c_and_inflections():
    a = "Saving edits updates values. A Remaining value greater than Work cannot be saved."
    c = "Saving edits updates values."
    assert om.omitted_tokens(a, c) == ["remaining", "greater", "work", "cannot"]


def test_numbers_are_kept_and_project_names_dropped():
    assert om.omitted_tokens("Zulip allows up to 10 managers", "Zulip allows managers", "zulip") == ["10"]


def test_mentions_matches_test_names_and_code():
    toks = ["greater", "cannot"]
    src = 'test("remaining greater than work cannot be saved", async () => {})'
    assert om.mentions(src, toks) == ["greater", "cannot"]
    assert om.mentions("expect(x).toBe(1)", toks) == []


def test_public_demo_runs_on_test_anchor_suites():
    res = om.scan(om.test_anchor_manifest())
    assert res["proxy_only"] is True
    assert {r["source"] for r in res["summary"]} == {"code_request", "code_spec", "spec_only"}
