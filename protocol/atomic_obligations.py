"""Typed, prompt-free atomic-obligation observations.

This contract operationalizes the article-inspired secondary mechanism without
turning it into a new smell taxonomy or a confirmatory feature family. Provider
T1 responses report only bounded atom types and statuses; the runtime
materializes hash-bound observations at T3. Raw obligation text is never
persisted in these records.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from hashlib import sha256
from typing import Any, Literal

ATOMIC_OBLIGATION_SCHEMA_VERSION = "atomic-obligations/v1"
AtomicObligationType = Literal[
    "actor",
    "action",
    "object",
    "condition",
    "threshold",
    "scope",
    "temporal",
    "exception",
    "modality",
]
AtomicObligationStatus = Literal["present", "absent", "uncertain"]

ATOMIC_OBLIGATION_TYPES = frozenset(
    {
        "actor",
        "action",
        "object",
        "condition",
        "threshold",
        "scope",
        "temporal",
        "exception",
        "modality",
    }
)
ATOMIC_OBLIGATION_STATUSES = frozenset({"present", "absent", "uncertain"})
_PROVIDER_FIELDS = {"constraint_index", "atom_type", "status"}
_OBSERVATION_FIELDS = {
    "schema_version",
    "obligation_id",
    "constraint_id",
    "constraint_sha256",
    "constraint_index",
    "atom_type",
    "status",
    "source_checkpoint",
    "observation_id",
    "preservation_class",
    "available_at",
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def validate_atomic_obligations(
    value: Any,
    constraints: Sequence[Any] | None = None,
) -> list[dict[str, Any]]:
    """Validate the provider's bounded T1 atom inventory.

    constraint_index is one-based and refers only to the provider's own
    interpreted constraints list. No source text, oracle, label or final
    artifact is accepted.
    """

    if not isinstance(value, list):
        raise ValueError("atomic_obligations must be a list")
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()
    constraint_count = len(constraints) if constraints is not None else None
    for item in value:
        if not isinstance(item, Mapping) or set(item) != _PROVIDER_FIELDS:
            raise ValueError(
                "atomic_obligations items must contain exactly "
                "constraint_index, atom_type, and status"
            )
        index = item["constraint_index"]
        atom_type = str(item["atom_type"]).strip()
        status = str(item["status"]).strip()
        if isinstance(index, bool) or not isinstance(index, int) or index < 1:
            raise ValueError("atomic_obligations.constraint_index must be a positive integer")
        if constraint_count is not None and index > constraint_count:
            raise ValueError("atomic_obligations.constraint_index exceeds constraint count")
        if atom_type not in ATOMIC_OBLIGATION_TYPES:
            raise ValueError(f"unsupported atomic obligation type: {atom_type}")
        if status not in ATOMIC_OBLIGATION_STATUSES:
            raise ValueError(f"unsupported atomic obligation status: {status}")
        key = (index, atom_type)
        if key in seen:
            raise ValueError("atomic_obligations cannot repeat a constraint/type pair")
        seen.add(key)
        normalized.append(
            {
                "constraint_index": index,
                "atom_type": atom_type,
                "status": status,
            }
        )
    return normalized


def materialize_atomic_obligation_observations(
    constraints: Sequence[Any],
    atomic_obligations: Sequence[Mapping[str, Any]],
    constraint_lineage: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Bind T1 atom observations to hash-only T3 constraint lineage."""

    normalized = validate_atomic_obligations(atomic_obligations, constraints)
    if len(constraint_lineage) != len(constraints):
        raise ValueError("atomic obligation lineage must cover every interpreted constraint")
    observations: list[dict[str, Any]] = []
    for item in normalized:
        index = int(item["constraint_index"])
        lineage = constraint_lineage[index - 1]
        if not isinstance(lineage, Mapping):
            raise ValueError("constraint lineage entries must be objects")
        constraint_id = str(lineage.get("constraint_id", "")).strip()
        constraint_digest = str(lineage.get("constraint_sha256", "")).strip()
        if not constraint_id or not _SHA256_RE.fullmatch(constraint_digest):
            raise ValueError("atomic obligation lineage requires a constraint ID and SHA-256 hash")
        atom_type = str(item["atom_type"])
        obligation_digest = sha256(
            f"{constraint_id}:{atom_type}".encode("utf-8")
        ).hexdigest()
        observations.append(
            {
                "schema_version": ATOMIC_OBLIGATION_SCHEMA_VERSION,
                "obligation_id": f"o{index:03d}-{obligation_digest[:12]}",
                "constraint_id": constraint_id,
                "constraint_sha256": constraint_digest,
                "constraint_index": index,
                "atom_type": atom_type,
                "status": str(item["status"]),
                "source_checkpoint": "T1",
                "observation_id": "atomic-obligation-normalizer/v1",
                # This is the article-inspired hard lane designation. It
                # describes the preservation policy, not a semantic verdict.
                "preservation_class": "constraint_hard_lane",
                "available_at": "T3",
            }
        )
    return validate_atomic_obligation_observations(
        observations,
        constraints=constraints,
        constraint_lineage=constraint_lineage,
    )


