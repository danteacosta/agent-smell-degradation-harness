"""Pure planned-pair diagnostics; no file I/O, providers or source execution."""
from collections import Counter, defaultdict

from protocol.paired_stats import clustered_bootstrap_ci

IDENTITY = ("run_id", "replication_id", "project_id", "intent_id", "constraint_id")
STATUSES = {"passed", "failed", "runtime_error", "timeout", "rejected", "not_executed", "worker_error"}


def key(row):
    values = tuple(row.get(name) for name in IDENTITY)
    if any(not isinstance(value, str) or not value for value in values):
        raise ValueError("complete string identities are required")
    return values


def analyze(plan: list[dict], outcomes: list[dict]) -> dict:
    """Equal project weights; only complete matched execution enters the delta.

    This diagnostic estimator is not the registered confirmatory analysis.
    Positive delta means more violations in the defective arm.
    """
    expected, observed = {}, {}
    for pair in plan:
        identity = key(pair)
        if identity in expected:
            raise ValueError("duplicate planned pair")
        for field in ("oracle_sha256", "configuration_sha256"):
            digest = pair.get(field)
            if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise ValueError("valid frozen-input hashes are required")
        expected[identity] = pair
    for row in outcomes:
        identity, variant = key(row), row.get("variant")
        if identity not in expected or variant not in {"clean", "defective"}:
            raise ValueError("unexpected episode")
        if (identity, variant) in observed:
            raise ValueError("duplicate episode; repetitions must not overwrite")
        if row.get("status") not in STATUSES:
            raise ValueError("unknown execution status")
        if any(row.get(f) != expected[identity][f] for f in ("oracle_sha256", "configuration_sha256")):
            raise ValueError("pair oracle/configuration mismatch")
        observed[identity, variant] = row
    projects, incomplete, counts = defaultdict(list), [], {v: Counter() for v in ("clean", "defective")}
    paired = []
    for identity, pair in expected.items():
        statuses = {v: observed.get((identity, v), {}).get("status", "missing") for v in counts}
        for variant, status in statuses.items():
            counts[variant][status] += 1
        if any(s not in {"passed", "failed"} for s in statuses.values()):
            incomplete.append({**{f: pair[f] for f in IDENTITY}, "statuses": statuses})
            continue
        delta = int(statuses["defective"] == "failed") - int(statuses["clean"] == "failed")
        projects[pair["project_id"]].append(delta)
        paired.append({**{f: pair[f] for f in IDENTITY}, "delta": delta})
    means = {p: sum(v) / len(v) for p, v in sorted(projects.items())}
    interval = clustered_bootstrap_ci(projects, n_boot=2000, seed=0) if len(projects) >= 2 else None
    return {"schema_version": "behavior-paired-diagnostic/v1", "confirmatory_eligible": False,
            "planned_pairs": len(plan), "complete_pairs": len(paired), "incomplete_pairs": incomplete,
            "status_counts": {v: dict(c) for v, c in counts.items()}, "paired_deltas": paired,
            "project_means": means, "project_count": len(means),
            "mean_project_delta": sum(means.values()) / len(means) if means else None,
            "diagnostic_project_bootstrap_ci": interval,
            "interpretation": "Complete-pair diagnostic only; missingness can select the sample. Synthetic intervals do not measure empirical uncertainty. No H1/H2 decision."}


