from __future__ import annotations

import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from agents.providers import ProviderRequest
from eval.exploratory_cost import (
    AmbiguousInFlightError,
    BudgetExhaustedError,
    CostConfiguration,
    CostLedger,
    CostLedgerError,
    CostUnverifiedError,
    PlannedCall,
    ProviderPricing,
    TokenBounds,
    budgeted_provider,
    fixed_task3_call_plan,
)


PHASE_BOUNDS = {
    "generation.T1": TokenBounds(input_tokens=192, output_tokens=128),
    "generation.T2": TokenBounds(input_tokens=192, output_tokens=64),
    "generation.artifact": TokenBounds(input_tokens=192, output_tokens=48),
    "judge": TokenBounds(input_tokens=128, output_tokens=64),
}


def pricing(
    provider: str = "openai",
    *,
    model: str | None = None,
    input_rate: str = "0.000001",
    cached_rate: str = "0.0000001",
    output_rate: str = "0.000001",
) -> ProviderPricing:
    return ProviderPricing(
        provider=provider,
        model=model or f"{provider}-model",
        model_version=f"{provider}-snapshot",
        pricing_snapshot_date="2026-09-02",
        pricing_source_ref="docs/research/2026-09-02-native-provider-smoke-model-selection.md",
        input_usd_per_1k=Decimal(input_rate),
        cached_input_usd_per_1k=Decimal(cached_rate),
        output_usd_per_1k=Decimal(output_rate),
    )


def config(
    *,
    providers: tuple[ProviderPricing, ...] = (pricing(), pricing("deepseek")),
    plan: tuple[PlannedCall, ...] | None = None,
    bounds: dict[str, TokenBounds] | None = None,
    cap: str = "1.00",
    contingency: str = "0.25",
    max_attempts: int = 2,
) -> CostConfiguration:
    provider_snapshot = tuple(providers)
    if len(provider_snapshot) == 1:
        provider_snapshot = provider_snapshot + (pricing("deepseek"),)
    canonical_plan = fixed_task3_call_plan(item.provider for item in provider_snapshot)
    if plan is not None:
        assert tuple(plan) == canonical_plan
    merged_bounds = dict(PHASE_BOUNDS)
    if bounds is not None:
        merged_bounds.update(bounds)
    return CostConfiguration(
        provider_pricing=provider_snapshot,
        token_bounds=merged_bounds,
        planned_calls=canonical_plan,
        approved_cap_usd=Decimal(cap),
        contingency_rate=Decimal(contingency),
        max_attempts_per_api_call=max_attempts,
    )


class RecordingProvider:
    name = "openai"

    def __init__(self, metadata: dict[str, object] | None = None) -> None:
        self.calls = 0
        self.last_call_metadata = (
            metadata
            if metadata is not None
            else {
                "usage": {"input_tokens": 1, "output_tokens": 1},
                "response_model": "openai-model",
            }
        )

    def complete(self, request: ProviderRequest) -> str:
        self.calls += 1
        return '{"ok":true}'


def request() -> ProviderRequest:
    return ProviderRequest(
        prompt="private prompt must not enter the ledger",
        pair={"requirement": "private requirement", "task_family": "test_gen"},
        variant="opaque",
        task_family="test_gen",
    )


def test_given_fixed_task3_plan_when_preflight_runs_then_it_reports_the_full_integer_envelope() -> None:
    providers = (pricing("openai"), pricing("deepseek"))
    configuration = CostConfiguration(
        provider_pricing=providers,
        token_bounds=PHASE_BOUNDS,
        planned_calls=fixed_task3_call_plan((item.provider for item in providers)),
        approved_cap_usd=Decimal("1.00"),
        contingency_rate=Decimal("0.25"),
        max_attempts_per_api_call=2,
    )

    report = configuration.preflight()

    assert report.passed is True
    assert report.planned_provider_api_calls == 1296
    assert report.max_attempts_per_api_call == 2
    assert report.direct_expected_cost_microusd == 1296
    assert report.retry_inclusive_worst_case_microusd == 2592
    assert report.contingency_reserve_microusd == 324
    assert report.worst_case_reserved_microusd == 2916
    assert report.approved_cap_microusd == 1_000_000
    assert report.unused_headroom_microusd == 997_084
    assert report["direct_expected_cost_usd"] == "0.001296"
    assert report["retry_inclusive_worst_case_usd"] == "0.002592"
    assert report["contingency_reserve_usd"] == "0.000324"
    assert report["unused_headroom_usd"] == "0.997084"
    assert all("float" not in type(value).__name__ for value in report.to_dict().values())


