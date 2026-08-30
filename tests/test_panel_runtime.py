from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from label_plane.llm_panel import build_panel_tasks
from label_plane.control_matrix import CONTROL_CONDITIONS
from label_plane.panel_runtime import (
    AdapterResponse,
    AnthropicMessagesAdapter,
    OpenAICompatibleAdapter,
    PanelAdapterError,
    PanelConfigurationError,
    PanelRunConfig,
    PanelRunner,
    _estimate_cost,
    _normalize_usage,
)


def _tasks(judges: tuple[str, ...] = ("judge-a", "judge-b", "judge-c")) -> list[dict[str, object]]:
    return build_panel_tasks(
        [
            {
                "candidate_id": "opaque-1",
                "requirement_text": "The system shall process the request.",
                "target_family": "polysemy",
            },
            {
                "candidate_id": "opaque-2",
                "requirement_text": "The system shall process it.",
                "target_family": "vague_pronoun",
            },
        ],
        judge_ids=judges,
    )


def _config(
    *, max_retries: int = 0, judge_ids: tuple[str, ...] = ("judge-a", "judge-b", "judge-c")
) -> PanelRunConfig:
    return PanelRunConfig.from_mapping(
        {
            "schema_version": "requirements-smell-panel-runtime/v1",
            "judges": [
                {"judge_id": judge_id, "adapter": "fake", "model": f"model-{judge_id}"}
                for judge_id in judge_ids
            ],
            "consensus_required": min(2, len(judge_ids)),
            "max_retries": max_retries,
            "retry_backoff_seconds": 0,
        }
    )


def _uniform_tasks(
    count: int, judges: tuple[str, ...] = ("judge-a", "judge-b")
) -> list[dict[str, object]]:
    return build_panel_tasks(
        [
            {
                "candidate_id": f"uniform-{index}",
                "requirement_text": f"The system shall process request {index}.",
                "target_family": "polysemy",
            }
            for index in range(count)
        ],
        judge_ids=judges,
    )


class FakeAdapter:
    name = "fake"

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def complete(self, *, prompt: str, judge: object) -> AdapterResponse:
        self.calls.append((str(getattr(judge, "judge_id")), prompt))
        return AdapterResponse(
            text=json.dumps(
                {
                    "label": "clean",
                    "target_family": "polysemy",
                    "evidence_span": "",
                    "rationale": "The requirement names the object directly.",
                    "confidence": 0.8,
                }
            ),
            usage={"input_tokens": 10, "output_tokens": 8, "total_tokens": 18},
        )


