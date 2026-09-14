"""Immutable receipts for resumable exploratory judge results.

The provider-call session remains the authority for response and cost recovery.
These receipts add the missing semantic boundary: they bind a validated judge
response, and then its deterministic two-judge consolidation, to the frozen run.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from eval.recoverable_calls import RecoveryBlocked, digest, durable_create, read_record
from label_plane.exploratory_judge import (
    JudgeRequest,
    JudgeResponse,
    parse_judge_response,
    serialize_judge_request,
)


_MAX_CALL_RECEIPT_BYTES = 131_072
_MAX_RESULT_RECEIPT_BYTES = 65_536
_JUDGE_LABELS = {"clean", "minor", "moderate", "severe", "not_visible"}


class JudgeReceipts:
    """Persist validated judge calls and consolidated occurrence outcomes."""

    def __init__(self, directory: Path, scope: Mapping[str, str], ledger) -> None:
        self.directory = Path(directory)
        self.scope_sha256 = digest(dict(scope))
        self.ledger = ledger

    @staticmethod
    def _call_name(occurrence_id: str, provider_slot_id: str) -> str:
        return f"judge-call-{digest([occurrence_id, provider_slot_id])}.json"

    @staticmethod
    def _result_name(occurrence_id: str) -> str:
        return f"judge-result-{digest(occurrence_id)}.json"

    def call_binding(
        self,
        *,
        occurrence_id: str,
        provider_slot_id: str,
        generator_slot_id: str,
        judge_relation: str,
        provider: str,
        model: str,
        model_version: str,
        request: JudgeRequest,
        prompt: str,
    ) -> dict[str, Any]:
        return {
            "occurrence_id": occurrence_id,
            "provider_slot_id": provider_slot_id,
            "generator_slot_id": generator_slot_id,
            "judge_relation": judge_relation,
            "provider": provider,
            "model": model,
            "model_version": model_version,
            "request_sha256": digest(serialize_judge_request(request)),
            "prompt_sha256": digest(prompt),
            "scope_sha256": self.scope_sha256,
        }

    def _read_call_record(self, binding: Mapping[str, Any]) -> dict[str, Any] | None:
        path = self.directory / self._call_name(
            str(binding["occurrence_id"]), str(binding["provider_slot_id"])
        )
        if not path.exists():
            return None
        record = read_record(path, _MAX_CALL_RECEIPT_BYTES)
        if (
            set(record)
            != {"schema", "binding", "attempt", "response", "response_sha256", "ledger_head_hash", "receipt_sha256"}
            or record["schema"] != "judge-call-receipt/v1"
        ):
            raise RecoveryBlocked("judge call receipt has an invalid envelope")
        unsigned = {key: value for key, value in record.items() if key != "receipt_sha256"}
        if record["receipt_sha256"] != digest(unsigned):
            raise RecoveryBlocked("judge call receipt checksum mismatch")
        if record["binding"] != dict(binding):
            raise RecoveryBlocked("judge call receipt binding changed")
        if type(record["attempt"]) is not int or record["attempt"] not in {1, 2}:
            raise RecoveryBlocked("judge call receipt has an invalid attempt")
        if not isinstance(record["response"], str) or record["response_sha256"] != digest(record["response"]):
            raise RecoveryBlocked("judge call response checksum mismatch")
        heads = {event.get("event_hash") for event in self.ledger.events}
        if record["ledger_head_hash"] not in heads:
            raise RecoveryBlocked("judge call receipt cost boundary is not in the ledger")
        return record

    def load_call(
        self, binding: Mapping[str, Any], request: JudgeRequest
    ) -> JudgeResponse | None:
        record = self._read_call_record(binding)
        if record is None:
            return None
        return parse_judge_response(record["response"], request)

    def save_call(
        self, binding: Mapping[str, Any], request: JudgeRequest, response: str, *, attempt: int
    ) -> JudgeResponse:
        if type(attempt) is not int or attempt not in {1, 2}:
            raise RecoveryBlocked("judge call receipt has an invalid attempt")
        if not isinstance(response, str) or len(response.encode("utf-8")) > 65_536:
            raise RecoveryBlocked("judge response exceeds receipt bound")
        parsed = parse_judge_response(response, request)
        record = {
            "schema": "judge-call-receipt/v1",
            "binding": dict(binding),
            "attempt": attempt,
            "response": response,
            "response_sha256": digest(response),
            "ledger_head_hash": self.ledger.ledger_head_hash,
        }
        record["receipt_sha256"] = digest(record)
        durable_create(
            self.directory
            / self._call_name(
                str(binding["occurrence_id"]), str(binding["provider_slot_id"])
            ),
            record,
        )
        return parsed

    def result_binding(
        self,
        *,
        occurrence_id: str,
        base_task_id: str,
        artifact_id: str,
        generator_slot_id: str,
        request: JudgeRequest,
        provider_slot_ids: Sequence[str],
    ) -> dict[str, Any]:
        return {
            "occurrence_id": occurrence_id,
            "base_task_id": base_task_id,
            "artifact_id": artifact_id,
            "generator_slot_id": generator_slot_id,
            "request_sha256": digest(serialize_judge_request(request)),
            "provider_slot_ids": sorted(str(value) for value in provider_slot_ids),
            "scope_sha256": self.scope_sha256,
        }

    def load_result(
        self,
        binding: Mapping[str, Any],
        call_bindings: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any] | None:
        path = self.directory / self._result_name(str(binding["occurrence_id"]))
        if not path.exists():
            return None
        record = read_record(path, _MAX_RESULT_RECEIPT_BYTES)
        if (
            set(record)
            != {"schema", "binding", "result", "call_receipt_sha256s", "ledger_head_hash", "receipt_sha256"}
            or record["schema"] != "judge-result-receipt/v1"
        ):
            raise RecoveryBlocked("judge result receipt has an invalid envelope")
        unsigned = {key: value for key, value in record.items() if key != "receipt_sha256"}
        if record["receipt_sha256"] != digest(unsigned) or record["binding"] != dict(binding):
            raise RecoveryBlocked("judge result receipt checksum or binding mismatch")
        expected_hashes: dict[str, str] = {}
        for call_binding in call_bindings:
            call_record = self._read_call_record(call_binding)
            if call_record is None:
                raise RecoveryBlocked("judge result is missing a judge call receipt")
            expected_hashes[str(call_binding["provider_slot_id"])] = call_record["receipt_sha256"]
        if record["call_receipt_sha256s"] != expected_hashes:
            raise RecoveryBlocked("judge result call receipts changed")
        heads = {event.get("event_hash") for event in self.ledger.events}
        if record["ledger_head_hash"] not in heads:
            raise RecoveryBlocked("judge result cost boundary is not in the ledger")
        return self._validated_result(record["result"], binding, call_bindings)

    @staticmethod
    def _validated_result(
        result: Any,
        binding: Mapping[str, Any],
        call_bindings: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        if (
            not isinstance(result, Mapping)
            or set(result) != {"label", "consensus", "judges"}
            or result["label"] not in _JUDGE_LABELS | {"uncertain"}
            or type(result["consensus"]) is not bool
            or not isinstance(result["judges"], list)
            or len(result["judges"]) != len(call_bindings)
        ):
            raise RecoveryBlocked("judge result receipt contains an invalid result")
        expected = {
            str(call["provider_slot_id"]): str(call["judge_relation"])
            for call in call_bindings
        }
        actual: dict[str, str] = {}
        for item in result["judges"]:
            if (
                not isinstance(item, Mapping)
                or set(item) != {
                    "provider_slot_id", "judge_relation", "label", "constraint_statuses"
                }
                or item["label"] not in _JUDGE_LABELS
                or item["judge_relation"] not in {"self", "cross"}
                or not isinstance(item["constraint_statuses"], list)
                or not item["constraint_statuses"]
                or any(
                    not isinstance(status, Mapping)
                    or set(status) != {"constraint_id", "status"}
                    or status["status"] not in {"covered", "omitted", "uncertain"}
                    for status in item["constraint_statuses"]
                )
                or len({status["constraint_id"] for status in item["constraint_statuses"]})
                != len(item["constraint_statuses"])
                or str(item["provider_slot_id"]) in actual
            ):
                raise RecoveryBlocked("judge result receipt contains an invalid judge")
            actual[str(item["provider_slot_id"])] = str(item["judge_relation"])
        if actual != expected or sorted(actual) != list(binding["provider_slot_ids"]):
            raise RecoveryBlocked("judge result receipt provider relations changed")
        signatures = {
            (
                item["label"],
                tuple(
                    sorted(
                        (status["constraint_id"], status["status"])
                        for status in item["constraint_statuses"]
                    )
                ),
            )
            for item in result["judges"]
        }
        if result["consensus"] != (len(signatures) == 1):
            raise RecoveryBlocked("judge result receipt consensus is inconsistent")
        if result["label"] != (
            result["judges"][0]["label"] if result["consensus"] else "uncertain"
        ):
            raise RecoveryBlocked("judge result receipt label is inconsistent")
        return dict(result)

    def save_result(
        self,
        binding: Mapping[str, Any],
        call_bindings: Sequence[Mapping[str, Any]],
        result: Mapping[str, Any],
    ) -> None:
        result = self._validated_result(result, binding, call_bindings)
        call_hashes: dict[str, str] = {}
        for call_binding in call_bindings:
            call_record = self._read_call_record(call_binding)
            if call_record is None:
                raise RecoveryBlocked("cannot consolidate without both judge call receipts")
            call_hashes[str(call_binding["provider_slot_id"])] = call_record["receipt_sha256"]
        record = {
            "schema": "judge-result-receipt/v1",
            "binding": dict(binding),
            "result": result,
            "call_receipt_sha256s": call_hashes,
            "ledger_head_hash": self.ledger.ledger_head_hash,
        }
        record["receipt_sha256"] = digest(record)
        durable_create(
            self.directory / self._result_name(str(binding["occurrence_id"])), record
        )

    def validate_inventory(
        self, occurrence_ids: Sequence[str], provider_slot_ids: Sequence[str]
    ) -> None:
        expected_calls = {
            self._call_name(str(occurrence), str(provider))
            for occurrence in occurrence_ids
            for provider in provider_slot_ids
        }
        expected_results = {self._result_name(str(value)) for value in occurrence_ids}
        actual_calls = {path.name for path in self.directory.glob("judge-call-*.json")}
        actual_results = {path.name for path in self.directory.glob("judge-result-*.json")}
        if not actual_calls.issubset(expected_calls) or not actual_results.issubset(expected_results):
            raise RecoveryBlocked("unexpected judge receipt in run directory")


__all__ = ["JudgeReceipts"]
