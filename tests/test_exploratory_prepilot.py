from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

import eval.exploratory_prepilot as runner
from eval.corpus_intake import build_redacted_manifest, freeze_validated_manifest
from eval.protocol_hashes import build_protocol_hashes
from eval.exploratory_prepilot import run_exploratory_prepilot


ROOT = Path(__file__).resolve().parents[1]


def _record(index: int) -> dict[str, object]:
    clean = f"The system shall reject request {index} after five minutes."
    defective = f"The system shall reject request {index} late."
    return {
        "source_intent_id": f"private-intent-{index:02d}",
        "project_id": f"project-{index % 6:02d}",
        "source_url": f"https://example.test/source/{index}",
        "source_revision_url": f"https://example.test/source/{index}/revisions/1",
        "source_revision_id": f"revision-{index:02d}-1",
        "retrieved_at": "2026-09-03T12:00:00+00:00",
        "license": "CC-BY-4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "reuse_permission_status": "license_confirmed",
        "rights_review": {
            "redistribution_allowed": True,
            "derivative_use_allowed": True,
            "external_provider_processing_allowed": True,
            "attribution_recorded": True,
            "reviewer_id": "rights-reviewer",
            "reviewed_at": "2026-09-03T12:01:00+00:00",
        },
        "canonical_text": f"Original source statement for request {index}.",
        "clean_requirement": clean,
        "defective_requirement": defective,
        "defect_family": "incompleteness_missing_condition",
        "removed_constraint_id": f"constraint-{index:02d}",
        "near_clone_group": f"near-clone-{index:02d}",
        "near_clone_reviewed": True,
        "manipulation_check": {
            "defect_present": True,
            "no_secondary_defect": True,
            "intent_preserved": True,
            "clean_variant_realistic": True,
            "constraint_independently_auditable": True,
            "reviewer_id": "manipulation-reviewer",
        },
        "generation_contract": {"test_gen": {"output_keys": ["criterion"]}},
    }


def _private_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    root = tmp_path / "repo"
    (root / "data/prepilot").mkdir(parents=True)
    (root / "tasks").mkdir()
    shutil.copy(
        ROOT / "tasks/acceptance_criteria_llm_judge_rubric.json",
        root / "tasks/acceptance_criteria_llm_judge_rubric.json",
    )
    records = [_record(index) for index in range(12)]
    private_corpus = tmp_path / "private-corpus.json"
    private_corpus.write_text(json.dumps(records), encoding="utf-8")
    candidate = build_redacted_manifest(records)
    frozen = freeze_validated_manifest(
        candidate,
        frozen_at="2026-09-03T12:02:00+00:00",
        freeze_reviewer_id="freeze-reviewer",
    )
    (root / "data/prepilot/corpus-manifest.json").write_text(
        json.dumps(frozen), encoding="utf-8"
    )
    constraints = {
        "schema_version": "prepilot-reference-constraints/v1",
        "records": [
            {
                "source_intent_id": f"private-intent-{index:02d}",
                "constraint_id": f"opaque-constraint-{index:02d}",
                "text": "The request is rejected after five minutes.",
            }
            for index in range(12)
        ],
    }
    reference_path = tmp_path / "reference-constraints.json"
    reference_path.write_text(json.dumps(constraints), encoding="utf-8")
    return root, private_corpus, reference_path


def _config(tmp_path: Path, source_revision: str) -> Path:
    payload = json.loads(
        (ROOT / "tasks/exploratory_llm_judged_prepilot.example.json").read_text(
            encoding="utf-8"
        )
    )
    payload["source_revision"] = source_revision
    payload["protocol_hashes"] = build_protocol_hashes(ROOT)
    path = tmp_path / "config.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_missing_frozen_manifest_blocks_before_provider_construction(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "tasks").mkdir()
    shutil.copy(
        ROOT / "tasks/acceptance_criteria_llm_judge_rubric.json",
        root / "tasks/acceptance_criteria_llm_judge_rubric.json",
    )
    source_revision = "a" * 40
    config = _config(tmp_path, source_revision)
    private = tmp_path / "private.json"
    private.write_text("[]", encoding="utf-8")
    reference = tmp_path / "reference.json"
    reference.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(runner, "_git_revision", lambda _root: source_revision)
    output = tmp_path / "report.json"

    report = run_exploratory_prepilot(
        config,
        output,
        private_corpus_path=private,
        reference_constraints_path=reference,
        repository_root=root,
        dry_run=True,
    )

    assert report["state"] == "stopped_protocol_violation"
    assert report["error_class"] == "ExploratoryPrepilotError"
    assert report["provider_api_calls"] == 0


