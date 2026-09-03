"""Secret-safe, explicit provider configuration for exploratory runs.

Only the credential is resolved from the environment.  Model snapshots,
endpoints, prices, token bounds, and protocol fingerprints are checked-in
non-secret inputs so a run cannot silently follow a moving provider alias.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
import json
import math
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any

from agents.providers import DeepSeekProvider, OpenAIProvider
from eval.exploratory_cost import CostConfiguration, ProviderPricing, TokenBounds


SCHEMA_VERSION = "exploratory-llm-judged-prepilot/v1"
PROVIDER_KINDS = frozenset({"openai", "deepseek"})
_ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
_HASH_NAME = re.compile(r"^[0-9a-f]{64}$")
_PHASES = ("generation.T1", "generation.T2", "generation.artifact", "judge")


class ProviderRuntimeConfigError(ValueError):
    """Raised for invalid public configuration or missing private keys."""


def _text(value: Any, field: str, *, maximum: int = 1024) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProviderRuntimeConfigError(f"{field} must be a non-empty string")
    result = value.strip()
    if len(result) > maximum or "\n" in result or "\r" in result:
        raise ProviderRuntimeConfigError(f"{field} is invalid")
    return result


def _env_name(value: Any, field: str) -> str:
    name = _text(value, field, maximum=128)
    if not _ENV_NAME.fullmatch(name):
        raise ProviderRuntimeConfigError(
            f"{field} must be an uppercase environment-variable name"
        )
    return name


def _required_env(name: str, environ: Mapping[str, str]) -> str:
    value = str(environ.get(name, ""))
    if not value.strip():
        raise ProviderRuntimeConfigError(
            f"required private environment variable is missing: {name}"
        )
    return value


def _decimal(value: Any, field: str, *, allow_none: bool = False) -> Decimal | None:
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or isinstance(value, float):
        raise ProviderRuntimeConfigError(f"{field} must be decimal text")
    try:
        parsed = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ProviderRuntimeConfigError(f"{field} must be a finite decimal") from error
    if not parsed.is_finite() or parsed < 0:
        raise ProviderRuntimeConfigError(f"{field} must be a finite non-negative decimal")
    return parsed


def _optional_number(value: Any, field: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProviderRuntimeConfigError(f"{field} must be a non-negative number or null")
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ProviderRuntimeConfigError(f"{field} must be a non-negative number or null")
    return result


def _positive_int(value: Any, field: str, default: int | None = None) -> int:
    if value is None and default is not None:
        return default
    if type(value) is not int or value <= 0:
        raise ProviderRuntimeConfigError(f"{field} must be a positive integer")
    return value


def _pricing_from_spec(
    spec: Mapping[str, Any],
    *,
    provider: str,
    model: str,
    model_version: str,
    require_complete: bool = True,
) -> ProviderPricing:
    raw_pricing = spec.get("pricing")
    if not isinstance(raw_pricing, Mapping):
        raw_pricing = {
            "input_usd_per_1k": spec.get("input_usd_per_1k"),
            "cached_input_usd_per_1k": spec.get("cached_input_usd_per_1k"),
            "output_usd_per_1k": spec.get("output_usd_per_1k"),
        }
    required = (
        "input_usd_per_1k",
        "cached_input_usd_per_1k",
        "output_usd_per_1k",
    )
    values = {
        field: _decimal(
            raw_pricing.get(field), field, allow_none=not require_complete
        )
        for field in required
    }
    snapshot = _text(
        spec.get("pricing_snapshot_date", raw_pricing.get("pricing_snapshot_date")),
        "pricing_snapshot_date",
        maximum=32,
    )
    try:
        if date.fromisoformat(snapshot).isoformat() != snapshot:
            raise ValueError
    except ValueError as error:
        raise ProviderRuntimeConfigError(
            "pricing_snapshot_date must be an ISO date"
        ) from error
    return ProviderPricing(
        provider=provider,
        model=model,
        model_version=model_version,
        pricing_snapshot_date=snapshot,
        pricing_source_ref=_text(
            spec.get("pricing_source_ref", raw_pricing.get("pricing_source_ref")),
            "pricing_source_ref",
        ),
        input_usd_per_1k=values["input_usd_per_1k"],
        cached_input_usd_per_1k=values["cached_input_usd_per_1k"],
        output_usd_per_1k=values["output_usd_per_1k"],
    )


def _resolve_public_value(
    spec: Mapping[str, Any],
    *,
    value_field: str,
    env_field: str,
    environ: Mapping[str, str],
    required: bool = True,
) -> str | None:
    if spec.get(value_field) is not None:
        return _text(spec[value_field], value_field)
    if spec.get(env_field) is not None:
        return _required_env(_env_name(spec[env_field], env_field), environ)
    if required:
        raise ProviderRuntimeConfigError(
            f"provider slot requires {value_field} or {env_field}"
        )
    return None


@dataclass(frozen=True, slots=True)
class ProviderSlot:
    """Resolved non-secret provider identity plus one dated price snapshot."""

    id: str
    kind: str
    api_key_env: str
    model: str
    model_version: str
    base_url: str | None
    reasoning_effort: str | None
    temperature: float | None
    max_tokens: int
    pricing: ProviderPricing

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _text(self.id, "provider id", maximum=128))
        kind = _text(self.kind, "provider kind", maximum=32).casefold()
        if kind not in PROVIDER_KINDS:
            raise ProviderRuntimeConfigError("provider kind is not supported")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "api_key_env", _env_name(self.api_key_env, "api_key_env"))
        object.__setattr__(self, "model", _text(self.model, "model", maximum=256))
        object.__setattr__(
            self,
            "model_version",
            _text(self.model_version, "model_version", maximum=256),
        )
        if self.base_url is not None:
            object.__setattr__(self, "base_url", _text(self.base_url, "base_url"))
        if self.reasoning_effort is not None:
            object.__setattr__(
                self,
                "reasoning_effort",
                _text(self.reasoning_effort, "reasoning_effort", maximum=64),
            )
        if self.temperature is not None and (
            not math.isfinite(self.temperature) or self.temperature < 0
        ):
            raise ProviderRuntimeConfigError("temperature must be finite and non-negative")
        object.__setattr__(self, "max_tokens", _positive_int(self.max_tokens, "max_tokens"))
        if not isinstance(self.pricing, ProviderPricing):
            raise ProviderRuntimeConfigError("pricing must be a ProviderPricing snapshot")
        if (
            self.pricing.provider != self.kind
            or self.pricing.model != self.model
            or self.pricing.model_version != self.model_version
        ):
            raise ProviderRuntimeConfigError("pricing identity does not match provider slot")

    def public_metadata(self) -> dict[str, Any]:
        """Return safe metadata; the environment key name is not its value."""

        return {
            "id": self.id,
            "kind": self.kind,
            "model": self.model,
            "model_version": self.model_version,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "reasoning_effort": self.reasoning_effort,
            "api_key_env": self.api_key_env,
            "pricing": self.pricing.to_dict(),
        }


def parse_provider_slot(spec: Mapping[str, Any], *, index: int = 0) -> ProviderSlot:
    if not isinstance(spec, Mapping):
        raise ProviderRuntimeConfigError(f"providers[{index}] must be an object")
    for forbidden in ("api_key", "secret", "token"):
        if forbidden in spec:
            raise ProviderRuntimeConfigError(
                f"providers[{index}] cannot contain a credential field"
            )
    provider_id = _text(spec.get("id"), f"providers[{index}].id", maximum=128)
    kind = _text(spec.get("kind"), f"providers[{index}].kind", maximum=32).casefold()
    model = _resolve_public_value(
        spec, value_field="model", env_field="model_env", environ={},
    )
    model_version = _resolve_public_value(
        spec, value_field="model_version", env_field="model_version_env", environ={},
    )
    assert model is not None and model_version is not None
    pricing = _pricing_from_spec(
        spec, provider=kind, model=model, model_version=model_version
    )
    raw_temperature = spec.get("temperature")
    temperature = _optional_number(raw_temperature, f"providers[{index}].temperature")
    reasoning = spec.get("reasoning_effort")
    if reasoning is not None:
        reasoning = _text(reasoning, f"providers[{index}].reasoning_effort", maximum=64)
    return ProviderSlot(
        id=provider_id,
        kind=kind,
        api_key_env=_env_name(spec.get("api_key_env"), f"providers[{index}].api_key_env"),
        model=model,
        model_version=model_version,
        base_url=(
            _text(spec["base_url"], f"providers[{index}].base_url")
            if spec.get("base_url") is not None
            else None
        ),
        reasoning_effort=reasoning,
        temperature=temperature,
        max_tokens=_positive_int(
            spec.get("max_tokens"), f"providers[{index}].max_tokens", default=4096
        ),
        pricing=pricing,
    )


def resolve_provider_spec(
    spec: Mapping[str, Any],
    *,
    environ: Mapping[str, str],
    client: Any | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Construct an adapter only after all public fields and the key are valid."""

    if not isinstance(spec, Mapping):
        raise ProviderRuntimeConfigError("provider spec must be an object")
    for forbidden in ("api_key", "secret", "token"):
        if forbidden in spec:
            raise ProviderRuntimeConfigError("provider spec cannot contain a credential field")
    kind = _text(spec.get("kind"), "provider kind", maximum=32).casefold()
    if kind not in PROVIDER_KINDS:
        raise ProviderRuntimeConfigError("provider kind is not supported")
    api_key_env = _env_name(spec.get("api_key_env"), "api_key_env")
    api_key = _required_env(api_key_env, environ)
    model = _resolve_public_value(
        spec, value_field="model", env_field="model_env", environ=environ,
    )
    model_version = _resolve_public_value(
        spec, value_field="model_version", env_field="model_version_env", environ=environ,
    )
    assert model is not None and model_version is not None
    base_url = spec.get("base_url")
    if base_url is None and spec.get("base_url_env") is not None:
        base_url = _required_env(_env_name(spec["base_url_env"], "base_url_env"), environ)
    elif base_url is not None:
        base_url = _text(base_url, "base_url")
    reasoning_effort = spec.get("reasoning_effort")
    if reasoning_effort is None and spec.get("reasoning_effort_env") is not None:
        reasoning_effort = _required_env(
            _env_name(spec["reasoning_effort_env"], "reasoning_effort_env"), environ
        )
    elif reasoning_effort is not None:
        reasoning_effort = _text(reasoning_effort, "reasoning_effort", maximum=64)
    temperature = _optional_number(spec.get("temperature", 0.0), "temperature")
    max_tokens = _positive_int(spec.get("max_tokens"), "max_tokens", default=4096)
    pricing_spec = dict(spec)
    raw_pricing = spec.get("pricing")
    if isinstance(raw_pricing, Mapping):
        pricing_spec["pricing"] = dict(raw_pricing)
    else:
        legacy_rates = {
            "input_usd_per_1k": "input_usd_per_1k_env",
            "cached_input_usd_per_1k": "cached_input_usd_per_1k_env",
            "output_usd_per_1k": "output_usd_per_1k_env",
        }
        pricing_spec["pricing"] = {
            target: (
                spec.get(source)
                if source not in spec
                else _required_env(_env_name(spec[source], source), environ)
            )
            for target, source in legacy_rates.items()
            if source in spec
        }
    if "pricing_snapshot_date" not in pricing_spec:
        pricing_spec["pricing_snapshot_date"] = "1970-01-01"
    if "pricing_source_ref" not in pricing_spec:
        pricing_spec["pricing_source_ref"] = "runtime-config"
    pricing = _pricing_from_spec(
        pricing_spec,
        provider=kind,
        model=model,
        model_version=model_version,
        require_complete=False,
    )
    kwargs = {
        "api_key": api_key,
        "model": model,
        "base_url": base_url,
        "max_tokens": max_tokens,
        "temperature": temperature or 0.0,
        "reasoning_effort": reasoning_effort,
        "input_usd_per_1k": (
            float(pricing.input_usd_per_1k)
            if pricing.input_usd_per_1k is not None
            else None
        ),
        "cached_input_usd_per_1k": (
            float(pricing.cached_input_usd_per_1k)
            if pricing.cached_input_usd_per_1k is not None
            else None
        ),
        "output_usd_per_1k": (
            float(pricing.output_usd_per_1k)
            if pricing.output_usd_per_1k is not None
            else None
        ),
        "client": client,
    }
    provider = OpenAIProvider(**kwargs) if kind == "openai" else DeepSeekProvider(**kwargs)
    provider_metadata = provider.configuration_metadata()
    public = {
        "id": _text(spec.get("id"), "provider id", maximum=128),
        "kind": kind,
        "model": model,
        "model_version": model_version,
        "base_url": provider.base_url,
        "max_tokens": max_tokens,
        "temperature": provider_metadata["temperature"],
        "reasoning_effort": reasoning_effort,
        "api_key_env": api_key_env,
        "pricing": pricing.to_dict(),
        "pricing_envs": {
            field: spec.get(field)
            for field in (
                "input_usd_per_1k_env",
                "cached_input_usd_per_1k_env",
                "output_usd_per_1k_env",
            )
            if spec.get(field)
        },
    }
    return provider, public