def test_given_noncanonical_plan_or_attempt_policy_when_configured_then_it_is_rejected() -> None:
    providers = (pricing("openai"), pricing("deepseek"))

    with pytest.raises(ValueError, match="planned_calls"):
        CostConfiguration(
            provider_pricing=providers,
            token_bounds=PHASE_BOUNDS,
            planned_calls=(PlannedCall("openai", "judge", 1),),
        )
    with pytest.raises(ValueError, match="max_attempts"):
        CostConfiguration(
            provider_pricing=providers,
            token_bounds=PHASE_BOUNDS,
            planned_calls=fixed_task3_call_plan(item.provider for item in providers),
            max_attempts_per_api_call=1,
        )
    with pytest.raises(ValueError, match="hard USD 1.00 cap"):
        CostConfiguration(
            provider_pricing=providers,
            token_bounds=PHASE_BOUNDS,
            planned_calls=fixed_task3_call_plan(item.provider for item in providers),
            approved_cap_usd=Decimal("1.01"),
        )


def test_given_forged_preflight_when_ledger_is_created_then_configuration_is_recomputed(
    tmp_path: Path,
) -> None:
    configuration = config(contingency="0")
    forged = replace(
        configuration.preflight(),
        approved_cap_microusd=configuration.approved_cap_microusd + 1,
    )

    with pytest.raises(CostLedgerError, match="preflight"):
        CostLedger(tmp_path / "forged.jsonl", configuration, preflight=forged)

    assert not (tmp_path / "forged.jsonl").exists()


def test_given_expensive_fixed_prices_when_preflight_runs_then_budget_fails_closed() -> None:
    providers = (
        pricing("openai", input_rate="0.01", output_rate="0.01"),
        pricing("deepseek", input_rate="0.01", output_rate="0.01"),
    )
    configuration = CostConfiguration(
        provider_pricing=providers,
        token_bounds=PHASE_BOUNDS,
        planned_calls=fixed_task3_call_plan((item.provider for item in providers)),
        approved_cap_usd=Decimal("1.00"),
    )

    report = configuration.preflight()

    assert report.passed is False
    assert report.budget_status == "stopped_budget_exhausted"
    assert report.stop_reason == "worst_case_reserved_cost_exceeds_approved_cap"
    assert report.worst_case_reserved_microusd > report.approved_cap_microusd


def test_given_fractional_micro_cost_when_reserved_then_every_ceiling_is_upward() -> None:
    one_call = CostConfiguration(
        provider_pricing=(pricing(input_rate="0.0000001", output_rate="0.0000001"), pricing("deepseek", input_rate="0.0000001", output_rate="0.0000001")),
        token_bounds={phase: TokenBounds(input_tokens=1, output_tokens=1) for phase in PHASE_BOUNDS},
        planned_calls=fixed_task3_call_plan(("openai", "deepseek")),
        approved_cap_usd=Decimal("1.00"),
        contingency_rate=Decimal("0"),
        max_attempts_per_api_call=2,
    )

    report = one_call.preflight()

    assert report.direct_expected_cost_microusd == 1_296
    assert report.breakdown[0]["reservation_per_attempt_microusd"] == 1
    assert report.retry_inclusive_worst_case_microusd == 2_592