def test_dry_run_reports_frozen_counts_and_budget_without_network(tmp_path, monkeypatch):
    root, private, reference = _private_inputs(tmp_path)
    source_revision = "b" * 40
    config = _config(tmp_path, source_revision)
    monkeypatch.setattr(runner, "_git_revision", lambda _root: source_revision)
    output = tmp_path / "dry-run-report.json"

    report = run_exploratory_prepilot(
        config,
        output,
        private_corpus_path=private,
        reference_constraints_path=reference,
        repository_root=root,
        dry_run=True,
    )

    assert report["state"] == "preflight_ready"
    assert report["base_episode_count"] == 120
    assert report["artifact_count"] == 240
    assert report["duplicate_base_task_count"] == 48
    assert report["logical_judging_calls"] == 576
    assert report["provider_api_calls"] == 1296
    assert report["preflight"]["worst_case_reserved_microusd"] == 988200
    serialized = output.read_text(encoding="utf-8")
    assert "The system shall reject" not in serialized
    assert "private-intent" not in serialized


def test_live_confirmation_is_required_after_a_ready_preflight(tmp_path, monkeypatch):
    root, private, reference = _private_inputs(tmp_path)
    source_revision = "c" * 40
    config = _config(tmp_path, source_revision)
    monkeypatch.setattr(runner, "_git_revision", lambda _root: source_revision)

    report = run_exploratory_prepilot(
        config,
        tmp_path / "confirmation-report.json",
        private_corpus_path=private,
        reference_constraints_path=reference,
        repository_root=root,
        provider_adapters={},
    )

    assert report["state"] == "stopped_protocol_violation"
    assert report["error_class"] == "LiveConfirmationRequired"


def test_live_run_stops_on_substantive_completeness_before_artifact(tmp_path, monkeypatch):
    root, private, reference = _private_inputs(tmp_path)
    source_revision = "d" * 40
    config = _config(tmp_path, source_revision)
    monkeypatch.setattr(runner, "_git_revision", lambda _root: source_revision)

    class VacuousProvider:
        def __init__(self, name: str, model: str, model_version: str) -> None:
            self.name = name
            self.model = model
            self.model_version = model_version
            self.calls = 0
            self.last_call_metadata: dict[str, object] = {}

        def complete(self, request):
            self.calls += 1
            self.last_call_metadata = {
                "usage": {"input_tokens": 10, "output_tokens": 2},
                "cost_usd": 0.0001,
            }
            return json.dumps({
                "constraints": [],
                "quantities": [],
                "unresolved_references": [],
                "assumptions": [],
                "contradictions": [],
                "conditional_semantics": [],
                "atomic_obligations": [],
            })

    report = run_exploratory_prepilot(
        config,
        tmp_path / "substantive-report.json",
        private_corpus_path=private,
        reference_constraints_path=reference,
        repository_root=root,
        provider_adapters={
            "openai-primary": VacuousProvider(
                "openai", "gpt-5.6-luna", "gpt-5.6-luna"
            ),
            "deepseek-secondary": VacuousProvider(
                "deepseek", "deepseek-v4-pro", "DeepSeek-V4-Pro-0813"
            ),
        },
        confirm_live=True,
    )

    assert report["state"] == "incomplete_substantive_evidence"
    assert report["error_class"] == "SubstantiveCompletenessError"
    assert report["artifact_count"] == 0
    assert report["judge_result_count"] == 0
    assert report["substantive_completeness"]["failed_stage"] == "interpretation"
