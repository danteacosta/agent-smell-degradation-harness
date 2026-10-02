from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import test_anchor_experiment as ta

SCAFFOLD = "<html><body><script>\n/* MODEL_BEHAVIOR */\n</script></body></html>\n"
ARMS = {"A": "Save values. Reject Remaining greater than Work.",
        "B": "Persist values; refuse Remaining above Work.", "C": "Save values."}


def _prompt(arm: str) -> str:
    return "Implement only the requirement.\n\nRequirement:\n" + ARMS[arm] + "\n\nFrozen page:\n" + SCAFFOLD


def _packet(root: Path, case: str, outcomes: dict[str, str]) -> Path:
    packet = root / case
    schedule, rows = [], []
    for index, (arm, category) in enumerate(outcomes.items()):
        arm_letter = arm[0]
        slot = f"{case}-{index}"
        schedule.append({"slot_id": slot, "arm": arm_letter})
        rows.append({"slot_id": slot, "arm": arm_letter, "model": "m", "replication": index,
                     "category": category})
        (packet / "frozen/requests").mkdir(parents=True, exist_ok=True)
        (packet / "frozen/requests" / f"{slot}.json").write_text(json.dumps({"prompt": _prompt(arm_letter)}))
        (packet / "artifacts" / slot).mkdir(parents=True)
        (packet / "artifacts" / slot / "app.html").write_text(SCAFFOLD.replace("/* MODEL_BEHAVIOR */", f"// {arm}"))
    (packet / "frozen/manifest.json").write_text(json.dumps({"schedule": schedule}))
    (packet / "results.json").write_text(json.dumps({"rows": rows}))
    return packet


class _Provider:
    def __init__(self, evidence: Path) -> None:
        self.evidence = evidence

    def complete(self, request) -> str:
        prompt = request.prompt if hasattr(request, "prompt") else request.args[0]
        if "Reject Remaining" in prompt:
            return "```js\nmodule.exports = { tests: [{ name: 'rejects', run: async () => {} }] };\n```"
        return "Here are two blocks\n```js\nmodule.exports={tests:[]}\n```\n```js\n1\n```"


def _executor(artifact: Path, suite: Path, output: Path) -> dict:
    # A spec-anchored suite alarms exactly on artifacts whose behavior lost the rule.
    lost = "// C" in artifact.read_text()
    return {"status": "complete",
            "tests": [{"name": "t", "outcome": "assertion_failure" if lost else "pass"}]}


@pytest.fixture()
def packets(tmp_path: Path) -> dict[str, Path]:
    return {
        "alpha": _packet(tmp_path / "packets", "alpha", {"A1": "pass", "C1": "target_only_failure", "C2": "pass"}),
        "beta": _packet(tmp_path / "packets", "beta", {"A1": "pass", "C1": "target_only_failure",
                                                       "B1": "pass", "C2": "browser_error"}),
    }


def test_split_prompt_recovers_requirement_and_scaffold() -> None:
    requirement, page = ta.split_prompt(_prompt("C"))
    assert requirement == ARMS["C"] and page == SCAFFOLD
    with pytest.raises(ValueError):
        ta.split_prompt("no sections")


def test_read_packet_keeps_only_oracle_labelled_a_and_c(packets: dict[str, Path]) -> None:
    case = ta.read_packet("beta", packets["beta"])
    assert {a["arm"] for a in case["artifacts"]} == {"A", "C"}
    assert [a["oracle_category"] for a in case["artifacts"]] == ["pass", "target_only_failure"]
    assert case["requirements"] == ARMS


def test_prompts_never_reveal_the_oracle_and_differ_only_in_inputs(packets: dict[str, Path]) -> None:
    cases = [ta.read_packet(name, path) for name, path in sorted(packets.items())]
    calls = ta.plan(cases)
    for call in calls:
        assert "target_only_failure" not in call["prompt"] and "oracle" not in call["prompt"].lower()
        assert call["prompt"].startswith(ta.INSTRUCTIONS)
    request_for_c = [c for c in calls if c["strategy"] == "code_request" and c["for_slot"] == "alpha-1"][0]
    assert ARMS["C"] in request_for_c["prompt"] and ARMS["A"] not in request_for_c["prompt"]
    spec_only = [c for c in calls if c["strategy"] == "spec_only" and c["case"] == "alpha"]
    assert len(spec_only) == ta.SPEC_ONLY_SUITES
    assert "// C" not in spec_only[0]["prompt"] and ARMS["A"] in spec_only[0]["prompt"]
    assert set(spec_only[0]["targets"]) == {"alpha-0", "alpha-1", "alpha-2"}