def test_given_a_higher_cached_input_price_when_preflighting_then_the_bound_is_conservative() -> None:
    configuration = CostConfiguration(
        provider_pricing=(
            pricing(input_rate="0.000001", cached_rate="0.002", output_rate="0"),
            pricing("deepseek", input_rate="0.000001", cached_rate="0.002", output_rate="0"),
        ),
        token_bounds={phase: TokenBounds(input_tokens=1, output_tokens=0) for phase in PHASE_BOUNDS},
        planned_calls=fixed_task3_call_plan(("openai", "deepseek")),
        approved_cap_usd=Decimal("1.00"),
        contingency_rate=Decimal("0"),
        max_attempts_per_api_call=2,
    )

    report = configuration.preflight()

    assert report.direct_expected_cost_microusd == 2_592
    assert report.breakdown[0]["reservation_per_attempt_microusd"] == 2


def test_given_decimal_boundary_rates_when_preflighting_then_micro_usd_is_exact_integer_arithmetic() -> None:
    rate = Decimal("0.001000001")
    configuration = CostConfiguration(
        provider_pricing=(
            pricing(input_rate=str(rate), cached_rate="0", output_rate=str(rate)),
            pricing("deepseek", input_rate=str(rate), cached_rate="0", output_rate=str(rate)),
        ),
        token_bounds={phase: TokenBounds(input_tokens=1, output_tokens=0) for phase in PHASE_BOUNDS},
        planned_calls=fixed_task3_call_plan(("openai", "deepseek")),
        approved_cap_usd=Decimal("1.00"),
        contingency_rate=Decimal("0.25"),
        max_attempts_per_api_call=2,
    )

    report = configuration.preflight()

    assert report.direct_expected_cost_microusd == 2_592
    assert report.retry_inclusive_worst_case_microusd == 5_184
    assert report.contingency_reserve_microusd == 648
    assert type(report.worst_case_reserved_microusd) is int


def test_given_frozen_configuration_when_mutation_is_attempted_then_it_is_rejected() -> None:
    configuration = config()

    with pytest.raises((AttributeError, TypeError, ValueError)):
        configuration.approved_cap_usd = Decimal("2.00")  # type: ignore[misc]
    with pytest.raises(TypeError):
        configuration.token_bounds["judge"] = TokenBounds(1, 1)  # type: ignore[index]
    with pytest.raises(TypeError):
        ProviderPricing(
            provider="openai",
            model="openai-model",
            model_version="openai-snapshot",
            pricing_snapshot_date="2026-09-02",
            pricing_source_ref="source",
            input_usd_per_1k=0.1,  # type: ignore[arg-type]
            cached_input_usd_per_1k=Decimal("0.1"),
            output_usd_per_1k=Decimal("0.1"),
        )


