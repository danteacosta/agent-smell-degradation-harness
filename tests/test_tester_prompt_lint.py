import pytest

from eval.tester_prompt_lint import lint_tester_prompt, lint_tester_prompts

IMPL = """function closeTask(task) {
  task.subtasks.forEach(s => { s.status = 'done'; });
  return task;
}
"""


def test_requirement_only_prompt_is_not_coupled():
    out = lint_tester_prompt("When a task is closed, pending subtasks become done.", [IMPL])
    assert out["coupled"] is False and out["findings"] == []


def test_verbatim_implementation_line_is_flagged_despite_whitespace():
    prompt = "Write tests.\ntask.subtasks.forEach(s =>   { s.status = 'done'; });\n"
    out = lint_tester_prompt(prompt, [IMPL])
    assert out["coupled"] is True
    assert "verbatim_implementation_line" in out["findings"]


def test_short_or_punctuation_lines_do_not_match():
    out = lint_tester_prompt("return task;\n}\n", [IMPL])
    assert out["coupled"] is False


def test_fenced_block_is_reported_but_not_coupled():
    out = lint_tester_prompt("Spec:\n```\nGiven a task\n```\n", [IMPL])
    assert out["coupled"] is False
    assert out["findings"] == ["fenced_code_block"] and out["fenced_block_count"] == 1


def test_batch_rejects_duplicate_and_missing_ids():
    with pytest.raises(ValueError):
        lint_tester_prompts([{"prompt_id": "a", "prompt": "x"}, {"prompt_id": "a", "prompt": "y"}])
    with pytest.raises(ValueError):
        lint_tester_prompts([{"prompt": "x"}])


def test_batch_lists_coupled_ids():
    out = lint_tester_prompts(
        [
            {"prompt_id": "clean", "prompt": "requirement text", "implementation_sources": [IMPL]},
            {"prompt_id": "dirty", "prompt": IMPL, "implementation_sources": [IMPL]},
        ]
    )
    assert out["coupled_prompt_ids"] == ["dirty"] and out["any_coupled"] is True