class RetryOnceAdapter(FakeAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.failed = False

    def complete(self, *, prompt: str, judge: object) -> AdapterResponse:
        if not self.failed:
            self.failed = True
            raise PanelAdapterError("temporary failure", retryable=True)
        return super().complete(prompt=prompt, judge=judge)


class MeteredErrorAdapter(FakeAdapter):
    def complete(self, *, prompt: str, judge: object) -> AdapterResponse:
        self.calls.append((str(getattr(judge, "judge_id")), prompt))
        raise PanelAdapterError(
            "provider returned no final text",
            usage={"input_tokens": 10, "output_tokens": 8, "total_tokens": 18},
        )


class _HttpResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self) -> "_HttpResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class PanelRuntimeTests(unittest.TestCase):
    def test_normalizes_nested_provider_usage_for_input_cache_output_and_reasoning(self) -> None:
        usage = _normalize_usage(
            {
                "prompt_tokens": 100,
                "prompt_tokens_details": {"cached_tokens": 40},
                "completion_tokens": 30,
                "completion_tokens_details": {"reasoning_tokens": 12},
                "total_tokens": 130,
            }
        )

        self.assertEqual(usage["input_tokens"], 100)
        self.assertEqual(usage["cached_tokens"], 40)
        self.assertEqual(usage["output_tokens"], 30)
        self.assertEqual(usage["reasoning_tokens"], 12)
        self.assertEqual(usage["total_tokens"], 130)

    def test_estimates_split_cache_cost_when_provider_rates_are_declared(self) -> None:
        cost = _estimate_cost(
            {"input_tokens": 100, "cached_tokens": 40, "output_tokens": 30},
            input_usd_per_1k=1.0,
            cached_input_usd_per_1k=0.1,
            output_usd_per_1k=2.0,
        )

        self.assertEqual(cost, 0.124)

    def test_smoke_limit_routes_arbitrary_judges_and_writes_auditable_records(self) -> None:
        adapter = FakeAdapter()
        config = _config()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            responses = root / "responses.jsonl"
            errors = root / "errors.jsonl"
            manifest_path = root / "manifest.json"

            manifest = PanelRunner(config, adapters={"fake": adapter}).run(
                _tasks(),
                run_id="panel-smoke-1",
                limit_per_judge=1,
                responses_path=responses,
                errors_path=errors,
                manifest_path=manifest_path,
            )

            self.assertEqual(manifest["status"], "completed_with_smoke_limit")
            self.assertEqual(manifest["selected_task_count"], 3)
            self.assertEqual(manifest["ok_count"], 3)
            self.assertEqual(len(adapter.calls), 3)
            self.assertEqual(errors.read_text(encoding="utf-8"), "")
            records = [json.loads(line) for line in responses.read_text(encoding="utf-8").splitlines()]
            self.assertEqual({row["provider_id"] for row in records}, {"judge-a", "judge-b", "judge-c"})
            self.assertTrue(all(len(row["prompt_sha256"]) == 64 for row in records))
            self.assertTrue(all(len(row["request_sha256"]) == 64 for row in records))
            self.assertTrue(all(len(row["response_sha256"]) == 64 for row in records))
            self.assertEqual(records[0]["usage"]["total_tokens"], 18)
            self.assertEqual(manifest["cost"], {"status": "not_configured", "total_usd": None})
            self.assertNotIn("PRIVATE", manifest_path.read_text(encoding="utf-8"))

    def test_declared_pricing_is_calculated_from_reported_token_usage(self) -> None:
        config = PanelRunConfig.from_mapping(
            {
                "schema_version": "requirements-smell-panel-runtime/v1",
                "judges": [
                    {
                        "judge_id": "judge-a",
                        "adapter": "fake",
                        "model": "model-a",
                        "model_snapshot": "model-a@2026-08-27",
                    },
                    {
                        "judge_id": "judge-b",
                        "adapter": "fake",
                        "model": "model-b",
                        "model_snapshot": "model-b@2026-08-27",
                    },
                ],
                "consensus_required": 2,
                "pricing": {"input_usd_per_1k": 1.0, "output_usd_per_1k": 2.0},
            }
        )
        with TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = PanelRunner(config, adapters={"fake": FakeAdapter()}).run(
                _tasks(("judge-a", "judge-b")),
                run_id="panel-cost-1",
                limit_per_judge=1,
                responses_path=root / "responses.jsonl",
                errors_path=root / "errors.jsonl",
                manifest_path=root / "manifest.json",
            )

            self.assertEqual(manifest["cost"]["status"], "measured")
            self.assertEqual(manifest["cost"]["total_usd"], 0.052)

    def test_full_run_budget_gate_requires_declared_cap(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(PanelConfigurationError, "max_total_cost_usd"):
                PanelRunner(_config(), adapters={"fake": FakeAdapter()}).run(
                    _tasks(),
                    run_id="panel-full-missing-cap",
                    responses_path=root / "responses.jsonl",
                    errors_path=root / "errors.jsonl",
                    manifest_path=root / "manifest.json",
                    require_budget_cap=True,
                )

    def test_full_run_budget_manifest_records_conservative_ceiling(self) -> None:
        config = PanelRunConfig.from_mapping(
            {
                "schema_version": "requirements-smell-panel-runtime/v1",
                "judges": [
                    {"judge_id": "judge-a", "adapter": "fake", "model": "model-a"},
                    {"judge_id": "judge-b", "adapter": "fake", "model": "model-b"},
                ],
                "consensus_required": 2,
                "max_retries": 0,
                "max_total_cost_usd": 10.0,
                "max_total_attempts": 4,
                "pricing": {"input_usd_per_1k": 1.0, "output_usd_per_1k": 2.0},
            }
        )
        with TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = PanelRunner(config, adapters={"fake": FakeAdapter()}).run(
                _tasks(("judge-a", "judge-b")),
                run_id="panel-full-budget",
                responses_path=root / "responses.jsonl",
                errors_path=root / "errors.jsonl",
                manifest_path=root / "manifest.json",
                require_budget_cap=True,
            )

        self.assertTrue(manifest["budget"]["full_run_budget_gate"])
        self.assertEqual(manifest["budget"]["conservative_max_attempts"], 4)
        self.assertLess(manifest["budget"]["conservative_max_cost_usd"], 10.0)

    def test_full_panel_validates_expected_task_counts_before_network_calls(self) -> None:
        adapter = FakeAdapter()
        config = PanelRunConfig.from_mapping(
            {
                "schema_version": "requirements-smell-panel-runtime/v1",
                "stage": "full_panel",
                "expected_tasks_per_judge": 3,
                "expected_total_tasks": 6,
                "judges": [
                    {
                        "judge_id": "judge-a",
                        "adapter": "fake",
                        "model": "model-a",
                        "model_snapshot": "model-a@2026-08-27",
                    },
                    {
                        "judge_id": "judge-b",
                        "adapter": "fake",
                        "model": "model-b",
                        "model_snapshot": "model-b@2026-08-27",
                    },
                ],
            }
        )
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "expected 3 tasks per judge"):
                PanelRunner(config, adapters={"fake": adapter}).run(
                    _uniform_tasks(2),
                    run_id="panel-counts-1",
                    responses_path=root / "responses.jsonl",
                    errors_path=root / "errors.jsonl",
                    manifest_path=root / "manifest.json",
                )
        self.assertEqual(adapter.calls, [])

    def test_full_panel_rejects_equal_counts_with_different_item_sets(self) -> None:
        adapter = FakeAdapter()
        config = PanelRunConfig.from_mapping(
            {
                "schema_version": "requirements-smell-panel-runtime/v1",
                "stage": "full_panel",
                "expected_tasks_per_judge": 2,
                "expected_total_tasks": 4,
                "judges": [
                    {
                        "judge_id": "judge-a",
                        "adapter": "fake",
                        "model": "model-a",
                        "model_snapshot": "model-a@2026-08-27",
                    },
                    {
                        "judge_id": "judge-b",
                        "adapter": "fake",
                        "model": "model-b",
                        "model_snapshot": "model-b@2026-08-27",
                    },
                ],
            }
        )
        tasks = build_panel_tasks(
            [
                {
                    "candidate_id": "left-1",
                    "requirement_text": "The system shall process request one.",
                    "target_family": "polysemy",
                },
                {
                    "candidate_id": "left-2",
                    "requirement_text": "The system shall process request two.",
                    "target_family": "polysemy",
                },
            ],
            judge_ids=("judge-a",),
        ) + build_panel_tasks(
            [
                {
                    "candidate_id": "right-1",
                    "requirement_text": "The system shall process request one.",
                    "target_family": "polysemy",
                },
                {
                    "candidate_id": "right-3",
                    "requirement_text": "The system shall process request three.",
                    "target_family": "polysemy",
                },
            ],
            judge_ids=("judge-b",),
        )
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "same item set"):
                PanelRunner(config, adapters={"fake": adapter}).run(
                    tasks,
                    run_id="panel-item-set-1",
                    responses_path=root / "responses.jsonl",
                    errors_path=root / "errors.jsonl",
                    manifest_path=root / "manifest.json",
                )
        self.assertEqual(adapter.calls, [])

    def test_cost_budget_stops_before_the_next_call(self) -> None:
        adapter = FakeAdapter()
        config = PanelRunConfig.from_mapping(
            {
                "schema_version": "requirements-smell-panel-runtime/v1",
                "stage": "pilot",
                "max_total_cost_usd": 0.052,
                "judges": [
                    {
                        "judge_id": "judge-a",
                        "adapter": "fake",
                        "model": "model-a",
                        "model_snapshot": "model-a@2026-08-27",
                    },
                    {
                        "judge_id": "judge-b",
                        "adapter": "fake",
                        "model": "model-b",
                        "model_snapshot": "model-b@2026-08-27",
                    },
                ],
                "pricing": {"input_usd_per_1k": 1.0, "output_usd_per_1k": 2.0},
            }
        )
        with TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = PanelRunner(config, adapters={"fake": adapter}).run(
                _uniform_tasks(2),
                run_id="panel-budget-1",
                responses_path=root / "responses.jsonl",
                errors_path=root / "errors.jsonl",
                manifest_path=root / "manifest.json",
            )

        self.assertEqual(len(adapter.calls), 2)
        self.assertEqual(manifest["status"], "stopped_cost_budget")
        self.assertEqual(manifest["budget"]["status"], "exhausted")
        self.assertEqual(manifest["completed_task_count"], 2)
        self.assertEqual(manifest["remaining_task_count"], 2)

    def test_metered_adapter_error_does_not_make_budget_unmeasurable(self) -> None:
        adapter = MeteredErrorAdapter()
        config = PanelRunConfig.from_mapping(
            {
                "schema_version": "requirements-smell-panel-runtime/v1",
                "stage": "prepilot",
                "max_total_cost_usd": 1.0,
                "judges": [
                    {
                        "judge_id": "judge-a",
                        "adapter": "fake",
                        "model": "model-a",
                        "model_snapshot": "model-a@2026-08-30",
                    }
                ],
                "consensus_required": 1,
                "pricing": {"input_usd_per_1k": 1.0, "output_usd_per_1k": 2.0},
            }
        )
        with TemporaryDirectory() as directory:
            root = Path(directory)
            errors = root / "errors.jsonl"
            manifest = PanelRunner(config, adapters={"fake": adapter}).run(
                _uniform_tasks(2, judges=("judge-a",)),
                run_id="panel-metered-error-1",
                responses_path=root / "responses.jsonl",
                errors_path=errors,
                manifest_path=root / "manifest.json",
            )

            error_rows = [json.loads(line) for line in errors.read_text().splitlines()]

        self.assertEqual(len(adapter.calls), 2)
        self.assertEqual(manifest["status"], "completed")
        self.assertEqual(manifest["budget"]["limit_usd"], 1.0)
        self.assertEqual(manifest["budget"]["spent_usd"], 0.052)
        self.assertEqual(manifest["budget"]["status"], "measured")
        self.assertEqual(manifest["usage"]["total_tokens"], 36)
        self.assertEqual(error_rows[0]["usage"]["total_tokens"], 18)
        self.assertEqual(error_rows[0]["cost_usd"], 0.026)

    def test_required_control_matrix_is_checked_before_execution(self) -> None:
        candidates = [
            {
                "candidate_id": f"control-{index}",
                "requirement_text": f"The system shall process request {index}.",
                "target_family": "polysemy",
                "control_condition": condition,
            }
            for index, condition in enumerate(CONTROL_CONDITIONS)
        ]
        config = PanelRunConfig.from_mapping(
            {
                "schema_version": "requirements-smell-panel-runtime/v1",
                "stage": "pilot",
                "require_negative_controls": True,
                "judges": [
                    {
                        "judge_id": "judge-a",
                        "adapter": "fake",
                        "model": "model-a",
                        "model_snapshot": "model-a@2026-08-27",
                    },
                    {
                        "judge_id": "judge-b",
                        "adapter": "fake",
                        "model": "model-b",
                        "model_snapshot": "model-b@2026-08-27",
                    },
                ],
            }
        )
        with TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = PanelRunner(config, adapters={"fake": FakeAdapter()}).run(
                build_panel_tasks(candidates, judge_ids=("judge-a", "judge-b")),
                run_id="panel-controls-1",
                responses_path=root / "responses.jsonl",
                errors_path=root / "errors.jsonl",
                manifest_path=root / "manifest.json",
            )
        self.assertEqual(manifest["control_strata"], {f"polysemy:{condition}": 2 for condition in CONTROL_CONDITIONS})

    def test_resume_is_idempotent_for_completed_tasks(self) -> None:
        adapter = FakeAdapter()
        config = _config()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {
                "responses_path": root / "responses.jsonl",
                "errors_path": root / "errors.jsonl",
                "manifest_path": root / "manifest.json",
            }
            first = PanelRunner(config, adapters={"fake": adapter}).run(
                _tasks(),
                run_id="panel-resume-1",
                limit_per_judge=1,
                **paths,
            )
            calls_after_first = len(adapter.calls)
            second = PanelRunner(config, adapters={"fake": adapter}).run(
                _tasks(),
                run_id="panel-resume-1",
                limit_per_judge=1,
                resume=True,
                **paths,
            )

        self.assertEqual(calls_after_first, 3)
        self.assertEqual(len(adapter.calls), calls_after_first)
        self.assertEqual(first["ok_count"], second["ok_count"])
        self.assertEqual(second["resumed"], True)

    def test_existing_outputs_require_explicit_resume(self) -> None:
        adapter = FakeAdapter()
        config = _config()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {
                "responses_path": root / "responses.jsonl",
                "errors_path": root / "errors.jsonl",
                "manifest_path": root / "manifest.json",
            }
            PanelRunner(config, adapters={"fake": adapter}).run(
                _tasks(),
                run_id="panel-resume-guard",
                limit_per_judge=1,
                **paths,
            )
            with self.assertRaisesRegex(ValueError, "resume"):
                PanelRunner(config, adapters={"fake": adapter}).run(
                    _tasks(),
                    run_id="panel-resume-guard",
                    limit_per_judge=1,
                    **paths,
                )

    def test_stage_model_snapshot_and_public_configuration_are_recorded(self) -> None:
        config = PanelRunConfig.from_mapping(
            {
                "schema_version": "requirements-smell-panel-runtime/v1",
                "stage": "prepilot",
                "judges": [
                    {
                        "judge_id": "main",
                        "adapter": "fake",
                        "model": "model-main",
                        "model_snapshot": "model-main@2026-08-27",
                    }
                ],
                "consensus_required": 1,
            }
        )
        with TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = PanelRunner(config, adapters={"fake": FakeAdapter()}).run(
                _tasks(("main",)),
                run_id="panel-snapshot-1",
                limit_per_judge=1,
                responses_path=root / "responses.jsonl",
                errors_path=root / "errors.jsonl",
                manifest_path=root / "manifest.json",
            )

        self.assertEqual(manifest["stage"], "prepilot")
        self.assertEqual(manifest["judges"][0]["model_snapshot"], "model-main@2026-08-27")
        self.assertIn("configuration", manifest)
        self.assertNotIn('"api_key":', json.dumps(manifest))

    def test_runtime_config_rejects_unknown_fields_and_fractional_counts(self) -> None:
        base = {
            "schema_version": "requirements-smell-panel-runtime/v1",
            "judges": [
                {"judge_id": "judge-a", "adapter": "fake", "model": "model-a"},
            ],
            "consensus_required": 1,
        }
        with self.assertRaisesRegex(ValueError, "unsupported fields"):
            PanelRunConfig.from_mapping({**base, "max_total_cost": 1.0})
        with self.assertRaisesRegex(ValueError, "positive integer"):
            PanelRunConfig.from_mapping({**base, "expected_total_tasks": 1.5})

    def test_retry_is_recorded_without_leaking_response_or_secret(self) -> None:
        adapter = RetryOnceAdapter()
        config = _config(max_retries=1, judge_ids=("judge-a",))
        with TemporaryDirectory() as directory:
            root = Path(directory)
            responses = root / "responses.jsonl"
            errors = root / "errors.jsonl"
            manifest_path = root / "manifest.json"
            manifest = PanelRunner(config, adapters={"fake": adapter}).run(
                _tasks(("judge-a",)),
                run_id="panel-retry-1",
                limit_per_judge=1,
                responses_path=responses,
                errors_path=errors,
                manifest_path=manifest_path,
            )

            self.assertEqual(manifest["ok_count"], 1)
            record = json.loads(responses.read_text(encoding="utf-8"))
            self.assertEqual(record["attempts"], 2)
            self.assertEqual(errors.read_text(encoding="utf-8"), "")

    def test_missing_configured_secret_fails_before_network_call(self) -> None:
        config = PanelRunConfig.from_mapping(
            {
                "schema_version": "requirements-smell-panel-runtime/v1",
                "judges": [
                    {
                        "judge_id": "judge-a",
                        "adapter": "openai_compatible",
                        "endpoint": "https://example.invalid/v1/chat/completions",
                        "model": "model-a",
                        "api_key_env": "PANEL_TEST_MISSING_KEY",
                    },
                    {"judge_id": "judge-b", "adapter": "fake", "model": "model-b"},
                ],
                "consensus_required": 2,
            }
        )
        os.environ.pop("PANEL_TEST_MISSING_KEY", None)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "PANEL_TEST_MISSING_KEY"):
                PanelRunner(config).run(
                    _tasks(("judge-a", "judge-b")),
                    run_id="panel-missing-key",
                    limit_per_judge=1,
                    responses_path=root / "responses.jsonl",
                    errors_path=root / "errors.jsonl",
                    manifest_path=root / "manifest.json",
                )

    def test_builtin_adapters_resolve_env_backed_settings_without_vendor_logic_in_runner(self) -> None:
        captured: list[object] = []

        def opener(request: object, *, timeout: float) -> _HttpResponse:
            captured.append((request, timeout))
            return _HttpResponse(
                {
                    "choices": [
                        {"message": {"content": '{"label":"clean","target_family":"polysemy"}'}}
                    ],
                    "usage": {"prompt_tokens": 4, "completion_tokens": 3},
                }
            )

        os.environ["PANEL_RUNTIME_KEY"] = "secret-value-not-for-artifacts"
        os.environ["PANEL_RUNTIME_ENDPOINT"] = "https://example.invalid/v1/chat/completions"
        os.environ["PANEL_RUNTIME_MODEL"] = "model-from-env"
        config = PanelRunConfig.from_mapping(
            {
                "schema_version": "requirements-smell-panel-runtime/v1",
                "judges": [
                    {
                        "judge_id": "alpha",
                        "adapter": "openai_compatible",
                        "endpoint_env": "PANEL_RUNTIME_ENDPOINT",
                        "model_env": "PANEL_RUNTIME_MODEL",
                        "api_key_env": "PANEL_RUNTIME_KEY",
                    },
                    {"judge_id": "beta", "adapter": "fake", "model": "model-b"},
                ],
            }
        )
        judge = config.judges[0].resolve(config)
        response = OpenAICompatibleAdapter(opener=opener).complete(prompt="opaque prompt", judge=judge)
        self.assertEqual(json.loads(response.text)["label"], "clean")
        self.assertEqual(response.usage["prompt_tokens"], 4)
        self.assertEqual(len(captured), 1)
        request = captured[0][0]
        self.assertNotIn("secret-value-not-for-artifacts", str(request))

        def anthropic_opener(request: object, *, timeout: float) -> _HttpResponse:
            return _HttpResponse(
                {
                    "content": [{"type": "text", "text": '{"label":"smelly"}'}],
                    "usage": {"input_tokens": 5, "output_tokens": 2},
                }
            )

        anthropic_config = PanelRunConfig.from_mapping(
            {
                "schema_version": "requirements-smell-panel-runtime/v1",
                "judges": [
                    {
                        "judge_id": "alpha",
                        "adapter": "anthropic_messages",
                        "endpoint": "https://example.invalid/v1/messages",
                        "model": "model-a",
                        "api_key_env": "PANEL_RUNTIME_KEY",
                    },
                    {"judge_id": "beta", "adapter": "fake", "model": "model-b"},
                ],
            }
        )
        anthropic_judge = anthropic_config.judges[0].resolve(anthropic_config)
        anthropic_response = AnthropicMessagesAdapter(opener=anthropic_opener).complete(
            prompt="opaque prompt", judge=anthropic_judge
        )
        self.assertEqual(json.loads(anthropic_response.text)["label"], "smelly")
        self.assertEqual(anthropic_response.usage["output_tokens"], 2)
        os.environ.pop("PANEL_RUNTIME_KEY", None)
        os.environ.pop("PANEL_RUNTIME_ENDPOINT", None)
        os.environ.pop("PANEL_RUNTIME_MODEL", None)

    def test_reasoning_openai_compatible_request_uses_reasoning_safe_parameters(self) -> None:
        captured: list[object] = []

        def opener(request: object, *, timeout: float) -> _HttpResponse:
            captured.append((request, timeout))
            return _HttpResponse(
                {
                    "choices": [
                        {"message": {"content": '{"label":"clean","target_family":"polysemy"}'}},
                    ],
                    "usage": {"prompt_tokens": 4, "completion_tokens": 3},
                }
            )

        os.environ["PANEL_REASONING_KEY"] = "secret-value-not-for-artifacts"
        config = PanelRunConfig.from_mapping(
            {
                "schema_version": "requirements-smell-panel-runtime/v1",
                "judges": [
                    {
                        "judge_id": "reasoning",
                        "adapter": "openai_compatible",
                        "endpoint": "https://example.invalid/v1/chat/completions",
                        "model": "gpt-5-mini-2025-08-07",
                        "reasoning_effort": "low",
                        "api_key_env": "PANEL_REASONING_KEY",
                    }
                ],
                "consensus_required": 1,
            }
        )
        judge = config.judges[0].resolve(config)
        OpenAICompatibleAdapter(opener=opener).complete(prompt="opaque prompt", judge=judge)
        request = captured[0][0]
        body = json.loads(request.data.decode("utf-8"))

        self.assertEqual(body["reasoning_effort"], "low")
        self.assertEqual(body["max_completion_tokens"], 512)
        self.assertNotIn("temperature", body)
        self.assertNotIn("max_tokens", body)
        os.environ.pop("PANEL_REASONING_KEY", None)

    def test_openai_compatible_empty_content_preserves_provider_usage(self) -> None:
        def opener(request: object, *, timeout: float) -> _HttpResponse:
            return _HttpResponse(
                {
                    "choices": [{"message": {"content": ""}}],
                    "usage": {
                        "prompt_tokens": 261,
                        "completion_tokens": 1024,
                        "completion_tokens_details": {"reasoning_tokens": 1024},
                        "total_tokens": 1285,
                    },
                }
            )

        os.environ["PANEL_EMPTY_CONTENT_KEY"] = "secret-value-not-for-artifacts"
        config = PanelRunConfig.from_mapping(
            {
                "schema_version": "requirements-smell-panel-runtime/v1",
                "judges": [
                    {
                        "judge_id": "reasoning",
                        "adapter": "openai_compatible",
                        "endpoint": "https://example.invalid/v1/chat/completions",
                        "model": "reasoning-model",
                        "api_key_env": "PANEL_EMPTY_CONTENT_KEY",
                    }
                ],
                "consensus_required": 1,
            }
        )
        judge = config.judges[0].resolve(config)

        with self.assertRaisesRegex(PanelAdapterError, "no text content") as caught:
            OpenAICompatibleAdapter(opener=opener).complete(prompt="opaque prompt", judge=judge)

        self.assertEqual(caught.exception.usage["completion_tokens"], 1024)
        os.environ.pop("PANEL_EMPTY_CONTENT_KEY", None)


if __name__ == "__main__":
    unittest.main()
