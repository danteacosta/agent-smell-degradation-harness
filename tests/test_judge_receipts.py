import json

import pytest

from eval.exploratory_cost import CostLedger
from eval.judge_receipts import JudgeReceipts
from eval.recoverable_calls import RecoveryBlocked
from label_plane.exploratory_judge import JudgeRequest, ReferenceConstraint
from test_exploratory_cost import config


SCOPE = {"run_id": "run", "configuration_sha256": "a" * 64}


def _ledger(path):
    ledger = CostLedger(path, config())
    pricing = config().provider_pricing[0]
    for index in range(2):
        reservation = ledger.reserve_attempt(
            call_id=f"judge:{index}", provider=pricing.provider,
            model=pricing.model, model_version=pricing.model_version,
            phase="judge", attempt=1,
        )
        ledger.reconcile_response(
            reservation, {"input_tokens": 1, "output_tokens": 1},
            metadata={"usage": {"input_tokens": 1, "output_tokens": 1}},
        )
    return ledger


def _request():
    return JudgeRequest(
        "occurrence", '{"criterion":"bounded"}',
        (ReferenceConstraint("constraint", "The request is bounded."),),
    )


def _binding(receipts, request, slot):
    return receipts.call_binding(
        occurrence_id="occurrence", provider_slot_id=slot,
        generator_slot_id="slot-a", judge_relation="self" if slot == "slot-a" else "cross",
        provider="fixture", model="fixture-model", model_version="fixture-version",
        request=request, prompt=f"prompt-{slot}",
    )


def test_restores_calls_and_consolidated_result(tmp_path):
    ledger = _ledger(tmp_path / "ledger.jsonl")
    receipts = JudgeReceipts(tmp_path, SCOPE, ledger)
    request = _request()
    bindings = [_binding(receipts, request, slot) for slot in ("slot-a", "slot-b")]
    for binding in bindings:
        parsed = receipts.save_call(
            binding, request, '{"label":"clean","status":"covered"}', attempt=1
        )
        assert parsed.label == "clean"
    result_binding = receipts.result_binding(
        occurrence_id="occurrence", base_task_id="task", artifact_id="artifact",
        generator_slot_id="slot-a", request=request,
        provider_slot_ids=["slot-a", "slot-b"],
    )
    result = {
        "label": "clean", "consensus": True,
        "judges": [
            {"provider_slot_id": "slot-a", "judge_relation": "self", "label": "clean", "constraint_statuses": [{"constraint_id": "constraint", "status": "covered"}]},
            {"provider_slot_id": "slot-b", "judge_relation": "cross", "label": "clean", "constraint_statuses": [{"constraint_id": "constraint", "status": "covered"}]},
        ],
    }
    receipts.save_result(result_binding, bindings, result)

    assert receipts.load_result(result_binding, bindings) == result
    assert receipts.load_call(bindings[0], request).label == "clean"


@pytest.mark.parametrize("target", ["call", "result"])
def test_tampering_blocks_recovery(tmp_path, target):
    ledger = _ledger(tmp_path / "ledger.jsonl")
    receipts = JudgeReceipts(tmp_path, SCOPE, ledger)
    request = _request()
    bindings = [_binding(receipts, request, slot) for slot in ("slot-a", "slot-b")]
    for binding in bindings:
        receipts.save_call(
            binding, request, '{"label":"clean","status":"covered"}', attempt=1
        )
    result_binding = receipts.result_binding(
        occurrence_id="occurrence", base_task_id="task", artifact_id="artifact",
        generator_slot_id="slot-a", request=request,
        provider_slot_ids=["slot-a", "slot-b"],
    )
    result = {"label": "clean", "consensus": True, "judges": [
        {"provider_slot_id": "slot-a", "judge_relation": "self", "label": "clean", "constraint_statuses": [{"constraint_id": "constraint", "status": "covered"}]},
        {"provider_slot_id": "slot-b", "judge_relation": "cross", "label": "clean", "constraint_statuses": [{"constraint_id": "constraint", "status": "covered"}]},
    ]}
    receipts.save_result(result_binding, bindings, result)
    path = next(tmp_path.glob("judge-call-*.json")) if target == "call" else next(tmp_path.glob("judge-result-*.json"))
    value = json.loads(path.read_text())
    value["ledger_head_hash"] = "0" * 64
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")))
    with pytest.raises(RecoveryBlocked):
        receipts.load_result(result_binding, bindings)


def test_unknown_receipt_inventory_is_rejected(tmp_path):
    ledger = _ledger(tmp_path / "ledger.jsonl")
    receipts = JudgeReceipts(tmp_path, SCOPE, ledger)
    request = _request()
    receipts.save_call(
        _binding(receipts, request, "slot-a"), request,
        '{"label":"clean","status":"covered"}', attempt=1,
    )
    with pytest.raises(RecoveryBlocked, match="unexpected"):
        receipts.validate_inventory(["different"], ["slot-a"])


@pytest.mark.parametrize("failed_boundary", ["receipt", "evidence"])
def test_judge_persistence_failure_never_dispatches_another_paid_attempt(
    tmp_path, failed_boundary
):
    from eval.exploratory_prepilot import _invoke_judge

    class Provider:
        calls = 0

        def complete(self, request, **kwargs):
            self.calls += 1
            return '{"label":"clean","status":"covered"}'

    provider = Provider()
    receipt_directory = tmp_path if failed_boundary == "evidence" else tmp_path / "missing"
    receipts = JudgeReceipts(receipt_directory, SCOPE, _ledger(tmp_path / "ledger.jsonl"))
    # Opening a directory for append fails after the call receipt is durable.
    evidence_path = tmp_path if failed_boundary == "evidence" else tmp_path / "evidence.jsonl"
    with pytest.raises(OSError):
        _invoke_judge(
            budgeted=provider, provider_slot_id="slot-a", generator_slot_id="slot-a",
            occurrence_id="occurrence", request=_request(), evidence_path=evidence_path,
            max_output_tokens=100, receipts=receipts, provider="fixture",
            model="fixture-model", model_version="fixture-version",
        )
    assert provider.calls == 1
    if failed_boundary == "evidence":
        restored, error = _invoke_judge(
            budgeted=provider, provider_slot_id="slot-a", generator_slot_id="slot-a",
            occurrence_id="occurrence", request=_request(),
            evidence_path=tmp_path / "recovered-evidence.jsonl", max_output_tokens=100,
            receipts=receipts, provider="fixture", model="fixture-model",
            model_version="fixture-version",
        )
        assert restored.label == "clean"
        assert error is None
        assert provider.calls == 1
