from __future__ import annotations

from pathlib import Path
from typing import Any

from feature_plane import DeployableFeatureInput, extract_deployable_features


def _extract_output_only(episode: dict[str, Any]) -> dict[str, int]:
    """Return retrospective outcome data, never deployable detector inputs."""
    return {"oracle_passed": int(bool(episode.get("oracle_passed")))}


def extract_features(episode: dict[str, Any], provenance_path: str | Path) -> dict[str, dict]:
    """Extract deployable pre-final features plus a separate offline outcome family."""
    deployable = extract_deployable_features(
        DeployableFeatureInput.from_episode(episode), provenance_path
    )
    # Preserve historical family names for downstream reports while sourcing
    # every primary feature from the strict deployable allowlist.
    provenance = deployable["provenance"]
    # Keep the retrospective report contract stable while sourcing the values
    # from the strict feature boundary above.
    return {
        "static_smell": {"smell_present": 0, "requirement_length": deployable["static"]["requirement_length"]},
        "operational": deployable["operational"],
        "provenance_semantic": {
            "constraint_event_present": int(provenance["constraint_count"] > 0),
            "constraint_field_count": provenance["constraint_field_count"],
            "constraint_has_comparator": provenance["constraint_has_comparator"],
            "semantic_event_count": int(provenance["constraint_count"] > 0),
        },
        "output_only": _extract_output_only(episode),
    }
