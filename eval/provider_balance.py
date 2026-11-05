"""Offline provider/label balance diagnostic for the H2 B3-versus-B0 contrast.

Procedural trace features can encode which model produced a run (see the
2026-11-04 literature-matrix entry on trajectory fingerprints).  If provider
and degradation label are unbalanced across projects, a pooled B3-minus-B0
gain could reflect provider identity.  This module is *descriptive*: it counts
provider x label cells per split and flags imbalance so provider-stratified
reporting can be planned.  It does not gate, fit, or change any H2 estimand,
and it makes no provider calls.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

DEFAULT_MAX_RATE_GAP = 0.20


def provider_balance_report(
    partitions: Mapping[str, Sequence[Mapping[str, Any]]],
    labels: Mapping[str, int],
    *,
    provider_key: str = "provider",
    max_rate_gap: float = DEFAULT_MAX_RATE_GAP,
) -> dict[str, Any]:
    """Report provider x label counts per split plus descriptive confound flags."""

    if not 0 <= max_rate_gap <= 1:
        raise ValueError("max_rate_gap must be in [0, 1]")
    report: dict[str, Any] = {"provider_key": provider_key, "max_rate_gap": max_rate_gap, "splits": {}}
    for split, rows in partitions.items():
        cells: Counter[tuple[str, int]] = Counter()
        project_providers: dict[str, set[str]] = defaultdict(set)
        missing = 0
        for row in rows:
            episode_id = str(row.get("episode_id", ""))
            if episode_id not in labels:
                raise ValueError(f"missing label for {episode_id}")
            label = labels[episode_id]
            if label not in (0, 1) or isinstance(label, bool):
                raise ValueError(f"label for {episode_id} must be binary")
            provider = str(row.get(provider_key, "")).strip()
            if not provider:
                missing += 1
                continue
            cells[(provider, label)] += 1
            project_providers[str(row.get("project_id", ""))].add(provider)
        providers = sorted({provider for provider, _ in cells})
        rates: dict[str, float] = {}
        per_provider: dict[str, dict[str, int]] = {}
        for provider in providers:
            neg, pos = cells[(provider, 0)], cells[(provider, 1)]
            per_provider[provider] = {"clean": neg, "degraded": pos}
            rates[provider] = pos / (pos + neg)
        gap = (max(rates.values()) - min(rates.values())) if len(rates) > 1 else 0.0
        all_providers = set(providers)
        flags = []
        if missing:
            flags.append("missing_provider")
        if len(providers) < 2:
            flags.append("single_provider")
        if any(0 in (c["clean"], c["degraded"]) for c in per_provider.values()):
            flags.append("provider_missing_a_class")
        if gap > max_rate_gap:
            flags.append("provider_label_rate_gap")
        if any(seen != all_providers for seen in project_providers.values()) and len(providers) > 1:
            flags.append("project_missing_a_provider")
        report["splits"][split] = {
            "episodes": len(rows),
            "missing_provider": missing,
            "per_provider": per_provider,
            "degraded_rate_by_provider": rates,
            "max_degraded_rate_gap": gap,
            "flags": flags,
        }
    report["any_flag"] = any(s["flags"] for s in report["splits"].values())
    report["note"] = (
        "Descriptive only: flags indicate that provider-stratified or "
        "leave-one-provider-out reporting of the B3 gain is needed; they do not "
        "gate H2 or change its estimand."
    )
    return report
