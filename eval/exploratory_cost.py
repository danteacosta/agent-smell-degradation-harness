"""Fail-closed cost accounting for the exploratory LLM-only pre-pilot.

This module is deliberately independent of provider construction.  Providers
may return raw responses to their caller, but the ledger accepts only bounded
usage metadata and writes only integer micro-USD and redacted identity facts.
The intended writer model is one process/thread owning one ledger path.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from pathlib import Path
from types import MappingProxyType
from typing import Any


SCHEMA_VERSION = "exploratory-cost-ledger/v1"
MICRO_USD_PER_USD = 1_000_000
FIXED_TASK3_PROVIDER_API_CALLS = 1_296
FIXED_TASK3_MAX_ATTEMPTS = 2
DEFAULT_APPROVED_CAP_USD = Decimal("1.00")
DEFAULT_CONTINGENCY_RATE = Decimal("0.25")
ZERO_HASH = "0" * 64

STOPPED_COST_UNVERIFIED = "stopped_cost_unverified"
STOPPED_BUDGET_EXHAUSTED = "stopped_budget_exhausted"

_PHASE_ALIASES = {
    "T1": "generation.T1",
    "generation.T1": "generation.T1",
    "T2": "generation.T2",
    "generation.T2": "generation.T2",
    "artifact": "generation.artifact",
    "generation.artifact": "generation.artifact",
    "judge": "judge",
}
_FIXED_TASK3_PHASE_COUNTS = {
    "generation.T1": 120,
    "generation.T2": 120,
    "generation.artifact": 120,
    "judge": 288,
}
_USAGE_FIELDS = frozenset(
    {
        "input_tokens",
        "output_tokens",
        "prompt_tokens",
        "completion_tokens",
        "cached_tokens",
        "total_tokens",
        "reasoning_tokens",
    }
)
_NESTED_TOKEN_DETAIL_FIELDS = frozenset(
    {
        "prompt_tokens_details",
        "input_tokens_details",
        "prompt_token_details",
        "completion_tokens_details",
        "output_tokens_details",
        "completion_token_details",
        "output_token_details",
    }
)
_USAGE_FIELDS_WITH_DETAILS = _USAGE_FIELDS | _NESTED_TOKEN_DETAIL_FIELDS
_CACHED_TOKEN_DETAIL_FIELDS = frozenset(
    {"prompt_tokens_details", "input_tokens_details", "prompt_token_details"}
)
_REASONING_TOKEN_DETAIL_FIELDS = frozenset(
    {
        "completion_tokens_details",
        "output_tokens_details",
        "completion_token_details",
        "output_token_details",
    }
)
_SAFE_OUTCOMES = frozenset({"success", "provider_error"})
_EVENT_TYPES = frozenset(
    {
        "preflight",
        "reservation",
        "reconciliation",
        STOPPED_COST_UNVERIFIED,
        STOPPED_BUDGET_EXHAUSTED,
    }
)
_CALL_ID_PREFIX = "call_"
_MAX_LEDGER_EVENTS = (
    1 + FIXED_TASK3_PROVIDER_API_CALLS * FIXED_TASK3_MAX_ATTEMPTS * 2 + 1
)
_COMMON_EVENT_FIELDS = frozenset(
    {"schema_version", "sequence", "event_type", "prev_event_hash", "event_hash"}
)
_PREFLIGHT_EVENT_FIELDS = _COMMON_EVENT_FIELDS | {
    "configuration_sha256",
    "preflight_status",
    "budget_status",
    "stop_reason",
    "planned_provider_api_calls",
    "max_attempts_per_api_call",
    "direct_expected_cost_microusd",
    "retry_inclusive_worst_case_microusd",
    "contingency_reserve_microusd",
    "worst_case_reserved_microusd",
    "approved_cap_microusd",
    "unused_headroom_microusd",
}
_RESERVATION_EVENT_FIELDS = _COMMON_EVENT_FIELDS | {
    "call_id",
    "provider",
    "model",
    "model_version",
    "phase",
    "attempt",
    "input_token_bound",
    "output_token_bound",
    "input_usd_per_1k",
    "cached_input_usd_per_1k",
    "output_usd_per_1k",
    "pricing_snapshot_date",
    "pricing_source_ref",
    "reserved_microusd",
}
_RECONCILIATION_BASE_FIELDS = _COMMON_EVENT_FIELDS | {
    "status",
    "call_id",
    "phase",
    "attempt",
    "reserved_microusd",
    "released_microusd",
}
_UNVERIFIED_RECONCILIATION_EVENT_FIELDS = _RECONCILIATION_BASE_FIELDS | {"stop_reason"}
_RECONCILED_EVENT_FIELDS = _RECONCILIATION_BASE_FIELDS | {
    "input_tokens",
    "output_tokens",
    "cached_tokens",
    "total_tokens",
    "actual_cost_microusd",
    "outcome",
}
_STOP_EVENT_FIELDS = _COMMON_EVENT_FIELDS | {"budget_status", "stop_reason"}
_COST_UNVERIFIED_STOP_REASONS = frozenset(
    {
        "ambiguous_in_flight",
        "attempt_policy_exceeded",
        "call_identity_mismatch",
        "fixed_task3_plan_mismatch",
        "invalid_call_identity",
        "invalid_reconciliation_outcome",
        "ledger_mismatch",
        "malformed_usage",
        "metadata_access_failed",
        "metadata_reset_failed",
        "missing_price",
        "missing_token_bound",
        "missing_usage",
        "provider_model_pricing_mismatch",
        "reservation_already_in_flight",
        "token_bounds_exceeded",
    }
)
_BUDGET_EXHAUSTED_STOP_REASONS = frozenset(
    {
        "attempt_reservation_exceeds_remaining_cap",
        "fixed_plan_exhausted",
        "worst_case_reserved_cost_exceeds_approved_cap",
    }
)
_STOP_REASONS_BY_STATUS = {
    STOPPED_COST_UNVERIFIED: _COST_UNVERIFIED_STOP_REASONS,
    STOPPED_BUDGET_EXHAUSTED: _BUDGET_EXHAUSTED_STOP_REASONS,
}
_STOP_REASONS = frozenset().union(*_STOP_REASONS_BY_STATUS.values())
_RECONCILIATION_REASONS_BY_STATUS = {
    "cost_unverified": frozenset(
        {
            "invalid_reconciliation_outcome",
            "ledger_mismatch",
            "malformed_usage",
            "metadata_access_failed",
            "missing_usage",
            "provider_model_pricing_mismatch",
            "token_bounds_exceeded",
        }
    ),
    "ambiguous_in_flight": frozenset({"ambiguous_in_flight"}),
}
_RECONCILIATION_REASONS = frozenset().union(*_RECONCILIATION_REASONS_BY_STATUS.values())


class CostLedgerError(ValueError):
    """Raised for invalid cost configuration or corrupted ledger state."""


class CostUnverifiedError(RuntimeError):
    """Raised when a charge cannot be reconciled safely."""


class BudgetExhaustedError(RuntimeError):
    """Raised before an attempt that cannot fit in the approved cap."""


class AmbiguousInFlightError(CostUnverifiedError):
    """Raised when a provider may have processed an attempt without evidence."""


class _UsageProblem(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason


class _MetadataProblem(Exception):
    """Raised when provider metadata cannot be safely read or copied."""


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _safe_text(value: Any, field_name: str, *, max_length: int = 256) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CostLedgerError(f"{field_name} must be a non-empty string")
    result = value.strip()
    if len(result) > max_length or "\n" in result or "\r" in result:
        raise CostLedgerError(f"{field_name} is invalid")
    return result


def _redacted_call_id(value: Any) -> str:
    """Return a stable ledger identifier without persisting caller text."""

    safe = _safe_text(value, "call_id")
    digest = hashlib.sha256(("exploratory-cost-call/v1\0" + safe).encode("utf-8")).hexdigest()
    return _CALL_ID_PREFIX + digest


def _is_redacted_call_id(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == len(_CALL_ID_PREFIX) + 64
        and value.startswith(_CALL_ID_PREFIX)
        and all(character in "0123456789abcdef" for character in value[len(_CALL_ID_PREFIX) :])
    )


def _contains_float(value: Any) -> bool:
    if type(value) is float:
        return True
    if isinstance(value, Mapping):
        return any(_contains_float(key) or _contains_float(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False


def _validate_nested_token_metadata(value: Any, *, seen: set[int] | None = None) -> None:
    """Validate token-count values anywhere in provider metadata without coercion."""

    visited = seen if seen is not None else set()
    try:
        if isinstance(value, Mapping):
            identity = id(value)
            if identity in visited:
                return
            visited.add(identity)
            for key in value:
                nested = value[key]
                if key in _USAGE_FIELDS and (
                    type(nested) is not int or nested < 0
                ):
                    raise _MetadataProblem("nested token metadata is malformed")
                _validate_nested_token_metadata(nested, seen=visited)
        elif isinstance(value, (list, tuple)):
            identity = id(value)
            if identity in visited:
                return
            visited.add(identity)
            for nested in value:
                _validate_nested_token_metadata(nested, seen=visited)
    except _MetadataProblem:
        raise
    except Exception as error:
        raise _MetadataProblem("nested token metadata access failed") from error


def _event_int(event: Mapping[str, Any], field_name: str, *, maximum: int | None = None) -> int:
    value = event.get(field_name)
    if type(value) is not int or value < 0 or (maximum is not None and value > maximum):
        raise CostUnverifiedError("ledger validation failed")
    return value


def _event_text(event: Mapping[str, Any], field_name: str) -> str:
    value = event.get(field_name)
    if type(value) is not str or not value:
        raise CostUnverifiedError("ledger validation failed")
    return value


def _event_optional_text(event: Mapping[str, Any], field_name: str) -> str | None:
    value = event.get(field_name)
    if value is None:
        return None
    if type(value) is not str or not value:
        raise CostUnverifiedError("ledger validation failed")
    return value


def _validate_event_schema(event: Mapping[str, Any]) -> None:
    event_type = event.get("event_type")
    if event_type == "preflight":
        allowed = _PREFLIGHT_EVENT_FIELDS
        budget_status = event.get("budget_status")
        if budget_status == "ready":
            if event.get("stop_reason") is not None:
                raise CostUnverifiedError("ledger validation failed")
        elif budget_status in _STOP_REASONS_BY_STATUS:
            _event_stop_reason(event, expected_status=budget_status)
        else:
            raise CostUnverifiedError("ledger validation failed")
    elif event_type == "reservation":
        allowed = _RESERVATION_EVENT_FIELDS
    elif event_type == "reconciliation":
        status = event.get("status")
        if status in _RECONCILIATION_REASONS_BY_STATUS:
            allowed = _UNVERIFIED_RECONCILIATION_EVENT_FIELDS
            _event_reconciliation_reason(event)
        elif status == "reconciled":
            allowed_sets = {
                _RECONCILED_EVENT_FIELDS,
                _RECONCILED_EVENT_FIELDS | {"reasoning_tokens"},
                _RECONCILED_EVENT_FIELDS | {"error_class"},
                _RECONCILED_EVENT_FIELDS | {"reasoning_tokens", "error_class"},
            }
            if set(event) not in allowed_sets:
                raise CostUnverifiedError("ledger validation failed")
            return
        else:
            raise CostUnverifiedError("ledger validation failed")
    elif event_type in {STOPPED_COST_UNVERIFIED, STOPPED_BUDGET_EXHAUSTED}:
        allowed = _STOP_EVENT_FIELDS
        _event_stop_reason(event, expected_status=event_type)
    else:
        raise CostUnverifiedError("ledger validation failed")
    if set(event) != allowed:
        raise CostUnverifiedError("ledger validation failed")


def _event_stop_reason(
    event: Mapping[str, Any], *, expected_status: str | None = None
) -> str:
    reason = _event_text(event, "stop_reason")
    allowed = _STOP_REASONS if expected_status is None else _STOP_REASONS_BY_STATUS.get(expected_status)
    if allowed is None or reason not in allowed:
        raise CostUnverifiedError("ledger validation failed")
    return reason


def _event_reconciliation_reason(event: Mapping[str, Any]) -> str:
    status = event.get("status")
    reason = _event_stop_reason(event)
    allowed = _RECONCILIATION_REASONS_BY_STATUS.get(status)
    if allowed is None or reason not in allowed:
        raise CostUnverifiedError("ledger validation failed")
    return reason


def _decimal(value: Any, field_name: str, *, allow_none: bool = False) -> Decimal | None:
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or isinstance(value, float):
        raise TypeError(f"{field_name} must use Decimal, integer, or decimal text")
    if not isinstance(value, (Decimal, int, str)):
        raise TypeError(f"{field_name} must use Decimal, integer, or decimal text")
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"{field_name} must be a finite decimal") from error
    if not parsed.is_finite() or parsed < 0:
        raise ValueError(f"{field_name} must be a finite non-negative decimal")
    return parsed


def _micro_usd(value: Decimal, field_name: str) -> int:
    scaled = value * MICRO_USD_PER_USD
    if scaled != scaled.to_integral_value():
        raise ValueError(f"{field_name} must have no more than six decimal places")
    return int(scaled)


def _usd_text(microusd: int | None) -> str | None:
    if microusd is None:
        return None
    return format(Decimal(microusd) / MICRO_USD_PER_USD, "f")


def _canonical_phase(value: Any) -> str:
    if not isinstance(value, str) or value.strip() not in _PHASE_ALIASES:
        raise CostLedgerError("phase is not part of the frozen exploratory call plan")
    return _PHASE_ALIASES[value.strip()]


def _safe_error_class(value: Any) -> str | None:
    if value is None:
        return None
    if (
        type(value) is not str
        or len(value) > 64
        or not value.isascii()
        or not value.isidentifier()
    ):
        raise _UsageProblem("invalid_reconciliation_outcome")
    return value


@dataclass(frozen=True)
class TokenBounds:
    """Maximum input and output tokens for one provider attempt."""

    input_tokens: int
    output_tokens: int

    def __post_init__(self) -> None:
        for name, value in (
            ("input_tokens", self.input_tokens),
            ("output_tokens", self.output_tokens),
        ):
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")

    def to_dict(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }


@dataclass(frozen=True)
class ProviderPricing:
    """Immutable provider/model and dated per-1K-token price snapshot."""

    provider: str
    model: str
    model_version: str
    pricing_snapshot_date: str
    pricing_source_ref: str
    input_usd_per_1k: Decimal | str | int | None
    cached_input_usd_per_1k: Decimal | str | int | None
    output_usd_per_1k: Decimal | str | int | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", _safe_text(self.provider, "provider"))
        object.__setattr__(self, "model", _safe_text(self.model, "model"))
        object.__setattr__(self, "model_version", _safe_text(self.model_version, "model_version"))
        snapshot_date = _safe_text(self.pricing_snapshot_date, "pricing_snapshot_date")
        try:
            if date.fromisoformat(snapshot_date).isoformat() != snapshot_date:
                raise ValueError
        except ValueError as error:
            raise ValueError("pricing_snapshot_date must be an ISO date") from error
        object.__setattr__(self, "pricing_snapshot_date", snapshot_date)
        object.__setattr__(
            self,
            "pricing_source_ref",
            _safe_text(self.pricing_source_ref, "pricing_source_ref", max_length=1024),
        )
        for name in (
            "input_usd_per_1k",
            "cached_input_usd_per_1k",
            "output_usd_per_1k",
        ):
            object.__setattr__(self, name, _decimal(getattr(self, name), name, allow_none=True))

    @property
    def prices_complete(self) -> bool:
        return all(
            value is not None
            for value in (
                self.input_usd_per_1k,
                self.cached_input_usd_per_1k,
                self.output_usd_per_1k,
            )
        )

    def _cost_microusd(self, input_tokens: int, output_tokens: int, cached_tokens: int) -> int:
        if not self.prices_complete:
            raise _UsageProblem("missing_price")
        assert self.input_usd_per_1k is not None
        assert self.cached_input_usd_per_1k is not None
        assert self.output_usd_per_1k is not None
        uncached_input = input_tokens - cached_tokens
        dollars = (
            Decimal(uncached_input) * self.input_usd_per_1k / 1000
            + Decimal(cached_tokens) * self.cached_input_usd_per_1k / 1000
            + Decimal(output_tokens) * self.output_usd_per_1k / 1000
        )
        return int(
            (dollars * MICRO_USD_PER_USD).to_integral_value(rounding=ROUND_CEILING)
        )

    def reservation_microusd(self, bounds: TokenBounds) -> int:
        """Calculate the conservative reservation for every valid cache split."""

        if not self.prices_complete:
            raise _UsageProblem("missing_price")
        assert self.input_usd_per_1k is not None
        assert self.cached_input_usd_per_1k is not None
        assert self.output_usd_per_1k is not None
        input_rate = max(self.input_usd_per_1k, self.cached_input_usd_per_1k)
        dollars = (
            Decimal(bounds.input_tokens) * input_rate / 1000
            + Decimal(bounds.output_tokens) * self.output_usd_per_1k / 1000
        )
        return int(
            (dollars * MICRO_USD_PER_USD).to_integral_value(rounding=ROUND_CEILING)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "model_version": self.model_version,
            "pricing_snapshot_date": self.pricing_snapshot_date,
            "pricing_source_ref": self.pricing_source_ref,
            "input_usd_per_1k": (
                str(self.input_usd_per_1k) if self.input_usd_per_1k is not None else None
            ),
            "cached_input_usd_per_1k": (
                str(self.cached_input_usd_per_1k)
                if self.cached_input_usd_per_1k is not None
                else None
            ),
            "output_usd_per_1k": (
                str(self.output_usd_per_1k) if self.output_usd_per_1k is not None else None
            ),
        }


PricingSnapshot = ProviderPricing


@dataclass(frozen=True)
class PlannedCall:
    provider: str
    phase: str
    count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", _safe_text(self.provider, "planned call provider"))
        object.__setattr__(self, "phase", _canonical_phase(self.phase))
        if type(self.count) is not int or self.count <= 0:
            raise ValueError("planned call count must be a positive integer")


def fixed_task3_call_plan(provider_names: Iterable[str]) -> tuple[PlannedCall, ...]:
    providers = tuple(_safe_text(value, "provider") for value in provider_names)
    if len(providers) != 2 or len(set(providers)) != 2:
        raise ValueError("Task 3 requires exactly two unique provider slots")
    return tuple(
        PlannedCall(provider=provider, phase=phase, count=count)
        for provider in providers
        for phase, count in _FIXED_TASK3_PHASE_COUNTS.items()
    )


@dataclass(frozen=True)
class CostConfiguration:
    """Frozen pricing, token bounds, call plan, cap, and attempt policy."""

    provider_pricing: tuple[ProviderPricing, ...]
    token_bounds: Mapping[str, TokenBounds | Mapping[str, Any]]
    planned_calls: tuple[PlannedCall, ...] | None = None
    approved_cap_usd: Decimal | str | int = DEFAULT_APPROVED_CAP_USD
    contingency_rate: Decimal | str | int = DEFAULT_CONTINGENCY_RATE
    max_attempts_per_api_call: int = FIXED_TASK3_MAX_ATTEMPTS
    _is_default_task3_plan: bool = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        pricing = tuple(self.provider_pricing)
        if not pricing or any(type(item) is not ProviderPricing for item in pricing):
            raise TypeError("provider_pricing must contain ProviderPricing snapshots")
        providers = tuple(item.provider for item in pricing)
        if len(providers) != 2:
            raise ValueError("Task 3 requires exactly two provider pricing snapshots")
        if len(set(providers)) != len(providers):
            raise ValueError("provider pricing providers must be unique")
        object.__setattr__(self, "provider_pricing", pricing)

        normalized_bounds: dict[str, TokenBounds] = {}
        if isinstance(self.token_bounds, Mapping):
            values = self.token_bounds.items()
        else:
            raise TypeError("token_bounds must be a mapping")
        for raw_phase, raw_bound in values:
            phase = _canonical_phase(raw_phase)
            if isinstance(raw_bound, TokenBounds):
                bound = raw_bound
            elif isinstance(raw_bound, Mapping):
                if set(raw_bound) != {"input_tokens", "output_tokens"}:
                    raise ValueError("token bounds require input_tokens and output_tokens")
                bound = TokenBounds(raw_bound["input_tokens"], raw_bound["output_tokens"])
            else:
                raise TypeError("token bounds must contain TokenBounds values")
            if phase in normalized_bounds:
                raise ValueError("token bounds contain duplicate phase aliases")
            normalized_bounds[phase] = bound
        if set(normalized_bounds) != set(_FIXED_TASK3_PHASE_COUNTS):
            raise ValueError("token_bounds must cover the frozen Task 3 stages exactly")
        object.__setattr__(self, "token_bounds", MappingProxyType(normalized_bounds))

        cap = _decimal(self.approved_cap_usd, "approved_cap_usd")
        contingency = _decimal(self.contingency_rate, "contingency_rate")
        assert cap is not None and contingency is not None
        object.__setattr__(self, "approved_cap_usd", cap)
        object.__setattr__(self, "contingency_rate", contingency)
        if _micro_usd(cap, "approved_cap_usd") <= 0:
            raise ValueError("approved_cap_usd must be positive")
        if cap > DEFAULT_APPROVED_CAP_USD:
            raise ValueError("approved_cap_usd cannot exceed the hard USD 1.00 cap")
        if (
            type(self.max_attempts_per_api_call) is not int
            or self.max_attempts_per_api_call != FIXED_TASK3_MAX_ATTEMPTS
        ):
            raise ValueError("Task 3 max_attempts_per_api_call is fixed at two")

        is_default = self.planned_calls is None
        plan = (
            fixed_task3_call_plan(providers)
            if is_default
            else tuple(self.planned_calls)
        )
        if not plan or any(type(item) is not PlannedCall for item in plan):
            raise TypeError("planned_calls must contain PlannedCall values")
        known_providers = set(providers)
        if any(item.provider not in known_providers for item in plan):
            raise ValueError("planned call provider is not in the frozen pricing snapshot")
        expected_plan = fixed_task3_call_plan(providers)
        actual_plan = {(item.provider, item.phase): item.count for item in plan}
        expected = {(item.provider, item.phase): item.count for item in expected_plan}
        if len(plan) != len(expected_plan) or actual_plan != expected:
            raise ValueError("planned_calls must match the frozen Task 3 plan exactly")
        object.__setattr__(self, "planned_calls", plan)
        object.__setattr__(self, "_is_default_task3_plan", is_default)

    @property
    def approved_cap_microusd(self) -> int:
        return _micro_usd(self.approved_cap_usd, "approved_cap_usd")

    @property
    def planned_provider_api_calls(self) -> int:
        return sum(item.count for item in self.planned_calls or ())

    def pricing_for(self, provider: str) -> ProviderPricing | None:
        return next((item for item in self.provider_pricing if item.provider == provider), None)

    def bounds_for(self, phase: str) -> TokenBounds | None:
        return self.token_bounds.get(_canonical_phase(phase))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "provider_pricing": [item.to_dict() for item in self.provider_pricing],
            "token_bounds": {
                phase: self.token_bounds[phase].to_dict()
                for phase in sorted(self.token_bounds)
            },
            "planned_calls": [
                {"provider": item.provider, "phase": item.phase, "count": item.count}
                for item in sorted(self.planned_calls or (), key=lambda value: (value.provider, value.phase))
            ],
            "approved_cap_usd": str(self.approved_cap_usd),
            "contingency_rate": str(self.contingency_rate),
            "max_attempts_per_api_call": self.max_attempts_per_api_call,
        }

    @property
    def configuration_sha256(self) -> str:
        return hashlib.sha256(_canonical_json(self.to_dict()).encode("utf-8")).hexdigest()

    def preflight(self) -> "PreflightReport":
        return preflight_cost(self)


CostConfig = CostConfiguration


@dataclass(frozen=True)
class PreflightReport:
    passed: bool
    planned_provider_api_calls: int
    max_attempts_per_api_call: int
    direct_expected_cost_microusd: int | None
    retry_inclusive_worst_case_microusd: int | None
    contingency_reserve_microusd: int | None
    worst_case_reserved_microusd: int | None
    approved_cap_microusd: int
    unused_headroom_microusd: int | None
    budget_status: str
    stop_reason: str | None
    breakdown: tuple[dict[str, Any], ...] = ()
    configuration_sha256: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "ready" if self.passed else "preflight_blocked",
            "passed": self.passed,
            "planned_provider_api_calls": self.planned_provider_api_calls,
            "max_attempts_per_api_call": self.max_attempts_per_api_call,
            "direct_expected_cost_microusd": self.direct_expected_cost_microusd,
            "retry_inclusive_worst_case_microusd": self.retry_inclusive_worst_case_microusd,
            "contingency_reserve_microusd": self.contingency_reserve_microusd,
            "worst_case_reserved_microusd": self.worst_case_reserved_microusd,
            "approved_cap_microusd": self.approved_cap_microusd,
            "direct_expected_cost_usd": _usd_text(self.direct_expected_cost_microusd),
            "retry_inclusive_worst_case_usd": _usd_text(self.retry_inclusive_worst_case_microusd),
            "contingency_reserve_usd": _usd_text(self.contingency_reserve_microusd),
            "contingency_cost_within_cap_usd": _usd_text(self.contingency_reserve_microusd),
            "worst_case_reserved_usd": _usd_text(self.worst_case_reserved_microusd),
            "approved_cap_usd": _usd_text(self.approved_cap_microusd),
            "remaining_headroom_microusd": self.unused_headroom_microusd,
            "unused_headroom_microusd": self.unused_headroom_microusd,
            "remaining_headroom_usd": _usd_text(self.unused_headroom_microusd),
            "unused_headroom_usd": _usd_text(self.unused_headroom_microusd),
            "budget_status": self.budget_status,
            "stop_reason": self.stop_reason,
            "breakdown": [dict(item) for item in self.breakdown],
            "configuration_sha256": self.configuration_sha256,
        }

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]


def _blocked_preflight(
    configuration: CostConfiguration,
    *,
    status: str,
    reason: str,
) -> PreflightReport:
    return PreflightReport(
        passed=False,
        planned_provider_api_calls=configuration.planned_provider_api_calls,
        max_attempts_per_api_call=configuration.max_attempts_per_api_call,
        direct_expected_cost_microusd=None,
        retry_inclusive_worst_case_microusd=None,
        contingency_reserve_microusd=None,
        worst_case_reserved_microusd=None,
        approved_cap_microusd=configuration.approved_cap_microusd,
        unused_headroom_microusd=None,
        budget_status=status,
        stop_reason=reason,
        configuration_sha256=configuration.configuration_sha256,
    )


def _fixed_plan_is_valid(configuration: CostConfiguration) -> bool:
    if (
        len(configuration.provider_pricing) != 2
        or configuration.max_attempts_per_api_call != FIXED_TASK3_MAX_ATTEMPTS
    ):
        return False
    expected = {
        (provider, phase): count
        for provider in (item.provider for item in configuration.provider_pricing)
        for phase, count in _FIXED_TASK3_PHASE_COUNTS.items()
    }
    actual = {(item.provider, item.phase): item.count for item in configuration.planned_calls or ()}
    return (
        configuration.planned_provider_api_calls == FIXED_TASK3_PROVIDER_API_CALLS
        and len(actual) == len(expected)
        and actual == expected
        and set(configuration.token_bounds) == set(_FIXED_TASK3_PHASE_COUNTS)
    )


def preflight_cost(configuration: CostConfiguration) -> PreflightReport:
    """Compute the fixed plan's conservative envelope without provider I/O."""

    if not _fixed_plan_is_valid(configuration):
        return _blocked_preflight(
            configuration,
            status=STOPPED_COST_UNVERIFIED,
            reason="fixed_task3_plan_mismatch",
        )
    for pricing in configuration.provider_pricing:
        if not pricing.prices_complete:
            return _blocked_preflight(configuration, status=STOPPED_COST_UNVERIFIED, reason="missing_price")
    breakdown: list[dict[str, Any]] = []
    direct = 0
    for planned in sorted(configuration.planned_calls or (), key=lambda item: (item.provider, item.phase)):
        bounds = configuration.bounds_for(planned.phase)
        pricing = configuration.pricing_for(planned.provider)
        if bounds is None:
            return _blocked_preflight(
                configuration,
                status=STOPPED_COST_UNVERIFIED,
                reason="missing_token_bound",
            )
        assert pricing is not None
        try:
            per_attempt = pricing.reservation_microusd(bounds)
        except _UsageProblem:
            return _blocked_preflight(configuration, status=STOPPED_COST_UNVERIFIED, reason="missing_price")
        line_total = per_attempt * planned.count
        direct += line_total
        breakdown.append(
            {
                "provider": planned.provider,
                "phase": planned.phase,
                "count": planned.count,
                "input_token_bound": bounds.input_tokens,
                "output_token_bound": bounds.output_tokens,
                "reservation_per_attempt_microusd": per_attempt,
                "direct_microusd": line_total,
            }
        )
    retry = direct * configuration.max_attempts_per_api_call
    contingency = int(
        (Decimal(direct) * configuration.contingency_rate).to_integral_value(rounding=ROUND_CEILING)
    )
    envelope = retry + contingency
    headroom = configuration.approved_cap_microusd - envelope
    if envelope > configuration.approved_cap_microusd:
        return PreflightReport(
            passed=False,
            planned_provider_api_calls=configuration.planned_provider_api_calls,
            max_attempts_per_api_call=configuration.max_attempts_per_api_call,
            direct_expected_cost_microusd=direct,
            retry_inclusive_worst_case_microusd=retry,
            contingency_reserve_microusd=contingency,
            worst_case_reserved_microusd=envelope,
            approved_cap_microusd=configuration.approved_cap_microusd,
            unused_headroom_microusd=headroom,
            budget_status=STOPPED_BUDGET_EXHAUSTED,
            stop_reason="worst_case_reserved_cost_exceeds_approved_cap",
            breakdown=tuple(breakdown),
            configuration_sha256=configuration.configuration_sha256,
        )
    return PreflightReport(
        passed=True,
        planned_provider_api_calls=configuration.planned_provider_api_calls,
        max_attempts_per_api_call=configuration.max_attempts_per_api_call,
        direct_expected_cost_microusd=direct,
        retry_inclusive_worst_case_microusd=retry,
        contingency_reserve_microusd=contingency,
        worst_case_reserved_microusd=envelope,
        approved_cap_microusd=configuration.approved_cap_microusd,
        unused_headroom_microusd=headroom,
        budget_status="ready",
        stop_reason=None,
        breakdown=tuple(breakdown),
        configuration_sha256=configuration.configuration_sha256,
    )


