from __future__ import annotations

import io
import json
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from label_plane.llm_panel import build_panel_tasks
from label_plane.panel_runtime import AdapterResponse, PanelRunner as RealPanelRunner
from scripts import run_llm_panel as cli


class RecordingAdapter:
    name = "fake"

    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def complete(self, *, prompt: str, judge: object) -> AdapterResponse:
        self.calls.append(
            {
                "judge_id": str(getattr(judge, "judge_id")),
                "model": str(getattr(judge, "model")),
                "prompt": prompt,
            }
        )
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


class RunLlmPanelTests(unittest.TestCase):
    def _private_inputs(self, root: Path) -> tuple[Path, Path, Path, Path, Path]:
        private = root / "private"
        private.mkdir()
        config = private / "config.json"
        config.write_text(
            json.dumps(
                {
                    "schema_version": "requirements-smell-panel-runtime/v1",
                    "stage": "prepilot",
                    "judges": [
                        {
                            "judge_id": "judge-a",
                            "adapter": "fake",
                            "model_env": "PANEL_TEST_MODEL",
                        }
                    ],
                    "consensus_required": 1,
                    "max_retries": 0,
                }
            ),
            encoding="utf-8",
        )
        tasks = private / "tasks.jsonl"
        task_rows = build_panel_tasks(
            [
                {
                    "candidate_id": "opaque-1",
                    "requirement_text": "The system shall process the request.",
                    "target_family": "polysemy",
                }
            ],
            judge_ids=("judge-a",),
        )
        tasks.write_text("\n".join(json.dumps(row) for row in task_rows) + "\n", encoding="utf-8")
        return (
            config,
            tasks,
            private / "responses.jsonl",
            private / "errors.jsonl",
            private / "manifest.json",
        )

    def _argv(
        self,
        config: Path,
        tasks: Path,
        responses: Path,
        errors: Path,
        manifest: Path,
    ) -> list[str]:
        return [
            "run_llm_panel.py",
            "--tasks",
            str(tasks),
            "--config",
            str(config),
            "--run-id",
            "dotenv-cli-test",
            "--responses",
            str(responses),
            "--errors",
            str(errors),
            "--manifest",
            str(manifest),
            "--limit-per-judge",
            "1",
        ]

    def test_cli_loads_repository_env_and_preserves_output_contract(self) -> None:
        secret = "SECRET_VALUE_SENTINEL"
        with TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repo"
            repository.mkdir()
            (repository / ".env").write_text(
                f"PANEL_TEST_MODEL=model-from-dotenv\nPANEL_UNUSED_SECRET={secret}\n",
                encoding="utf-8",
            )
            config, tasks, responses, errors, manifest = self._private_inputs(root)
            adapter = RecordingAdapter()

            def runner_factory(config_value: object) -> RealPanelRunner:
                return RealPanelRunner(config_value, adapters={"fake": adapter})  # type: ignore[arg-type]

            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                patch.dict(os.environ, {}, clear=True),
                patch.object(cli, "REPOSITORY_ROOT", repository),
                patch.object(cli, "PanelRunner", new=runner_factory),
                patch.object(sys, "argv", self._argv(config, tasks, responses, errors, manifest)),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                result = cli.main()

            response_rows = [json.loads(line) for line in responses.read_text(encoding="utf-8").splitlines()]
            manifest_value = json.loads(manifest.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(len(adapter.calls), 1)
        self.assertEqual(adapter.calls[0]["model"], "model-from-dotenv")
        self.assertEqual(response_rows[0]["schema_version"], "requirements-smell-panel-response/v1")
        self.assertEqual(response_rows[0]["usage"]["total_tokens"], 18)
        self.assertEqual(manifest_value["ok_count"], 1)
        self.assertEqual(json.loads(stdout.getvalue()), manifest_value)
        self.assertEqual(stderr.getvalue(), "")
        self.assertNotIn(secret, stdout.getvalue() + stderr.getvalue())

    def test_cli_does_not_replace_inherited_empty_value(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repo"
            repository.mkdir()
            (repository / ".env").write_text("PANEL_TEST_MODEL=model-from-dotenv\n", encoding="utf-8")
            config, tasks, responses, errors, manifest = self._private_inputs(root)
            adapter = RecordingAdapter()

            def runner_factory(config_value: object) -> RealPanelRunner:
                return RealPanelRunner(config_value, adapters={"fake": adapter})  # type: ignore[arg-type]

            stderr = io.StringIO()
            with (
                patch.dict(os.environ, {"PANEL_TEST_MODEL": ""}, clear=True),
                patch.object(cli, "REPOSITORY_ROOT", repository),
                patch.object(cli, "PanelRunner", new=runner_factory),
                patch.object(sys, "argv", self._argv(config, tasks, responses, errors, manifest)),
                redirect_stderr(stderr),
                self.assertRaises(SystemExit) as raised,
            ):
                cli.main()

        self.assertEqual(raised.exception.code, 1)
        self.assertEqual(adapter.calls, [])
        self.assertIn("missing model", stderr.getvalue())

    def test_malformed_env_exits_before_runner_call_without_leaking_value(self) -> None:
        secret = "SECRET_VALUE_SENTINEL"
        with TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repo"
            repository.mkdir()
            (repository / ".env").write_text(
                f"PANEL_TEST_MODEL={secret}\nmalformed-line\n", encoding="utf-8"
            )
            config, tasks, responses, errors, manifest = self._private_inputs(root)
            runner_calls: list[object] = []

            def runner_factory(config_value: object) -> RealPanelRunner:
                runner_calls.append(config_value)
                return RealPanelRunner(config_value)  # type: ignore[arg-type]

            stderr = io.StringIO()
            with (
                patch.dict(os.environ, {}, clear=True),
                patch.object(cli, "REPOSITORY_ROOT", repository),
                patch.object(cli, "PanelRunner", new=runner_factory),
                patch.object(sys, "argv", self._argv(config, tasks, responses, errors, manifest)),
                redirect_stderr(stderr),
                self.assertRaises(SystemExit) as raised,
            ):
                cli.main()

        self.assertEqual(raised.exception.code, 1)
        self.assertEqual(runner_calls, [])
        self.assertIn("line 2", stderr.getvalue())
        self.assertNotIn(secret, stderr.getvalue())

    def test_nonregular_env_exits_before_runner_call_without_leaking_path(self) -> None:
        with TemporaryDirectory(prefix="PRIVATE_PATH_SENTINEL-") as directory:
            root = Path(directory)
            repository = root / "repo"
            repository.mkdir()
            (repository / ".env").mkdir()
            config, tasks, responses, errors, manifest = self._private_inputs(root)
            runner_calls: list[object] = []

            def runner_factory(config_value: object) -> RealPanelRunner:
                runner_calls.append(config_value)
                return RealPanelRunner(config_value)  # type: ignore[arg-type]

            stderr = io.StringIO()
            with (
                patch.dict(os.environ, {}, clear=True),
                patch.object(cli, "REPOSITORY_ROOT", repository),
                patch.object(cli, "PanelRunner", new=runner_factory),
                patch.object(sys, "argv", self._argv(config, tasks, responses, errors, manifest)),
                redirect_stderr(stderr),
                self.assertRaises(SystemExit) as raised,
            ):
                cli.main()

        self.assertEqual(raised.exception.code, 1)
        self.assertEqual(runner_calls, [])
        self.assertNotIn("PRIVATE_PATH_SENTINEL", stderr.getvalue())