def _parse_token_bounds(value: Any) -> Mapping[str, TokenBounds]:
    if not isinstance(value, Mapping) or set(value) != set(_PHASES):
        raise ProviderRuntimeConfigError(
            "token_bounds must contain exactly the four frozen protocol phases"
        )
    result: dict[str, TokenBounds] = {}
    for phase in _PHASES:
        raw = value[phase]
        if not isinstance(raw, Mapping) or set(raw) != {"input_tokens", "output_tokens"}:
            raise ProviderRuntimeConfigError(f"token_bounds[{phase}] is invalid")
        try:
            result[phase] = TokenBounds(raw["input_tokens"], raw["output_tokens"])
        except (TypeError, ValueError) as error:
            raise ProviderRuntimeConfigError(f"token_bounds[{phase}] is invalid") from error
    return MappingProxyType(result)


def validate_measured_token_fit(
    measurements: Mapping[str, Mapping[str, Any]],
    bounds: Mapping[str, TokenBounds],
) -> None:
    """Reject a preflight when compact prompt/schema measurements exceed bounds."""

    for phase in _PHASES:
        measurement = measurements.get(phase)
        bound = bounds.get(phase)
        if not isinstance(measurement, Mapping) or bound is None:
            raise ProviderRuntimeConfigError(f"token fit measurement is missing for {phase}")
        input_tokens = measurement.get("input_tokens")
        output_tokens = measurement.get("output_tokens")
        if type(input_tokens) is not int or type(output_tokens) is not int:
            raise ProviderRuntimeConfigError(f"token fit measurement is invalid for {phase}")
        if input_tokens > bound.input_tokens or output_tokens > bound.output_tokens:
            raise ProviderRuntimeConfigError(f"token bound exceeded for {phase}")


