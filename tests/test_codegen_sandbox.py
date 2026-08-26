from __future__ import annotations

import json
from pathlib import Path
import textwrap

import pytest

import eval.codegen_sandbox as sandbox
from eval.codegen_sandbox import evaluate


def _source(body: str) -> str:
    return textwrap.dedent(body).strip() + "\n"


def _require_execution(result: dict) -> None:
    if result["status"] == "unsafe_not_run":
        pytest.skip("the host cannot apply every required sandbox control")


def test_accepts_agent_source_with_outer_indentation() -> None:
    result = evaluate(
        "\n            def evaluate(value):\n                return value + 1\n            ",
        [{"args": [1], "expected": 2}],
    )

    assert not any(issue["code"] == "syntax_error" for issue in result["validation_errors"])
    _require_execution(result)
    assert result["status"] == "passed"


def test_runs_a_pure_function_against_literal_hidden_tests() -> None:
    result = evaluate(
        _source(
            """
            def evaluate(value):
                if value > 10:
                    return "high"
                return "low"
            """
        ),
        [
            {"args": [11], "expected": "high"},
            {"args": [2], "expected": "low"},
        ],
    )

    _require_execution(result)
    assert result["status"] == "passed"
    assert result["passed"] == 2
    assert result["failed"] == 0
    assert [case["status"] for case in result["cases"]] == ["passed", "passed"]


def test_reports_a_functional_mismatch_without_stopping_other_cases() -> None:
    result = evaluate(
        _source(
            """
            def evaluate(value):
                return value + 1
            """
        ),
        [
            {"args": [1], "expected": 2},
            {"args": [2], "expected": 99},
            {"args": [3], "expected": 4},
        ],
    )

    _require_execution(result)
    assert result["status"] == "failed"
    assert result["passed"] == 2
    assert result["failed"] == 1
    assert result["cases"][1]["status"] == "failed"
    assert result["cases"][1]["expected"] == 99
    assert result["cases"][1]["actual"] == 3


@pytest.mark.parametrize(
    ("source", "expected_code"),
    [
        (
            """
            import os

            def evaluate(value):
                return value
            """,
            "module_shape",
        ),
        (
            """
            def evaluate(value):
                return open("secret.txt")
            """,
            "disallowed_call",
        ),
        (
            """
            def evaluate(value):
                return __import__("os")
            """,
            "disallowed_name",
        ),
        (
            """
            def evaluate(value):
                return eval("value")
            """,
            "disallowed_call",
        ),
        (
            """
            def evaluate(value):
                return compile("value", "generated", "eval")
            """,
            "disallowed_call",
        ),
        (
            """
            def evaluate(value):
                return exec("value = 1")
            """,
            "disallowed_call",
        ),
        (
            """
            def evaluate(value):
                return value.network
            """,
            "disallowed_syntax",
        ),
        (
            """
            def evaluate(value):
                with value:
                    return 1
            """,
            "disallowed_syntax",
        ),
        (
            """
            def evaluate(value):
                class Secret:
                    pass
                return value
            """,
            "disallowed_syntax",
        ),
    ],
)
def test_rejects_unsafe_or_unsupported_source(source: str, expected_code: str) -> None:
    result = evaluate(source, [{"args": [1], "expected": 1}])

    assert result["status"] == "rejected"
    assert expected_code in {issue["code"] for issue in result["validation_errors"]}
    assert result["cases"] == []


def test_rejects_syntax_errors_before_starting_a_subprocess() -> None:
    result = evaluate("def evaluate(value):\n    return (", [{"args": [1], "expected": 1}])

    assert result["status"] == "rejected"
    assert any(issue["code"] == "syntax_error" for issue in result["validation_errors"])


def test_reports_runtime_errors_per_case() -> None:
    result = evaluate(
        _source(
            """
            def evaluate(value):
                return 10 / value
            """
        ),
        [{"args": [0], "expected": 0}],
    )

    _require_execution(result)
    assert result["status"] == "runtime_error"
    assert result["passed"] == 0
    assert result["failed"] == 0
    assert result["cases"][0]["status"] == "runtime_error"
    assert result["cases"][0]["exception_type"] == "ZeroDivisionError"