def validate_atomic_obligation_observations(
    value: Any,
    *,
    constraints: Sequence[Any] | None = None,
    constraint_lineage: Sequence[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Validate hash-bound T3 observations without terminal evidence."""

    if not isinstance(value, list):
        raise ValueError("atomic_obligation_observations must be a list")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, Mapping) or set(item) != _OBSERVATION_FIELDS:
            raise ValueError("atomic obligation observations have an invalid field set")
        if item["schema_version"] != ATOMIC_OBLIGATION_SCHEMA_VERSION:
            raise ValueError("atomic obligation observation has an unsupported schema version")
        obligation_id = str(item["obligation_id"]).strip()
        constraint_id = str(item["constraint_id"]).strip()
        digest = str(item["constraint_sha256"]).strip()
        index = item["constraint_index"]
        atom_type = str(item["atom_type"]).strip()
        status = str(item["status"]).strip()
        source_checkpoint = str(item["source_checkpoint"]).strip()
        observation_id = str(item["observation_id"]).strip()
        preservation_class = str(item["preservation_class"]).strip()
        available_at = str(item["available_at"]).strip()
        if (
            not obligation_id
            or obligation_id in seen
            or not constraint_id
            or not _SHA256_RE.fullmatch(digest)
        ):
            raise ValueError("atomic obligation observations require unique IDs and hashes")
        if isinstance(index, bool) or not isinstance(index, int) or index < 1:
            raise ValueError("atomic obligation observation index must be positive")
        if constraints is not None and index > len(constraints):
            raise ValueError("atomic obligation observation index exceeds constraint count")
        if atom_type not in ATOMIC_OBLIGATION_TYPES:
            raise ValueError(f"unsupported atomic obligation type: {atom_type}")
        if status not in ATOMIC_OBLIGATION_STATUSES:
            raise ValueError(f"unsupported atomic obligation status: {status}")
        if (
            source_checkpoint != "T1"
            or not observation_id
            or preservation_class != "constraint_hard_lane"
            or available_at != "T3"
        ):
            raise ValueError("atomic obligation observation has invalid provenance metadata")
        if constraint_lineage is not None:
            if len(constraint_lineage) != len(constraints or ()):
                raise ValueError("atomic obligation lineage length is inconsistent")
            lineage = constraint_lineage[index - 1]
            if (
                str(lineage.get("constraint_id", "")) != constraint_id
                or str(lineage.get("constraint_sha256", "")) != digest
            ):
                raise ValueError("atomic obligation observation is not bound to its lineage")
        seen.add(obligation_id)
        normalized.append(
            {
                "schema_version": ATOMIC_OBLIGATION_SCHEMA_VERSION,
                "obligation_id": obligation_id,
                "constraint_id": constraint_id,
                "constraint_sha256": digest,
                "constraint_index": index,
                "atom_type": atom_type,
                "status": status,
                "source_checkpoint": source_checkpoint,
                "observation_id": observation_id,
                "preservation_class": preservation_class,
                "available_at": available_at,
            }
        )
    return normalized


def summarize_atomic_obligations(
    observations: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return numeric, non-terminal mechanism metrics for secondary analysis."""

    statuses = Counter(str(item.get("status", "")) for item in observations)
    atom_types = Counter(str(item.get("atom_type", "")) for item in observations)
    return {
        "schema_version": ATOMIC_OBLIGATION_SCHEMA_VERSION,
        "source_checkpoint": "T1",
        "available_at": "T3",
        "observation_count": len(observations),
        "present_count": statuses.get("present", 0),
        "absent_count": statuses.get("absent", 0),
        "uncertain_count": statuses.get("uncertain", 0),
        "atom_type_counts": dict(sorted(atom_types.items())),
        "preservation_class": "constraint_hard_lane",
    }


__all__ = (
    "ATOMIC_OBLIGATION_SCHEMA_VERSION",
    "ATOMIC_OBLIGATION_STATUSES",
    "ATOMIC_OBLIGATION_TYPES",
    "AtomicObligationStatus",
    "AtomicObligationType",
    "materialize_atomic_obligation_observations",
    "summarize_atomic_obligations",
    "validate_atomic_obligation_observations",
    "validate_atomic_obligations",
)