def _validate_protocol_hashes(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ProviderRuntimeConfigError("protocol_hashes must be an object")
    fields = (
        "generation_prompt_template_sha256",
        "judge_prompt_template_sha256",
        "generation_output_schema_sha256",
        "judge_response_schema_sha256",
        "rubric_sha256",
    )
    if set(value) != set(fields) or any(
        not isinstance(value[field], str) or not _HASH_NAME.fullmatch(value[field])
        for field in fields
    ):
        raise ProviderRuntimeConfigError("protocol_hashes must contain five SHA-256 values")
    return {field: value[field] for field in fields}


@dataclass(frozen=True, slots=True)
class ExploratoryRuntimeConfig:
    stage: str
    task_family: str
    context_condition: str
    providers: tuple[ProviderSlot, ...]
    token_bounds: Mapping[str, TokenBounds]
    approved_cap_usd: Decimal
    max_attempts_per_api_call: int
    duplicate_fraction: Decimal
    duplicate_seed: int
    contingency_rate: Decimal
    protocol_hashes: Mapping[str, str]
    source_revision: str

    def __post_init__(self) -> None:
        if self.context_condition != "no_compaction":
            raise ProviderRuntimeConfigError("exploratory run must use no_compaction")
        if len(self.providers) != 2 or {item.kind for item in self.providers} != PROVIDER_KINDS:
            raise ProviderRuntimeConfigError(
                "exploratory runtime requires exactly one openai and one deepseek slot"
            )
        if len({item.id for item in self.providers}) != len(self.providers):
            raise ProviderRuntimeConfigError("provider slot ids must be unique")
        if len({item.model_version for item in self.providers}) != len(self.providers):
            raise ProviderRuntimeConfigError("provider/model configurations must be distinct")
        if not isinstance(self.approved_cap_usd, Decimal) or self.approved_cap_usd <= 0:
            raise ProviderRuntimeConfigError("approved_cap_usd must be positive")
        if self.approved_cap_usd > Decimal("1.00"):
            raise ProviderRuntimeConfigError("approved_cap_usd cannot exceed USD 1.00")
        if self.max_attempts_per_api_call != 2:
            raise ProviderRuntimeConfigError("max_attempts_per_api_call must be two")
        if self.duplicate_fraction != Decimal("0.2") or self.duplicate_seed != 0:
            raise ProviderRuntimeConfigError("duplicate selection must use the frozen 20% seed")
        if type(self.duplicate_seed) is not int:
            raise ProviderRuntimeConfigError("duplicate_seed must be an integer")
        if self.contingency_rate != Decimal("0.25"):
            raise ProviderRuntimeConfigError("contingency_rate must be 25 percent")
        if set(self.token_bounds) != set(_PHASES):
            raise ProviderRuntimeConfigError("token bounds are incomplete")
        _validate_protocol_hashes(self.protocol_hashes)
        object.__setattr__(self, "token_bounds", MappingProxyType(dict(self.token_bounds)))
        object.__setattr__(self, "protocol_hashes", MappingProxyType(dict(self.protocol_hashes)))
        object.__setattr__(self, "providers", tuple(self.providers))

    def cost_configuration(self) -> CostConfiguration:
        return CostConfiguration(
            provider_pricing=tuple(item.pricing for item in self.providers),
            token_bounds=self.token_bounds,
            approved_cap_usd=self.approved_cap_usd,
            contingency_rate=self.contingency_rate,
            max_attempts_per_api_call=self.max_attempts_per_api_call,
        )

    def public_metadata(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "stage": self.stage,
            "task_family": self.task_family,
            "context_condition": self.context_condition,
            "providers": [item.public_metadata() for item in self.providers],
            "token_bounds": {
                phase: self.token_bounds[phase].to_dict() for phase in _PHASES
            },
            "approved_cap_usd": str(self.approved_cap_usd),
            "max_attempts_per_api_call": self.max_attempts_per_api_call,
            "duplicate_fraction": str(self.duplicate_fraction),
            "duplicate_seed": self.duplicate_seed,
            "contingency_rate": str(self.contingency_rate),
            "protocol_hashes": dict(self.protocol_hashes),
            "source_revision": self.source_revision,
        }


def load_exploratory_runtime_config(path: str | Path) -> ExploratoryRuntimeConfig:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProviderRuntimeConfigError(f"cannot read exploratory runtime config: {path}") from error
    if not isinstance(payload, Mapping):
        raise ProviderRuntimeConfigError("exploratory runtime config must be an object")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ProviderRuntimeConfigError(f"config schema_version must be {SCHEMA_VERSION}")
    providers_raw = payload.get("providers")
    if not isinstance(providers_raw, list):
        raise ProviderRuntimeConfigError("providers must be a list")
    slots = tuple(parse_provider_slot(raw, index=index) for index, raw in enumerate(providers_raw))
    bounds = _parse_token_bounds(payload.get("token_bounds"))
    approved = _decimal(payload.get("approved_cap_usd"), "approved_cap_usd")
    duplicate_fraction = _decimal(payload.get("duplicate_fraction"), "duplicate_fraction")
    contingency = _decimal(payload.get("contingency_rate"), "contingency_rate")
    assert approved is not None and duplicate_fraction is not None and contingency is not None
    source_revision = _text(payload.get("source_revision"), "source_revision", maximum=128)
    return ExploratoryRuntimeConfig(
        stage=_text(payload.get("stage"), "stage", maximum=128),
        task_family=_text(payload.get("task_family"), "task_family", maximum=128),
        context_condition=_text(
            payload.get("context_condition"), "context_condition", maximum=64
        ),
        providers=slots,
        token_bounds=bounds,
        approved_cap_usd=approved,
        max_attempts_per_api_call=_positive_int(
            payload.get("max_attempts_per_api_call"),
            "max_attempts_per_api_call",
        ),
        duplicate_fraction=duplicate_fraction,
        duplicate_seed=payload.get("duplicate_seed"),
        contingency_rate=contingency,
        protocol_hashes=_validate_protocol_hashes(payload.get("protocol_hashes")),
        source_revision=source_revision,
    )


def build_provider_from_slot(
    slot: ProviderSlot,
    *,
    environ: Mapping[str, str],
    client: Any | None = None,
) -> tuple[Any, dict[str, Any]]:
    spec = {
        **slot.public_metadata(),
        "pricing": slot.pricing.to_dict(),
    }
    return resolve_provider_spec(spec, environ=environ, client=client)


__all__ = [
    "ExploratoryRuntimeConfig",
    "PROVIDER_KINDS",
    "ProviderRuntimeConfigError",
    "ProviderSlot",
    "SCHEMA_VERSION",
    "build_provider_from_slot",
    "load_exploratory_runtime_config",
    "parse_provider_slot",
    "resolve_provider_spec",
    "validate_measured_token_fit",
]
