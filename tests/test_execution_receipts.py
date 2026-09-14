import json

import pytest

from agents.checkpoints import AgentExecution, CheckpointObservation
from eval.execution_receipts import ExecutionReceipts
from eval.exploratory_cost import CostLedger
from eval.recoverable_calls import RecoveryBlocked
from test_exploratory_cost import config


SCOPE = {"run_id": "run", "configuration_sha256": "a" * 64}


def execution():
    interpretation = {
        "constraints": ["c"], "quantities": [], "unresolved_references": [],
        "assumptions": [], "contradictions": [], "conditional_semantics": [],
        "atomic_obligations": [],
    }
    plan = {"validation_checks": [], "planned_tools": [], "coverage_targets": []}
    tool = {
        "revisions": 0, "validation_attempts": 1, "errors": [],
        "retrieval_events": 0, "constraint_lineage": [],
        "context_management": [], "atomic_obligation_observations": [],
    }
    times = [
        ("2026-09-13T12:00:00+00:00", "2026-09-13T12:00:01+00:00"),
        ("2026-09-13T12:00:01+00:00", "2026-09-13T12:00:02+00:00"),
        ("2026-09-13T12:00:02+00:00", "2026-09-13T12:00:02+00:00"),
        ("2026-09-13T12:00:02+00:00", "2026-09-13T12:00:03+00:00"),
    ]
    return AgentExecution(tuple(
        CheckpointObservation(name, payload, *time)
        for name, payload, time in zip(
            ("interpretation.completed", "plan.completed", "execution.started", "tool.completed"),
            (interpretation, plan, {}, tool), times, strict=True)
    ), {"criterion": "x"}, {
        "provider": "fixture", "model": "fixture-model",
        "model_version": "fixture-version"})


def ledger_with_cost(path):
    ledger = CostLedger(path, config())
    pricing = config().provider_pricing[0]
    reservation = ledger.reserve_attempt(
        call_id="artifact:T1", provider=pricing.provider,
        model=pricing.model, model_version=pricing.model_version,
        phase="generation.T1", attempt=1)
    ledger.reconcile_response(
        reservation, {"input_tokens": 1, "output_tokens": 1},
        metadata={"usage": {"input_tokens": 1, "output_tokens": 1}})
    return ledger


def test_restores_original_timestamps_and_payload(tmp_path):
    ledger = ledger_with_cost(tmp_path / "ledger.jsonl")
    receipts = ExecutionReceipts(tmp_path, SCOPE, ledger)
    binding = receipts.binding(
        artifact_id="a", episode_id="e", base_task_id="b", provider_slot_id="p",
        provider="fixture", model="fixture-model", model_version="fixture-version",
        pair={"private": "pair"}, variant="clean", task_family="test_gen")
    original = execution()
    receipts.save(binding, original)
    restored = receipts.load(binding)
    assert restored == original
    assert [item.started_at for item in restored.checkpoints] == [
        item.started_at for item in original.checkpoints]


@pytest.mark.parametrize("change", ["binding", "execution", "ledger"])
def test_changed_binding_execution_or_cost_boundary_blocks(tmp_path, change):
    ledger = ledger_with_cost(tmp_path / "ledger.jsonl")
    receipts = ExecutionReceipts(tmp_path, SCOPE, ledger)
    binding = receipts.binding(
        artifact_id="a", episode_id="e", base_task_id="b", provider_slot_id="p",
        provider="fixture", model="fixture-model", model_version="fixture-version",
        pair={"private": "pair"}, variant="clean", task_family="test_gen")
    receipts.save(binding, execution())
    if change == "binding":
        binding["pair_sha256"] = "0" * 64
    else:
        path = next(tmp_path.glob("execution-*.json"))
        value = json.loads(path.read_text())
        if change == "execution":
            value["execution"]["artifact"]["criterion"] = "changed"
        else:
            value["ledger_head_hash"] = "0" * 64
        path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")))
    with pytest.raises(RecoveryBlocked):
        receipts.load(binding)


def test_unplanned_receipt_and_provider_identity_are_rejected(tmp_path):
    ledger = ledger_with_cost(tmp_path / "ledger.jsonl")
    receipts = ExecutionReceipts(tmp_path, SCOPE, ledger)
    binding = receipts.binding(
        artifact_id="a", episode_id="e", base_task_id="b", provider_slot_id="p",
        provider="fixture", model="fixture-model", model_version="fixture-version",
        pair={"private": "pair"}, variant="clean", task_family="test_gen")
    receipts.save(binding, execution())
    with pytest.raises(RecoveryBlocked, match="unexpected"):
        receipts.validate_inventory(["different"])
    binding["provider"] = "other"
    with pytest.raises(RecoveryBlocked):
        receipts.load(binding)
