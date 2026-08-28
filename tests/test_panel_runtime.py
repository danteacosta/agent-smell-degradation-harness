from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from label_plane.llm_panel import build_panel_tasks
from label_plane.panel_runtime import (
    AdapterResponse,
    AnthropicMessagesAdapter,
    OpenAICompatibleAdapter,
    PanelAdapterError,
    PanelConfigurationError,
    PanelRunConfig,
    PanelRunner,
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


def _config(*, max_retries: int = 0) -> PanelRunConfig:
    return PanelRunConfig.from_mapping(
        {
            "schema_version": "requirements-smell-panel-runtime/v1",
            "judges": [
                {"judge_id": "judge-a", "adapter": "fake", "model": "model-a"},
                {"judge_id": "judge-b", "adapter": "fake", "model": "model-b"},
                {"judge_id": "judge-c", "adapter": "fake", "model": "model-c"},
            ],
            "consensus_required": 2,
            "max_retries": max_retries,
            "retry_backoff_seconds": 0,
        }
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
                    {"judge_id": "judge-a", "adapter": "fake", "model": "model-a"},
                    {"judge_id": "judge-b", "adapter": "fake", "model": "model-b"},
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

    def test_full_run_budget_gate_requires_declared_cap_and_pricing(self) -> None:
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

    def test_retry_is_recorded_without_leaking_response_or_secret(self) -> None:
        adapter = RetryOnceAdapter()
        config = _config(max_retries=1)
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


if __name__ == "__main__":
    unittest.main()