def test_given_a_response_when_reserved_and_reconciled_then_unused_reservation_is_explicitly_released(
    tmp_path: Path,
) -> None:
    configuration = config(
        max_attempts=2,
        contingency="0",
    )
    ledger = CostLedger(tmp_path / "cost-ledger.jsonl", configuration)

    reservation = ledger.reserve_attempt(
        call_id="call-1",
        provider="openai",
        model="openai-model",
        model_version="openai-snapshot",
        phase="T1",
    )
    reconciliation = ledger.reconcile_response(
        reservation,
        {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
    )

    assert reservation.reserved_microusd == 1
    assert reconciliation.actual_cost_microusd == 1
    assert reconciliation.released_microusd == 0
    events = [json.loads(line) for line in (tmp_path / "cost-ledger.jsonl").read_text().splitlines()]
    assert [event["event_type"] for event in events] == ["preflight", "reservation", "reconciliation"]
    assert events[-1]["released_microusd"] == 0
    assert ledger.ledger_head_hash == events[-1]["event_hash"]


def test_given_a_secret_like_call_id_when_reserved_then_only_a_stable_digest_is_logged(
    tmp_path: Path,
) -> None:
    configuration = config(contingency="0")
    path = tmp_path / "redacted-call-id.jsonl"
    ledger = CostLedger(path, configuration)
    raw_call_id = "call_" + ("a" * 64)

    reservation = ledger.reserve_attempt(
        call_id=raw_call_id,
        provider="openai",
        model="openai-model",
        model_version="openai-snapshot",
        phase="judge",
    )

    assert reservation.call_id.startswith("call_")
    assert reservation.call_id != raw_call_id
    assert raw_call_id not in path.read_text()




def test_given_under_bound_usage_when_reconciled_then_release_is_recorded(tmp_path: Path) -> None:
    configuration = config(
        providers=(pricing(input_rate="0.001", output_rate="0.001"),),
        bounds={"judge": TokenBounds(input_tokens=10, output_tokens=10)},
        contingency="0",
        max_attempts=2,
    )
    ledger = CostLedger(tmp_path / "ledger.jsonl", configuration)
    reservation = ledger.reserve_attempt(
        call_id="call-1",
        provider="openai",
        model="openai-model",
        model_version="openai-snapshot",
        phase="judge",
    )

    result = ledger.reconcile_response(
        reservation,
        {"input_tokens": 1, "output_tokens": 1},
    )

    assert result.released_microusd == reservation.reserved_microusd - result.actual_cost_microusd
    assert result.released_microusd > 0
    assert ledger.report()["released_microusd"] == result.released_microusd


@pytest.mark.parametrize(
    ("usage", "reason"),
    [
        (None, "missing_usage"),
        ({"input_tokens": "10", "output_tokens": 1}, "malformed_usage"),
        ({"input_tokens": -1, "output_tokens": 1}, "malformed_usage"),
        ({"input_tokens": 11, "output_tokens": 1}, "token_bounds_exceeded"),
        ({"input_tokens": 1, "output_tokens": 1, "total_tokens": 99}, "malformed_usage"),
        ({"input_tokens": 1, "output_tokens": 1, "reasoning_tokens": 1.0}, "malformed_usage"),
        ({"input_tokens": 1, "output_tokens": 1, "reasoning_tokens": -1}, "malformed_usage"),
        ({"input_tokens": 1, "output_tokens": 1, "reasoning_tokens": True}, "malformed_usage"),
        ({"input_tokens": 1, "output_tokens": 1, "reasoning_tokens": 11}, "token_bounds_exceeded"),
        ({"input_tokens": 1, "prompt_tokens": True, "output_tokens": 1}, "malformed_usage"),
        ({"input_tokens": 1, "prompt_tokens": 1.0, "output_tokens": 1}, "malformed_usage"),
        ({"input_tokens": 1, "prompt_tokens": "1", "output_tokens": 1}, "malformed_usage"),
        ({"input_tokens": 1, "output_tokens": 1, "completion_tokens": True}, "malformed_usage"),
        ({"input_tokens": 1, "output_tokens": 1, "completion_tokens": 1.0}, "malformed_usage"),
        ({"input_tokens": 1, "output_tokens": 1, "completion_tokens": "1"}, "malformed_usage"),
    ],
)
def test_given_unverifiable_usage_when_reconciled_then_the_ledger_stops_cost_unverified(
    tmp_path: Path, usage: object, reason: str
) -> None:
    configuration = config(
        bounds={"judge": TokenBounds(input_tokens=10, output_tokens=10)},
        contingency="0",
        max_attempts=2,
    )
    ledger = CostLedger(tmp_path / "ledger.jsonl", configuration)
    reservation = ledger.reserve_attempt(
        call_id="call-1",
        provider="openai",
        model="openai-model",
        model_version="openai-snapshot",
        phase="judge",
    )

    with pytest.raises(CostUnverifiedError):
        ledger.reconcile_response(reservation, usage)  # type: ignore[arg-type]

    assert ledger.report()["budget_status"] == "stopped_cost_unverified"
    assert ledger.report()["stop_reason"] == reason
    with pytest.raises(CostUnverifiedError):
        ledger.reserve_attempt(
            call_id="call-2",
            provider="openai",
            model="openai-model",
            model_version="openai-snapshot",
            phase="judge",
        )
    with pytest.raises(CostUnverifiedError):
        ledger.reconcile_response(reservation, {"input_tokens": 1, "output_tokens": 1})


def test_given_missing_price_or_identity_mismatch_when_reserving_then_no_provider_call_is_allowed(
    tmp_path: Path,
) -> None:
    missing_price = config(
        providers=(
            ProviderPricing(
                provider="openai",
                model="openai-model",
                model_version="openai-snapshot",
                pricing_snapshot_date="2026-09-02",
                pricing_source_ref="source",
                input_usd_per_1k=None,
                cached_input_usd_per_1k=Decimal("0.1"),
                output_usd_per_1k=Decimal("0.1"),
            ),
        ),
        contingency="0",
    )
    missing_ledger = CostLedger(tmp_path / "missing.jsonl", missing_price)
    with pytest.raises(CostUnverifiedError):
        missing_ledger.reserve_attempt(
            call_id="call-1",
            provider="openai",
            model="openai-model",
            model_version="openai-snapshot",
            phase="judge",
        )
    assert missing_ledger.report()["stop_reason"] == "missing_price"

    mismatch_ledger = CostLedger(tmp_path / "mismatch.jsonl", config())
    with pytest.raises(CostUnverifiedError):
        mismatch_ledger.reserve_attempt(
            call_id="call-1",
            provider="openai",
            model="wrong-model",
            model_version="openai-snapshot",
            phase="judge",
        )
    assert mismatch_ledger.report()["stop_reason"] == "provider_model_pricing_mismatch"


def test_given_provider_object_model_mismatch_when_wrapped_then_no_provider_call_is_allowed(
    tmp_path: Path,
) -> None:
    configuration = config(
        contingency="0",
        max_attempts=2,
    )

    class MisconfiguredProvider(RecordingProvider):
        model = "wrong-model"

    provider = MisconfiguredProvider()
    ledger = CostLedger(tmp_path / "provider-mismatch.jsonl", configuration)
    wrapped = budgeted_provider(provider, ledger)

    with pytest.raises(CostUnverifiedError):
        wrapped.complete(request(), call_id="call-1", phase="judge")

    assert provider.calls == 0
    assert ledger.report()["stop_reason"] == "provider_model_pricing_mismatch"


def test_given_provider_error_with_usage_when_wrapped_then_it_reconciles_and_records_safe_class(
    tmp_path: Path,
) -> None:
    configuration = config(
        contingency="0",
        max_attempts=2,
    )

    class FailsOnceProvider(RecordingProvider):
        def __init__(self) -> None:
            super().__init__()
            self.calls = 0

        def complete(self, request: ProviderRequest) -> str:
            self.calls += 1
            self.last_call_metadata = {
                "usage": {"input_tokens": 1, "output_tokens": 1},
                "response_model": "openai-model",
            }
            if self.calls == 1:
                raise RuntimeError("private provider error")
            return '{"ok":true}'

    path = tmp_path / "provider-retry.jsonl"
    provider = FailsOnceProvider()
    ledger = CostLedger(path, configuration)
    wrapped = budgeted_provider(provider, ledger)

    with pytest.raises(RuntimeError):
        wrapped.complete(request(), call_id="call-1", phase="judge")
    assert wrapped.complete(request(), call_id="call-1", phase="judge") == '{"ok":true}'

    events = [json.loads(line) for line in path.read_text().splitlines()]
    assert events[2]["outcome"] == "provider_error"
    assert events[2]["error_class"] == "RuntimeError"
    assert "private provider error" not in path.read_text()


def test_given_one_reconciled_attempt_when_retrying_then_only_the_single_retry_is_allowed(
    tmp_path: Path,
) -> None:
    configuration = config(
        contingency="0",
        max_attempts=2,
    )
    ledger = CostLedger(tmp_path / "retry.jsonl", configuration)
    first = ledger.reserve_attempt(
        call_id="call-1",
        provider="openai",
        model="openai-model",
        model_version="openai-snapshot",
        phase="judge",
    )
    ledger.reconcile_response(first, {"input_tokens": 1, "output_tokens": 1})
    second = ledger.reserve_attempt(
        call_id="call-1",
        provider="openai",
        model="openai-model",
        model_version="openai-snapshot",
        phase="judge",
    )
    ledger.reconcile_response(second, {"input_tokens": 1, "output_tokens": 1})

    with pytest.raises(CostUnverifiedError):
        ledger.reserve_attempt(
            call_id="call-1",
            provider="openai",
            model="openai-model",
            model_version="openai-snapshot",
            phase="judge",
        )
    assert ledger.report()["stop_reason"] == "attempt_policy_exceeded"


def test_given_an_over_cap_fixed_plan_when_ledger_is_created_then_budget_hard_stops_before_provider_call(
    tmp_path: Path,
) -> None:
    configuration = config(
        providers=(
            pricing(input_rate="0.001", output_rate="0.001"),
            pricing("deepseek", input_rate="0.001", output_rate="0.001"),
        ),
        cap="0.000001",
        contingency="0",
        max_attempts=2,
    )
    provider = RecordingProvider()
    ledger = CostLedger(tmp_path / "budget.jsonl", configuration)
    wrapped = budgeted_provider(provider, ledger)

    with pytest.raises(BudgetExhaustedError):
        wrapped.complete(request(), call_id="call-1", phase="judge")

    assert provider.calls == 0
    assert ledger.report()["budget_status"] == "stopped_budget_exhausted"
    with pytest.raises(BudgetExhaustedError):
        ledger.reconcile_response("call-1", {"input_tokens": 1, "output_tokens": 1})


def test_given_same_events_when_written_twice_then_hash_chain_and_serialization_are_deterministic(
    tmp_path: Path,
) -> None:
    configuration = config(
        contingency="0",
        max_attempts=2,
    )
    first = CostLedger(tmp_path / "first.jsonl", configuration)
    first_reservation = first.reserve_attempt(
        call_id="call-1",
        provider="openai",
        model="openai-model",
        model_version="openai-snapshot",
        phase="judge",
    )
    first.reconcile_response(first_reservation, {"input_tokens": 1, "output_tokens": 1})

    second = CostLedger(tmp_path / "second.jsonl", configuration)
    second_reservation = second.reserve_attempt(
        call_id="call-1",
        provider="openai",
        model="openai-model",
        model_version="openai-snapshot",
        phase="judge",
    )
    second.reconcile_response(second_reservation, {"input_tokens": 1, "output_tokens": 1})

    assert first.ledger_head_hash == second.ledger_head_hash
    assert (tmp_path / "first.jsonl").read_bytes() == (tmp_path / "second.jsonl").read_bytes()
    events = [json.loads(line) for line in (tmp_path / "first.jsonl").read_text().splitlines()]
    assert [event["sequence"] for event in events] == [1, 2, 3]
    assert events[0]["prev_event_hash"] == "0" * 64
    assert all(len(event["event_hash"]) == 64 for event in events)


def test_given_existing_ledger_when_new_events_are_appended_then_original_lines_are_preserved(
    tmp_path: Path,
) -> None:
    path = tmp_path / "append-only.jsonl"
    configuration = config(
        contingency="0",
        max_attempts=2,
    )
    first = CostLedger(path, configuration)
    reservation = first.reserve_attempt(
        call_id="call-1",
        provider="openai",
        model="openai-model",
        model_version="openai-snapshot",
        phase="judge",
    )
    first.reconcile_response(reservation, {"input_tokens": 1, "output_tokens": 1})
    original_lines = path.read_bytes().splitlines()

    resumed = CostLedger(path, configuration)
    reservation = resumed.reserve_attempt(
        call_id="call-2",
        provider="openai",
        model="openai-model",
        model_version="openai-snapshot",
        phase="judge",
    )
    resumed.reconcile_response(reservation, {"input_tokens": 1, "output_tokens": 1})

    lines = path.read_bytes().splitlines()
    assert lines[: len(original_lines)] == original_lines
    assert len(lines) == 5
    assert [json.loads(line)["sequence"] for line in lines] == [1, 2, 3, 4, 5]


def test_ledger_hash_mismatch_is_rejected_without_echoing_ledger_contents(tmp_path: Path) -> None:
    path = tmp_path / "tampered.jsonl"
    configuration = config(
        contingency="0",
        max_attempts=2,
    )
    ledger = CostLedger(path, configuration)
    reservation = ledger.reserve_attempt(
        call_id="call-1",
        provider="openai",
        model="openai-model",
        model_version="openai-snapshot",
        phase="judge",
    )
    ledger.reconcile_response(reservation, {"input_tokens": 1, "output_tokens": 1})
    path.write_text(path.read_text().replace('"actual_cost_microusd":1', '"actual_cost_microusd":2'))

    with pytest.raises(CostUnverifiedError, match="ledger"):
        CostLedger(path, configuration)

    text = path.read_text()
    assert "private prompt" not in text
    assert "private requirement" not in text


def _rewrite_last_event(path: Path, **changes: object) -> None:
    events = [json.loads(line) for line in path.read_text().splitlines()]
    events[-1].update(changes)
    unsigned = dict(events[-1])
    unsigned.pop("event_hash")
    events[-1]["event_hash"] = CostLedger._hash_event(unsigned)
    path.write_text(
        "\n".join(
            json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            for event in events
        )
        + "\n"
    )


@pytest.mark.parametrize("bad_amount", [1.5, True, "1", "1.0", -1])
def test_given_signed_replay_with_non_integer_amount_when_opened_then_it_fails_closed(
    tmp_path: Path, bad_amount: object
) -> None:
    configuration = config(contingency="0")
    path = tmp_path / "bad-amount.jsonl"
    ledger = CostLedger(path, configuration)
    reservation = ledger.reserve_attempt(
        call_id="call-1",
        provider="openai",
        model="openai-model",
        model_version="openai-snapshot",
        phase="judge",
    )
    ledger.reconcile_response(reservation, {"input_tokens": 1, "output_tokens": 1})
    _rewrite_last_event(path, actual_cost_microusd=bad_amount)

    with pytest.raises(CostUnverifiedError):
        CostLedger(path, configuration)


def test_given_signed_replay_with_unknown_event_type_when_opened_then_it_fails_closed(
    tmp_path: Path,
) -> None:
    configuration = config(contingency="0")
    path = tmp_path / "unknown-event.jsonl"
    ledger = CostLedger(path, configuration)
    reservation = ledger.reserve_attempt(
        call_id="call-1",
        provider="openai",
        model="openai-model",
        model_version="openai-snapshot",
        phase="judge",
    )
    ledger.reconcile_response(reservation, {"input_tokens": 1, "output_tokens": 1})
    _rewrite_last_event(path, event_type="unknown_event")

    with pytest.raises(CostUnverifiedError):
        CostLedger(path, configuration)


def test_given_ambiguous_in_flight_response_when_wrapped_then_no_retry_is_possible(tmp_path: Path) -> None:
    configuration = config(
        contingency="0",
        max_attempts=2,
    )

    class AmbiguousProvider(RecordingProvider):
        def __init__(self) -> None:
            super().__init__({})

        def complete(self, request: ProviderRequest) -> str:
            self.calls += 1
            raise TimeoutError("secret response and prompt must not be copied")

    provider = AmbiguousProvider()
    ledger = CostLedger(tmp_path / "ambiguous.jsonl", configuration)
    wrapped = budgeted_provider(provider, ledger)

    with pytest.raises(AmbiguousInFlightError):
        wrapped.complete(request(), call_id="call-1", phase="judge")
    with pytest.raises(CostUnverifiedError):
        wrapped.complete(request(), call_id="call-1", phase="judge")

    assert provider.calls == 1
    assert ledger.report()["budget_status"] == "stopped_cost_unverified"
    assert ledger.report()["stop_reason"] == "ambiguous_in_flight"
    text = (tmp_path / "ambiguous.jsonl").read_text()
    assert "secret response" not in text
    assert "private prompt" not in text


def test_given_stale_provider_metadata_when_provider_raises_then_it_is_not_reconciled(
    tmp_path: Path,
) -> None:
    configuration = config(contingency="0")

    class StaleMetadataProvider(RecordingProvider):
        def __init__(self) -> None:
            super().__init__(
                {
                    "usage": {"input_tokens": 1, "output_tokens": 1},
                    "response_model": "openai-model",
                    "private": "stale secret",
                }
            )

        def complete(self, request: ProviderRequest) -> str:
            self.calls += 1
            raise TimeoutError("provider timeout")

    path = tmp_path / "stale-metadata.jsonl"
    provider = StaleMetadataProvider()
    wrapped = budgeted_provider(provider, CostLedger(path, configuration))

    with pytest.raises(AmbiguousInFlightError):
        wrapped.complete(request(), call_id="call-1", phase="judge")
    with pytest.raises(CostUnverifiedError):
        wrapped.complete(request(), call_id="call-1", phase="judge")

    assert provider.calls == 1
    assert "stale secret" not in path.read_text()


def test_given_a_reconciled_ledger_when_reopened_then_state_and_report_are_identical(
    tmp_path: Path,
) -> None:
    configuration = config(contingency="0")
    path = tmp_path / "replay-state.jsonl"
    live = CostLedger(path, configuration)
    reservation = live.reserve_attempt(
        call_id="call-1",
        provider="openai",
        model="openai-model",
        model_version="openai-snapshot",
        phase="judge",
    )
    live.reconcile_response(reservation, {"input_tokens": 1, "output_tokens": 1})
    live_report = live.report()

    reopened = CostLedger(path, configuration)

    assert reopened.status == live.status == "running"
    assert reopened.report() == live_report


def test_given_unreconciled_reservation_when_ledger_is_reopened_then_it_stops_as_ambiguous(
    tmp_path: Path,
) -> None:
    configuration = config(
        contingency="0",
        max_attempts=2,
    )
    path = tmp_path / "interrupted.jsonl"
    ledger = CostLedger(path, configuration)
    ledger.reserve_attempt(
        call_id="call-1",
        provider="openai",
        model="openai-model",
        model_version="openai-snapshot",
        phase="judge",
    )

    resumed = CostLedger(path, configuration)

    assert resumed.status == "stopped_cost_unverified"
    assert resumed.report()["stop_reason"] == "ambiguous_in_flight"
    with pytest.raises(CostUnverifiedError):
        resumed.reserve_attempt(
            call_id="call-2",
            provider="openai",
            model="openai-model",
            model_version="openai-snapshot",
            phase="judge",
        )


def test_given_unsafe_reconciliation_outcome_when_reconciled_then_it_stops_without_logging_it(
    tmp_path: Path,
) -> None:
    configuration = config(
        contingency="0",
        max_attempts=2,
    )
    path = tmp_path / "unsafe-outcome.jsonl"
    ledger = CostLedger(path, configuration)
    reservation = ledger.reserve_attempt(
        call_id="call-1",
        provider="openai",
        model="openai-model",
        model_version="openai-snapshot",
        phase="judge",
    )

    with pytest.raises(CostUnverifiedError):
        ledger.reconcile_response(
            reservation,
            {"input_tokens": 1, "output_tokens": 1},
            outcome="private provider error and prompt",
        )

    assert ledger.report()["stop_reason"] == "invalid_reconciliation_outcome"
    assert "private provider error and prompt" not in path.read_text()