def test_extract_suite_is_strict() -> None:
    assert "module.exports" in ta.extract_suite("x\n```js\nmodule.exports = {tests: []};\n```")
    for bad in ("no block", "```js\nconst a = 1;\n```", "```js\nmodule.exports = require('fs');\n```",
                "```js\nmodule.exports={}\n```\n```js\nx\n```"):
        with pytest.raises(ValueError):
            ta.extract_suite(bad)


def test_end_to_end_with_fake_provider_and_executor(tmp_path: Path, packets: dict[str, Path]) -> None:
    out = tmp_path / "run"
    plan = ta.prepare(out, packets, "fake-model", Path("/bin/sh"))
    assert plan["calls"] == 2 * 5 + 2 * ta.SPEC_ONLY_SUITES
    status = ta.generate(out, provider_factory=_Provider)
    # Prompts carrying the complete rule yield a suite; C requests yield an invalid response.
    assert status == {"suite_ready": 2 + 5 + 2 * ta.SPEC_ONLY_SUITES, "suite_invalid": 3}
    summary = ta.execute(out, executor=_executor)
    spec = summary["spec_only"]
    assert spec["detection_itt"] == 1.0
    assert spec["false_alarm_itt"] == pytest.approx(1 / 3)  # the passing C artifact in alpha
    code_request = summary["code_request"]
    assert code_request["detection_itt"] == 0.0  # invalid suites count as no detection
    assert code_request["detection_usable_only"] is None
    with pytest.raises(FileExistsError):
        ta.generate(out, provider_factory=_Provider)
    receipt = json.loads((out / "receipt.json").read_text())["files"]
    assert "results.json" in receipt


def test_frozen_drift_is_rejected(tmp_path: Path, packets: dict[str, Path]) -> None:
    out = tmp_path / "run"
    ta.prepare(out, packets, "fake-model", Path("/bin/sh"))
    prompt = next((out / "frozen/prompts").iterdir())
    prompt.write_text(prompt.read_text() + "tampered")
    with pytest.raises(ValueError, match="drift"):
        ta.generate(out, provider_factory=_Provider)


def test_classify() -> None:
    assert ta.classify({"status": "suite_invalid"}) == "suite_invalid"
    assert ta.classify({"status": "runner_error"}) == "runner_error"
    assert ta.classify({"status": "complete", "tests": [{"outcome": "pass"}]}) == "quiet"
    assert ta.classify({"status": "complete", "tests": [{"outcome": "error"}]}) == "error_alarm"
    assert ta.classify({"status": "complete", "tests": [{"outcome": "error"},
                                                        {"outcome": "assertion_failure"}]}) == "assertion_alarm"


def test_controls_compare_observed_with_expected(tmp_path: Path) -> None:
    def fake(artifact: Path, suite: Path, output: Path) -> dict:
        text = artifact.read_text()
        outcome = "pass" if "cannot exceed" in text else "assertion_failure"
        return {"status": "complete", "tests": [{"name": "t", "outcome": outcome}]}

    result = ta.run_controls(tmp_path / "controls", executor=fake)
    assert result["qualified"] is True
    assert "lost_rule" in result["observed"]


def test_locate_matches_public_frozen_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    public = tmp_path / "public"
    evidence = tmp_path / "evidence"
    for index, case in enumerate(ta.CASES):
        packet = evidence / f"{case}-packet"
        (packet / "frozen").mkdir(parents=True)
        (packet / "frozen/receipt.json").write_text(json.dumps({"n": index}))
        (packet / "results.json").write_text("{}")
        (public / case).mkdir(parents=True)
        (public / case / "summary.json").write_text(json.dumps(
            {"frozen_receipt_sha256": ta.sha256_file(packet / "frozen/receipt.json")}))
    decoy = evidence / "unrelated"
    (decoy / "frozen").mkdir(parents=True)
    (decoy / "frozen/receipt.json").write_text("{}")
    monkeypatch.setattr(ta, "PUBLIC_SUMMARIES", public)
    found = ta.locate(evidence)
    assert found == {case: str(evidence / f"{case}-packet") for case in ta.CASES}
    (evidence / "realworld-favorites-packet/frozen/receipt.json").write_text("changed")
    with pytest.raises(SystemExit):
        ta.locate(evidence)