@dataclass(frozen=True)
class Reservation:
    call_id: str
    provider: str
    model: str
    model_version: str
    phase: str
    attempt: int
    input_token_bound: int
    output_token_bound: int
    reserved_microusd: int


@dataclass(frozen=True)
class Reconciliation:
    call_id: str
    attempt: int
    actual_cost_microusd: int
    released_microusd: int
    outcome: str = "success"


class CostLedger:
    """Single-writer append-only ledger with a deterministic SHA-256 chain."""

    def __init__(
        self,
        path: str | Path,
        configuration: CostConfiguration,
        *,
        preflight: PreflightReport | None = None,
    ) -> None:
        computed_preflight = configuration.preflight()
        if (
            preflight is not None
            and (type(preflight) is not PreflightReport or preflight != computed_preflight)
        ):
            raise CostLedgerError("preflight does not match immutable configuration")
        self.path = Path(path)
        self.configuration = configuration
        self.preflight = computed_preflight
        self._lock = threading.RLock()
        self._events: list[dict[str, Any]] = []
        self._pending: dict[tuple[str, int], Reservation] = {}
        self._attempts: dict[str, list[Reservation]] = {}
        self._logical_classes: dict[str, tuple[str, str]] = {}
        self._spent_microusd = 0
        self._active_reserved_microusd = 0
        self._released_microusd = 0
        self._contingency_reserved_microusd = (
            self.preflight.contingency_reserve_microusd or 0
        ) if self.preflight.passed else 0
        self._state = self.preflight.budget_status if not self.preflight.passed else "ready"
        self._stop_reason = self.preflight.stop_reason if not self.preflight.passed else None
        self._load_or_initialize()

    @property
    def ledger_head_hash(self) -> str:
        return self._events[-1]["event_hash"] if self._events else ZERO_HASH

    @property
    def events(self) -> tuple[dict[str, Any], ...]:
        return tuple(dict(event) for event in self._events)

    @property
    def status(self) -> str:
        return self._state

    def _load_or_initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists() and self.path.stat().st_size:
            try:
                lines = self.path.read_bytes().splitlines()
                self._replay(lines)
                if self._pending:
                    self._stop(STOPPED_COST_UNVERIFIED, "ambiguous_in_flight")
                    self._pending.clear()
            except CostUnverifiedError:
                raise
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
                raise CostUnverifiedError("ledger validation failed") from error
            return
        self._append_event(
            "preflight",
            configuration_sha256=self.configuration.configuration_sha256,
            preflight_status="ready" if self.preflight.passed else "preflight_blocked",
            budget_status=self.preflight.budget_status,
            stop_reason=self.preflight.stop_reason,
            planned_provider_api_calls=self.preflight.planned_provider_api_calls,
            max_attempts_per_api_call=self.preflight.max_attempts_per_api_call,
            direct_expected_cost_microusd=self.preflight.direct_expected_cost_microusd,
            retry_inclusive_worst_case_microusd=self.preflight.retry_inclusive_worst_case_microusd,
            contingency_reserve_microusd=self.preflight.contingency_reserve_microusd,
            worst_case_reserved_microusd=self.preflight.worst_case_reserved_microusd,
            approved_cap_microusd=self.preflight.approved_cap_microusd,
            unused_headroom_microusd=self.preflight.unused_headroom_microusd,
        )

    @staticmethod
    def _hash_event(event_without_hash: Mapping[str, Any]) -> str:
        return hashlib.sha256(_canonical_json(event_without_hash).encode("utf-8")).hexdigest()

    def _append_event(self, event_type: str, **fields: Any) -> dict[str, Any]:
        event: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "sequence": len(self._events) + 1,
            "event_type": event_type,
            "prev_event_hash": self.ledger_head_hash,
            **fields,
        }
        event["event_hash"] = self._hash_event(event)
        encoded = (_canonical_json(event) + "\n").encode("utf-8")
        try:
            descriptor = os.open(str(self.path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            try:
                written = os.write(descriptor, encoded)
                if written != len(encoded):
                    raise OSError("ledger event append was incomplete")
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        except OSError as error:
            raise CostUnverifiedError("ledger event append failed") from error
        self._events.append(event)
        return event

    def _replay(self, lines: list[bytes]) -> None:
        expected_sequence = 1
        expected_previous = ZERO_HASH
        terminal_seen = False
        terminal_event_pending = False
        terminal_binding_reason: str | None = None
        for raw_line in lines:
            if not raw_line:
                raise CostUnverifiedError("ledger validation failed")
            try:
                event = json.loads(raw_line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise CostUnverifiedError("ledger validation failed") from error
            if not isinstance(event, dict):
                raise CostUnverifiedError("ledger validation failed")
            if raw_line != _canonical_json(event).encode("utf-8"):
                raise CostUnverifiedError("ledger validation failed")
            if _contains_float(event):
                raise CostUnverifiedError("ledger validation failed")
            if event.get("schema_version") != SCHEMA_VERSION:
                raise CostUnverifiedError("ledger validation failed")
            sequence = _event_int(event, "sequence", maximum=_MAX_LEDGER_EVENTS)
            event_type = event.get("event_type")
            if type(event_type) is not str or event_type not in _EVENT_TYPES:
                raise CostUnverifiedError("ledger validation failed")
            if expected_sequence != 1 and event_type == "preflight":
                raise CostUnverifiedError("ledger validation failed")
            _validate_event_schema(event)
            previous = event.get("prev_event_hash")
            if (
                type(previous) is not str
                or len(previous) != 64
                or any(character not in "0123456789abcdef" for character in previous)
            ):
                raise CostUnverifiedError("ledger validation failed")
            if (
                sequence != expected_sequence
                or previous != expected_previous
                or terminal_seen
                or (
                    terminal_event_pending
                    and event_type not in {
                        "reconciliation",
                        STOPPED_COST_UNVERIFIED,
                        STOPPED_BUDGET_EXHAUSTED,
                    }
                )
            ):
                raise CostUnverifiedError("ledger validation failed")
            if terminal_event_pending:
                if event_type == "reconciliation":
                    if event.get("status") not in _RECONCILIATION_REASONS_BY_STATUS:
                        raise CostUnverifiedError("ledger validation failed")
                else:
                    stop_reason = _event_stop_reason(event, expected_status=event_type)
                    if terminal_binding_reason is not None and (
                        event_type != STOPPED_COST_UNVERIFIED
                        or stop_reason != terminal_binding_reason
                    ):
                        raise CostUnverifiedError("ledger validation failed")
                    if terminal_binding_reason is None and (
                        event_type == STOPPED_COST_UNVERIFIED
                        and stop_reason != "ambiguous_in_flight"
                    ):
                        raise CostUnverifiedError("ledger validation failed")
            supplied_hash = event.get("event_hash")
            if (
                type(supplied_hash) is not str
                or len(supplied_hash) != 64
                or any(character not in "0123456789abcdef" for character in supplied_hash)
            ):
                raise CostUnverifiedError("ledger validation failed")
            unsigned = dict(event)
            unsigned.pop("event_hash", None)
            if self._hash_event(unsigned) != supplied_hash:
                raise CostUnverifiedError("ledger validation failed")
            self._replay_event(event)
            self._events.append(event)
            if event_type == "reconciliation" and event.get("status") != "reconciled":
                reason = event["stop_reason"]
                if not terminal_event_pending:
                    terminal_binding_reason = (
                        None if reason == "ambiguous_in_flight" else reason
                    )
                elif terminal_binding_reason is None and reason != "ambiguous_in_flight":
                    terminal_binding_reason = reason
                terminal_event_pending = True
            elif event_type in {STOPPED_COST_UNVERIFIED, STOPPED_BUDGET_EXHAUSTED}:
                terminal_event_pending = False
                terminal_binding_reason = None
            terminal_seen = event_type in {
                STOPPED_COST_UNVERIFIED,
                STOPPED_BUDGET_EXHAUSTED,
            } or (
                event_type == "preflight"
                and event.get("budget_status") in {
                    STOPPED_COST_UNVERIFIED,
                    STOPPED_BUDGET_EXHAUSTED,
                }
            )
            expected_sequence += 1
            expected_previous = supplied_hash
        if not self._events or self._events[0].get("event_type") != "preflight":
            raise CostUnverifiedError("ledger validation failed")
        if self._events[0].get("configuration_sha256") != self.configuration.configuration_sha256:
            raise CostUnverifiedError("ledger configuration mismatch")
        if terminal_event_pending:
            self._stop(
                STOPPED_COST_UNVERIFIED,
                terminal_binding_reason or "ambiguous_in_flight",
            )
            terminal_event_pending = False
            terminal_binding_reason = None
        if terminal_seen and self._pending:
            raise CostUnverifiedError("ledger validation failed")

    def _replay_event(self, event: Mapping[str, Any]) -> None:
        event_type = event["event_type"]
        if event_type == "preflight":
            expected = self.preflight
            if _event_text(event, "configuration_sha256") != self.configuration.configuration_sha256:
                raise CostUnverifiedError("ledger configuration mismatch")
            if event.get("preflight_status") != ("ready" if expected.passed else "preflight_blocked"):
                raise CostUnverifiedError("ledger validation failed")
            if event.get("budget_status") != expected.budget_status:
                raise CostUnverifiedError("ledger validation failed")
            if _event_optional_text(event, "stop_reason") != expected.stop_reason:
                raise CostUnverifiedError("ledger validation failed")
            for field_name, expected_value in (
                ("planned_provider_api_calls", expected.planned_provider_api_calls),
                ("max_attempts_per_api_call", expected.max_attempts_per_api_call),
                ("approved_cap_microusd", expected.approved_cap_microusd),
            ):
                if _event_int(event, field_name) != expected_value:
                    raise CostUnverifiedError("ledger validation failed")
            for field_name, expected_value in (
                ("direct_expected_cost_microusd", expected.direct_expected_cost_microusd),
                ("retry_inclusive_worst_case_microusd", expected.retry_inclusive_worst_case_microusd),
                ("contingency_reserve_microusd", expected.contingency_reserve_microusd),
                ("worst_case_reserved_microusd", expected.worst_case_reserved_microusd),
                ("unused_headroom_microusd", expected.unused_headroom_microusd),
            ):
                value = event.get(field_name)
                if expected_value is None:
                    if value is not None:
                        raise CostUnverifiedError("ledger validation failed")
                elif _event_int(event, field_name) != expected_value:
                    raise CostUnverifiedError("ledger validation failed")
            if not expected.passed:
                self._state = expected.budget_status
                self._stop_reason = expected.stop_reason
            return
        if event_type == "reservation":
            call_id = _event_text(event, "call_id")
            if not _is_redacted_call_id(call_id):
                raise CostUnverifiedError("ledger validation failed")
            provider = _event_text(event, "provider")
            pricing = self.configuration.pricing_for(provider)
            if pricing is None:
                raise CostUnverifiedError("ledger configuration mismatch")
            model = _event_text(event, "model")
            model_version = _event_text(event, "model_version")
            phase = _event_text(event, "phase")
            if (
                model != pricing.model
                or model_version != pricing.model_version
                or _canonical_phase(phase) != phase
                or _event_text(event, "pricing_snapshot_date") != pricing.pricing_snapshot_date
                or _event_text(event, "pricing_source_ref") != pricing.pricing_source_ref
                or _event_text(event, "input_usd_per_1k") != str(pricing.input_usd_per_1k)
                or _event_text(event, "cached_input_usd_per_1k") != str(pricing.cached_input_usd_per_1k)
                or _event_text(event, "output_usd_per_1k") != str(pricing.output_usd_per_1k)
            ):
                raise CostUnverifiedError("ledger configuration mismatch")
            bounds = self.configuration.bounds_for(phase)
            if bounds is None:
                raise CostUnverifiedError("ledger configuration mismatch")
            attempt = _event_int(event, "attempt", maximum=FIXED_TASK3_MAX_ATTEMPTS)
            input_bound = _event_int(event, "input_token_bound")
            output_bound = _event_int(event, "output_token_bound")
            reserved_microusd = _event_int(event, "reserved_microusd")
            if (
                attempt < 1
                or input_bound != bounds.input_tokens
                or output_bound != bounds.output_tokens
                or reserved_microusd != pricing.reservation_microusd(bounds)
            ):
                raise CostUnverifiedError("ledger validation failed")
            attempts = self._attempts.get(call_id, [])
            if len(attempts) != attempt - 1 or (call_id, attempt) in self._pending:
                raise CostUnverifiedError("ledger validation failed")
            identity = (provider, phase)
            if call_id in self._logical_classes and self._logical_classes[call_id] != identity:
                raise CostUnverifiedError("ledger validation failed")
            if call_id not in self._logical_classes and sum(
                1 for value in self._logical_classes.values() if value == identity
            ) >= self._planned_count(provider, phase):
                raise CostUnverifiedError("ledger validation failed")
            reservation = Reservation(
                call_id=call_id,
                provider=provider,
                model=model,
                model_version=model_version,
                phase=phase,
                attempt=attempt,
                input_token_bound=input_bound,
                output_token_bound=output_bound,
                reserved_microusd=reserved_microusd,
            )
            self._pending[(reservation.call_id, reservation.attempt)] = reservation
            self._attempts.setdefault(reservation.call_id, []).append(reservation)
            self._logical_classes.setdefault(
                reservation.call_id, (reservation.provider, reservation.phase)
            )
            self._active_reserved_microusd += reservation.reserved_microusd
            self._state = "running"
            return
        if event_type == "reconciliation":
            status = event.get("status")
            if type(status) is not str or status not in {
                "reconciled",
                "cost_unverified",
                "ambiguous_in_flight",
            }:
                raise CostUnverifiedError("ledger validation failed")
            call_id = _event_text(event, "call_id")
            attempt = _event_int(event, "attempt", maximum=FIXED_TASK3_MAX_ATTEMPTS)
            if not _is_redacted_call_id(call_id):
                raise CostUnverifiedError("ledger validation failed")
            key = (call_id, attempt)
            reservation = self._pending.get(key)
            if reservation is None:
                raise CostUnverifiedError("ledger validation failed")
            if event.get("phase") != reservation.phase:
                raise CostUnverifiedError("ledger validation failed")
            if _event_int(event, "reserved_microusd") != reservation.reserved_microusd:
                raise CostUnverifiedError("ledger validation failed")
            released = _event_int(event, "released_microusd")
            if status != "reconciled":
                if released != 0 or _event_reconciliation_reason(event) not in _RECONCILIATION_REASONS:
                    raise CostUnverifiedError("ledger validation failed")
                if any(
                    field_name in event
                    for field_name in (
                        "input_tokens",
                        "output_tokens",
                        "cached_tokens",
                        "total_tokens",
                        "reasoning_tokens",
                        "actual_cost_microusd",
                    )
                ):
                    raise CostUnverifiedError("ledger validation failed")
                self._pending.pop(key)
                return
            usage: dict[str, Any] = {}
            for field_name in (
                "input_tokens",
                "output_tokens",
                "cached_tokens",
                "total_tokens",
                "reasoning_tokens",
            ):
                if field_name in event:
                    usage[field_name] = event[field_name]
            try:
                normalized = self._normalized_usage(usage)
            except _UsageProblem as error:
                raise CostUnverifiedError("ledger validation failed") from error
            if (
                normalized["input_tokens"] > reservation.input_token_bound
                or normalized["output_tokens"] > reservation.output_token_bound
                or normalized["reasoning_tokens"] > reservation.output_token_bound
                or normalized["total_tokens"] > reservation.input_token_bound + reservation.output_token_bound
            ):
                raise CostUnverifiedError("ledger validation failed")
            pricing = self.configuration.pricing_for(reservation.provider)
            if pricing is None:
                raise CostUnverifiedError("ledger configuration mismatch")
            try:
                actual = pricing._cost_microusd(
                    normalized["input_tokens"],
                    normalized["output_tokens"],
                    normalized["cached_tokens"],
                )
            except _UsageProblem as error:
                raise CostUnverifiedError("ledger validation failed") from error
            if _event_int(event, "actual_cost_microusd") != actual or released != reservation.reserved_microusd - actual:
                raise CostUnverifiedError("ledger validation failed")
            outcome = event.get("outcome")
            if type(outcome) is not str or outcome not in _SAFE_OUTCOMES:
                raise CostUnverifiedError("ledger validation failed")
            try:
                _safe_error_class(event.get("error_class"))
            except _UsageProblem as error:
                raise CostUnverifiedError("ledger validation failed") from error
            self._pending.pop(key)
            self._active_reserved_microusd -= reservation.reserved_microusd
            self._spent_microusd += actual
            self._released_microusd += released
            return
        if event_type in {STOPPED_COST_UNVERIFIED, STOPPED_BUDGET_EXHAUSTED}:
            if event.get("budget_status") != event_type:
                raise CostUnverifiedError("ledger validation failed")
            reason = _event_stop_reason(event, expected_status=event_type)
            if self._pending:
                if event_type != STOPPED_COST_UNVERIFIED or reason != "ambiguous_in_flight":
                    raise CostUnverifiedError("ledger validation failed")
                self._pending.clear()
            self._state = event_type
            self._stop_reason = reason
            return
        raise CostUnverifiedError("ledger validation failed")

    def _raise_for_state(self) -> None:
        if self._state == STOPPED_BUDGET_EXHAUSTED:
            raise BudgetExhaustedError("exploratory budget is stopped")
        if self._state == STOPPED_COST_UNVERIFIED:
            raise CostUnverifiedError("exploratory cost is unverified")
        if self._state == "preflight_blocked":
            if self.preflight.budget_status == STOPPED_BUDGET_EXHAUSTED:
                raise BudgetExhaustedError("exploratory preflight exceeds the approved cap")
            raise CostUnverifiedError("exploratory preflight is blocked")

    def _stop(self, status: str, reason: str) -> None:
        with self._lock:
            if self._state in {STOPPED_COST_UNVERIFIED, STOPPED_BUDGET_EXHAUSTED}:
                return
            pending = tuple(
                sorted(self._pending.values(), key=lambda item: (item.call_id, item.attempt))
            )
            effective_reason = reason
            if (
                status == STOPPED_COST_UNVERIFIED
                and pending
                and (
                    not self._events
                    or self._events[-1].get("event_type") != "reconciliation"
                    or self._events[-1].get("status") == "reconciled"
                )
            ):
                effective_reason = "ambiguous_in_flight"
            for reservation in pending:
                self._append_event(
                    "reconciliation",
                    status="ambiguous_in_flight",
                    call_id=reservation.call_id,
                    phase=reservation.phase,
                    attempt=reservation.attempt,
                    reserved_microusd=reservation.reserved_microusd,
                    released_microusd=0,
                    stop_reason="ambiguous_in_flight",
                )
            self._pending.clear()
            self._append_event(
                status,
                budget_status=status,
                stop_reason=effective_reason,
            )
            self._state = status
            self._stop_reason = effective_reason

    def _stop_cost_unverified(self, reason: str) -> None:
        self._stop(STOPPED_COST_UNVERIFIED, reason)
        raise CostUnverifiedError("exploratory cost is unverified")

    def _stop_attempt_cost_unverified(self, reservation: Reservation, reason: str) -> None:
        with self._lock:
            self._raise_for_state()
            current = self._pending.get((reservation.call_id, reservation.attempt))
            if current is None or current != reservation:
                self._stop_cost_unverified("ledger_mismatch")
            assert current is not None
            self._append_event(
                "reconciliation",
                status="cost_unverified",
                call_id=current.call_id,
                phase=current.phase,
                attempt=current.attempt,
                reserved_microusd=current.reserved_microusd,
                released_microusd=0,
                stop_reason=reason,
            )
            self._pending.pop((current.call_id, current.attempt))
            self._stop(STOPPED_COST_UNVERIFIED, reason)
            raise CostUnverifiedError("exploratory cost is unverified")

    def _stop_budget(self, reason: str) -> None:
        self._stop(STOPPED_BUDGET_EXHAUSTED, reason)
        raise BudgetExhaustedError("exploratory budget is exhausted")

    def _planned_count(self, provider: str, phase: str) -> int:
        return sum(
            item.count
            for item in self.configuration.planned_calls or ()
            if item.provider == provider and item.phase == phase
        )

    def reserve_attempt(
        self,
        *,
        call_id: str,
        provider: str,
        phase: str,
        model: str | None = None,
        model_version: str | None = None,
        attempt: int | None = None,
    ) -> Reservation:
        with self._lock:
            self._raise_for_state()
            try:
                safe_call_id = _redacted_call_id(call_id)
                safe_provider = _safe_text(provider, "provider")
                canonical = _canonical_phase(phase)
            except (CostLedgerError, TypeError, ValueError):
                self._stop_cost_unverified("invalid_call_identity")
            pricing = self.configuration.pricing_for(safe_provider)
            if pricing is None:
                self._stop_cost_unverified("provider_model_pricing_mismatch")
            assert pricing is not None
            if model is not None and model != pricing.model:
                self._stop_cost_unverified("provider_model_pricing_mismatch")
            if model_version is not None and model_version != pricing.model_version:
                self._stop_cost_unverified("provider_model_pricing_mismatch")
            if not pricing.prices_complete:
                self._stop_cost_unverified("missing_price")
            bounds = self.configuration.bounds_for(canonical)
            if bounds is None:
                self._stop_cost_unverified("missing_token_bound")
            assert bounds is not None
            attempts = self._attempts.get(safe_call_id, [])
            if safe_call_id in self._logical_classes and self._logical_classes[safe_call_id] != (safe_provider, canonical):
                self._stop_cost_unverified("call_identity_mismatch")
            if any(item.call_id == safe_call_id for item in self._pending.values()):
                self._stop_cost_unverified("reservation_already_in_flight")
            expected_attempt = len(attempts) + 1
            if attempt is not None and (type(attempt) is not int or attempt != expected_attempt):
                self._stop_cost_unverified("attempt_policy_exceeded")
            if expected_attempt > self.configuration.max_attempts_per_api_call:
                self._stop_cost_unverified("attempt_policy_exceeded")
            if not attempts and len(
                {
                    item.call_id
                    for item in self._attempts.get(safe_call_id, [])
                }
            ) == 0:
                used_logical = sum(
                    1
                    for key in self._logical_classes
                    if self._logical_classes[key] == (safe_provider, canonical)
                )
                if used_logical >= self._planned_count(safe_provider, canonical):
                    self._stop_budget("fixed_plan_exhausted")
            try:
                reserved = pricing.reservation_microusd(bounds)
            except _UsageProblem:
                self._stop_cost_unverified("missing_price")
            available = (
                self.configuration.approved_cap_microusd
                - self._contingency_reserved_microusd
                - self._spent_microusd
                - self._active_reserved_microusd
            )
            if reserved > available:
                self._stop_budget("attempt_reservation_exceeds_remaining_cap")
            reservation = Reservation(
                call_id=safe_call_id,
                provider=safe_provider,
                model=pricing.model,
                model_version=pricing.model_version,
                phase=canonical,
                attempt=expected_attempt,
                input_token_bound=bounds.input_tokens,
                output_token_bound=bounds.output_tokens,
                reserved_microusd=reserved,
            )
            self._append_event(
                "reservation",
                call_id=reservation.call_id,
                provider=reservation.provider,
                model=reservation.model,
                model_version=reservation.model_version,
                phase=reservation.phase,
                attempt=reservation.attempt,
                input_token_bound=reservation.input_token_bound,
                output_token_bound=reservation.output_token_bound,
                input_usd_per_1k=str(pricing.input_usd_per_1k),
                cached_input_usd_per_1k=str(pricing.cached_input_usd_per_1k),
                output_usd_per_1k=str(pricing.output_usd_per_1k),
                pricing_snapshot_date=pricing.pricing_snapshot_date,
                pricing_source_ref=pricing.pricing_source_ref,
                reserved_microusd=reservation.reserved_microusd,
            )
            self._pending[(reservation.call_id, reservation.attempt)] = reservation
            self._attempts.setdefault(reservation.call_id, []).append(reservation)
            self._logical_classes.setdefault(reservation.call_id, (safe_provider, canonical))
            self._active_reserved_microusd += reservation.reserved_microusd
            self._state = "running"
            return reservation

    @staticmethod
    def _normalized_usage(usage: Any) -> dict[str, int]:
        if not isinstance(usage, Mapping):
            raise _UsageProblem("missing_usage" if usage is None else "malformed_usage")
        try:
            _validate_nested_token_metadata(usage)
            if any(key not in _USAGE_FIELDS_WITH_DETAILS for key in usage):
                raise _UsageProblem("malformed_usage")
            for field_name in (
                "input_tokens",
                "output_tokens",
                "prompt_tokens",
                "completion_tokens",
                "cached_tokens",
                "total_tokens",
                "reasoning_tokens",
            ):
                if field_name in usage and (
                    type(usage[field_name]) is not int or usage[field_name] < 0
                ):
                    raise _UsageProblem("malformed_usage")
            input_value = usage.get("input_tokens", usage.get("prompt_tokens"))
            output_value = usage.get("output_tokens", usage.get("completion_tokens"))
            if "input_tokens" in usage and "prompt_tokens" in usage and usage["input_tokens"] != usage["prompt_tokens"]:
                raise _UsageProblem("malformed_usage")
            if "output_tokens" in usage and "completion_tokens" in usage and usage["output_tokens"] != usage["completion_tokens"]:
                raise _UsageProblem("malformed_usage")
            if input_value is None or output_value is None:
                raise _UsageProblem("missing_usage")
            cached_detail_values: list[int] = []
            for detail_field in _CACHED_TOKEN_DETAIL_FIELDS:
                if detail_field in usage:
                    details = usage[detail_field]
                    if not isinstance(details, Mapping):
                        raise _UsageProblem("malformed_usage")
                    if "cached_tokens" in details:
                        cached_detail_values.append(details["cached_tokens"])
            if len(set(cached_detail_values)) > 1:
                raise _UsageProblem("malformed_usage")
            cached_value = usage.get(
                "cached_tokens",
                cached_detail_values[0] if cached_detail_values else 0,
            )
            if cached_detail_values and cached_value != cached_detail_values[0]:
                raise _UsageProblem("malformed_usage")
            if cached_value > input_value:
                raise _UsageProblem("malformed_usage")
            total_value = usage.get("total_tokens", input_value + output_value)
            if total_value != input_value + output_value:
                raise _UsageProblem("malformed_usage")
            reasoning_detail_values: list[int] = []
            for detail_field in _REASONING_TOKEN_DETAIL_FIELDS:
                if detail_field in usage:
                    details = usage[detail_field]
                    if not isinstance(details, Mapping):
                        raise _UsageProblem("malformed_usage")
                    if "reasoning_tokens" in details:
                        reasoning_detail_values.append(details["reasoning_tokens"])
            if len(set(reasoning_detail_values)) > 1:
                raise _UsageProblem("malformed_usage")
            reasoning_value = usage.get(
                "reasoning_tokens",
                reasoning_detail_values[0] if reasoning_detail_values else 0,
            )
            if reasoning_detail_values and reasoning_value != reasoning_detail_values[0]:
                raise _UsageProblem("malformed_usage")
            return {
                "input_tokens": input_value,
                "output_tokens": output_value,
                "cached_tokens": cached_value,
                "total_tokens": total_value,
                "reasoning_tokens": reasoning_value,
            }
        except _UsageProblem:
            raise
        except Exception as error:
            raise _UsageProblem("malformed_usage") from error

    @staticmethod
    def _check_identity(
        reservation: Reservation,
        *,
        provider: str | None,
        model: str | None,
        model_version: str | None,
        metadata: Mapping[str, Any] | None,
    ) -> None:
        supplied = dict(metadata) if isinstance(metadata, Mapping) else {}
        for key, expected in (
            ("provider", reservation.provider),
            ("model", reservation.model),
            ("response_model", reservation.model),
            ("model_version", reservation.model_version),
        ):
            value = supplied.get(key)
            if value is not None and value != expected:
                raise _UsageProblem("provider_model_pricing_mismatch")
        for key, value in (
            ("provider", provider),
            ("model", model),
            ("model_version", model_version),
        ):
            if value is not None and value != getattr(reservation, key):
                raise _UsageProblem("provider_model_pricing_mismatch")

    def reconcile_response(
        self,
        reservation: Reservation | str,
        usage: Mapping[str, Any] | None,
        *,
        provider: str | None = None,
        model: str | None = None,
        model_version: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        outcome: str = "success",
        error_class: str | None = None,
    ) -> Reconciliation:
        with self._lock:
            self._raise_for_state()
            if isinstance(reservation, Reservation):
                key = (reservation.call_id, reservation.attempt)
            else:
                try:
                    safe_call_id = _redacted_call_id(reservation)
                except (CostLedgerError, TypeError, ValueError):
                    self._stop_cost_unverified("ledger_mismatch")
                matches = [item for item in self._pending.values() if item.call_id == safe_call_id]
                if len(matches) != 1:
                    self._stop_cost_unverified("ledger_mismatch")
                key = (matches[0].call_id, matches[0].attempt)
            current = self._pending.get(key)
            if current is None:
                self._stop_cost_unverified("ledger_mismatch")
            assert current is not None
            if isinstance(reservation, Reservation) and reservation != current:
                self._stop_cost_unverified("ledger_mismatch")
            safe_metadata: dict[str, Any] | None = None
            problem: _UsageProblem | None = None
            try:
                if metadata is not None:
                    if not isinstance(metadata, Mapping):
                        raise _UsageProblem("malformed_usage")
                    try:
                        safe_metadata = dict(metadata)
                    except Exception as error:
                        raise _UsageProblem("malformed_usage") from error
                    _validate_nested_token_metadata(safe_metadata)
                    if usage is None:
                        usage = safe_metadata.get("usage")
                if type(outcome) is not str or outcome not in _SAFE_OUTCOMES:
                    raise _UsageProblem("invalid_reconciliation_outcome")
                safe_error_class = _safe_error_class(error_class)
                self._check_identity(
                    current,
                    provider=provider,
                    model=model,
                    model_version=model_version,
                    metadata=safe_metadata,
                )
                normalized = self._normalized_usage(usage)
                if (
                    normalized["input_tokens"] > current.input_token_bound
                    or normalized["output_tokens"] > current.output_token_bound
                    or normalized["reasoning_tokens"] > current.output_token_bound
                    or normalized["total_tokens"] > current.input_token_bound + current.output_token_bound
                ):
                    raise _UsageProblem("token_bounds_exceeded")
                pricing = self.configuration.pricing_for(current.provider)
                if pricing is None:
                    raise _UsageProblem("provider_model_pricing_mismatch")
                actual = pricing._cost_microusd(
                    normalized["input_tokens"],
                    normalized["output_tokens"],
                    normalized["cached_tokens"],
                )
                if actual > current.reserved_microusd:
                    raise _UsageProblem("ledger_mismatch")
            except _UsageProblem as error:
                problem = error
            except Exception as error:
                problem = _UsageProblem("malformed_usage")
            if problem is not None:
                self._append_event(
                    "reconciliation",
                    status="cost_unverified",
                    call_id=current.call_id,
                    phase=current.phase,
                    attempt=current.attempt,
                    reserved_microusd=current.reserved_microusd,
                    released_microusd=0,
                    stop_reason=problem.reason,
                )
                self._pending.pop(key)
                self._stop(STOPPED_COST_UNVERIFIED, problem.reason)
                raise CostUnverifiedError("exploratory cost is unverified")
            released = current.reserved_microusd - actual
            reconciliation_fields: dict[str, Any] = {
                "status": "reconciled",
                "call_id": current.call_id,
                "phase": current.phase,
                "attempt": current.attempt,
                "input_tokens": normalized["input_tokens"],
                "output_tokens": normalized["output_tokens"],
                "cached_tokens": normalized["cached_tokens"],
                "total_tokens": normalized["total_tokens"],
                "reasoning_tokens": normalized["reasoning_tokens"],
                "actual_cost_microusd": actual,
                "reserved_microusd": current.reserved_microusd,
                "released_microusd": released,
                "outcome": outcome,
            }
            if safe_error_class is not None:
                reconciliation_fields["error_class"] = safe_error_class
            self._append_event(
                "reconciliation",
                **reconciliation_fields,
            )
            self._pending.pop(key)
            self._active_reserved_microusd -= current.reserved_microusd
            self._spent_microusd += actual
            self._released_microusd += released
            return Reconciliation(current.call_id, current.attempt, actual, released, outcome)

    def mark_ambiguous_in_flight(self, reservation: Reservation | str) -> None:
        with self._lock:
            self._raise_for_state()
            if isinstance(reservation, Reservation):
                current = self._pending.get((reservation.call_id, reservation.attempt))
            else:
                try:
                    safe_call_id = _redacted_call_id(reservation)
                except (CostLedgerError, TypeError, ValueError):
                    self._stop_cost_unverified("ledger_mismatch")
                matches = [item for item in self._pending.values() if item.call_id == safe_call_id]
                current = matches[0] if len(matches) == 1 else None
            if current is None:
                self._stop_cost_unverified("ledger_mismatch")
            assert current is not None
            self._append_event(
                "reconciliation",
                status="ambiguous_in_flight",
                call_id=current.call_id,
                phase=current.phase,
                attempt=current.attempt,
                reserved_microusd=current.reserved_microusd,
                released_microusd=0,
                stop_reason="ambiguous_in_flight",
            )
            self._pending.pop((current.call_id, current.attempt))
            self._stop(STOPPED_COST_UNVERIFIED, "ambiguous_in_flight")

    def report(self) -> dict[str, Any]:
        with self._lock:
            remaining = (
                self.configuration.approved_cap_microusd
                - self._contingency_reserved_microusd
                - self._spent_microusd
                - self._active_reserved_microusd
            )
            result = self.preflight.to_dict()
            result.update(
                {
                    "state": self._state,
                    "budget_status": self._state if self._state.startswith("stopped_") else "ready",
                    "stop_reason": self._stop_reason,
                    "spent_microusd": self._spent_microusd,
                    "actual_cost_microusd": self._spent_microusd,
                    "active_reserved_microusd": self._active_reserved_microusd,
                    "released_microusd": self._released_microusd,
                    "remaining_headroom_microusd": remaining,
                    "unused_headroom_microusd": self.configuration.approved_cap_microusd - self._spent_microusd,
                    "remaining_headroom_usd": _usd_text(remaining),
                    "unused_headroom_usd": _usd_text(
                        self.configuration.approved_cap_microusd - self._spent_microusd
                    ),
                    "ledger_head_hash": self.ledger_head_hash,
                    "configuration_sha256": self.configuration.configuration_sha256,
                    "pending_attempt_count": len(self._pending),
                    "observed_attempt_count": sum(len(value) for value in self._attempts.values()),
                    "observed_logical_call_count": len(self._logical_classes),
                }
            )
            return result


def _provider_metadata(provider: Any) -> Mapping[str, Any]:
    try:
        metadata = getattr(provider, "last_call_metadata")
        if not isinstance(metadata, Mapping):
            raise _MetadataProblem("metadata is not a mapping")
        snapshot = dict(metadata)
        _validate_nested_token_metadata(snapshot)
        return snapshot
    except _MetadataProblem:
        raise
    except Exception as error:
        raise _MetadataProblem("metadata access failed") from error


def _clear_provider_metadata(provider: Any) -> bool:
    try:
        setattr(provider, "last_call_metadata", {})
        cleared = getattr(provider, "last_call_metadata")
        return isinstance(cleared, Mapping) and not dict(cleared)
    except Exception:
        return False


class BudgetedProvider:
    """Provider adapter that enforces reserve-before-call and reconcile-after-call."""

    def __init__(self, provider: Any, ledger: CostLedger) -> None:
        self._provider = provider
        self._ledger = ledger
        self.name = str(getattr(provider, "name", ""))

    def complete(
        self,
        request: Any,
        *,
        call_id: str,
        phase: str,
        attempt: int | None = None,
    ) -> Any:
        self._ledger._raise_for_state()
        if not _clear_provider_metadata(self._provider):
            self._ledger._stop_cost_unverified("metadata_reset_failed")
        pricing = self._ledger.configuration.pricing_for(self.name)
        if pricing is None:
            self._ledger._stop_cost_unverified("provider_model_pricing_mismatch")
        assert pricing is not None
        provider_model = getattr(self._provider, "model", None)
        if provider_model is not None and provider_model != pricing.model:
            self._ledger._stop_cost_unverified("provider_model_pricing_mismatch")
        provider_model_version = getattr(self._provider, "model_version", None)
        if provider_model_version is not None and provider_model_version != pricing.model_version:
            self._ledger._stop_cost_unverified("provider_model_pricing_mismatch")
        reservation = self._ledger.reserve_attempt(
            call_id=call_id,
            provider=self.name,
            model=pricing.model,
            model_version=pricing.model_version,
            phase=phase,
            attempt=attempt,
        )
        try:
            response = self._provider.complete(request)
        except Exception as error:
            try:
                metadata = _provider_metadata(self._provider)
                usage = metadata.get("usage")
            except _MetadataProblem:
                self._ledger._stop_attempt_cost_unverified(reservation, "metadata_access_failed")
            if usage is None:
                try:
                    self._ledger.mark_ambiguous_in_flight(reservation)
                except CostUnverifiedError:
                    pass
                raise AmbiguousInFlightError(
                    "provider response status is ambiguous; retry is forbidden"
                ) from error
            self._ledger.reconcile_response(
                reservation,
                usage,
                metadata=metadata,
                outcome="provider_error",
                error_class=type(error).__name__,
            )
            raise
        try:
            metadata = _provider_metadata(self._provider)
            usage = metadata.get("usage")
        except _MetadataProblem:
            self._ledger._stop_attempt_cost_unverified(reservation, "metadata_access_failed")
        self._ledger.reconcile_response(reservation, usage, metadata=metadata)
        return response


def budgeted_provider(provider: Any, ledger: CostLedger) -> BudgetedProvider:
    return BudgetedProvider(provider, ledger)


__all__ = [
    "AmbiguousInFlightError",
    "BudgetExhaustedError",
    "BudgetedProvider",
    "CostConfig",
    "CostConfiguration",
    "CostLedger",
    "CostLedgerError",
    "CostUnverifiedError",
    "MICRO_USD_PER_USD",
    "PlannedCall",
    "PreflightReport",
    "PricingSnapshot",
    "ProviderPricing",
    "Reconciliation",
    "Reservation",
    "STOPPED_BUDGET_EXHAUSTED",
    "STOPPED_COST_UNVERIFIED",
    "TokenBounds",
    "budgeted_provider",
    "fixed_task3_call_plan",
    "preflight_cost",
]