def test_terminates_a_long_running_function_at_the_timeout() -> None:
    result = evaluate(
        _source(
            """
            def evaluate(value):
                total = 0
                for item in range(1000000000):
                    total = total + item
                return total
            """
        ),
        [{"args": [1], "expected": 0}],
        timeout_seconds=0.15,
    )

    _require_execution(result)
    assert result["status"] == "timeout"
    assert result["timed_out"] is True
    assert result["cases"] == []


def test_rejects_non_literal_hidden_test_values() -> None:
    result = evaluate(
        _source(
            """
            def evaluate(value):
                return value
            """
        ),
        [{"args": [object()], "expected": 1}],
    )

    assert result["status"] == "rejected"
    assert any(issue["code"] == "invalid_test_literal" for issue in result["validation_errors"])


def test_returns_only_json_serializable_structured_data() -> None:
    result = evaluate(
        _source(
            """
            def evaluate(value):
                return {"value": value}
            """
        ),
        [{"args": [3], "expected": {"value": 3}}],
    )

    json.dumps(result)
    assert set(result) >= {
        "status",
        "passed",
        "failed",
        "cases",
        "safety_controls",
        "safety_errors",
        "validation_errors",
        "timed_out",
    }


def test_starts_child_with_empty_environment_and_temporary_working_directory(monkeypatch) -> None:
    captured: dict[str, object] = {}
    real_popen = sandbox.subprocess.Popen

    def capture_popen(*args, **kwargs):
        captured.update(kwargs)
        return real_popen(*args, **kwargs)

    monkeypatch.setattr(sandbox.subprocess, "Popen", capture_popen)
    result = evaluate(
        _source(
            """
            def evaluate(value):
                return value
            """
        ),
        [{"args": [3], "expected": 3}],
    )

    assert result["status"] in {"passed", "unsafe_not_run"}
    assert captured["env"] == {}
    child_cwd = Path(captured["cwd"])
    assert child_cwd.name.startswith("codegen-sandbox-")
    assert not child_cwd.exists()


def test_reports_all_required_safety_controls_before_running_code() -> None:
    result = evaluate(
        _source(
            """
            def evaluate(value):
                return value
            """
        ),
        [{"args": [3], "expected": 3}],
    )

    assert result["status"] in {"passed", "unsafe_not_run"}
    assert set(result["safety_controls"]) == {
        "cpu",
        "address_space",
        "nproc",
        "nofile",
        "output",
        "non_root",
    }
    if result["status"] == "unsafe_not_run":
        assert result["safety_errors"]
        assert result["cases"] == []
    else:
        assert all(result["safety_controls"].values())
        assert result["safety_errors"] == []


def test_propagates_unsafe_not_run_without_executing_cases(monkeypatch) -> None:
    class FakeProcess:
        returncode = 0
        pid = 12345

        def communicate(self, payload=None, timeout=None):
            return (
                json.dumps(
                    {
                        "status": "unsafe_not_run",
                        "passed": 0,
                        "failed": 0,
                        "errors": 0,
                        "cases": [],
                        "validation_errors": [],
                        "timed_out": False,
                        "safety_controls": {"cpu": False},
                        "safety_errors": [
                            {"control": "cpu", "code": "limit_unavailable"}
                        ],
                    }
                ).encode(),
                b"",
            )

        def poll(self):
            return self.returncode

    monkeypatch.setattr(sandbox.subprocess, "Popen", lambda *args, **kwargs: FakeProcess())
    result = evaluate(
        _source(
            """
            def evaluate(value):
                return value
            """
        ),
        [{"args": [3], "expected": 3}],
    )

    assert result["status"] == "unsafe_not_run"
    assert result["cases"] == []
    assert result["safety_errors"][0]["control"] == "cpu"


def test_requires_exactly_one_function_named_evaluate() -> None:
    result = evaluate(
        _source(
            """
            def helper(value):
                return value

            def evaluate(value):
                return helper(value)
            """
        ),
        [{"args": [1], "expected": 1}],
    )

    assert result["status"] == "rejected"
    assert any(issue["code"] == "module_shape" for issue in result["validation_errors"])
