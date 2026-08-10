from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "replay-gate.yml"


def test_replay_workflow_is_no_secret_and_fork_safe() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "pull_request" in text
    assert "security-events: write" in text
    assert "if: always()" in text
    assert "upload-artifact" in text
    assert "report.json" in text and "report.sarif" in text
    assert "OPENAI_API_KEY" not in text
    assert "ANTHROPIC_API_KEY" not in text
    assert "secrets." not in text
    assert "constraint-loss" in text and "clean" in text
