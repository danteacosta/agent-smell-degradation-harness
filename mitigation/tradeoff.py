from __future__ import annotations

from typing import Any

from eval.runner import run_eval

MITIGATION_THRESHOLD = 0.5
RQ3_POLICIES = ("direct", "structured_rewrite", "targeted_clarification")
ORACLE_UPPER_BOUNDS = (
    "oracle_rewrite_upper_bound",
    "oracle_clarification_upper_bound",
)
MITIGATION_POLICIES = RQ3_POLICIES + ORACLE_UPPER_BOUNDS


def _summary_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "paired_degradation_rate": metrics["paired_degradation_rate"],
        "oracle_pass_rate_clean": metrics["oracle_pass_rate_clean"],
        "oracle_pass_rate_smelly": metrics["oracle_pass_rate_smelly"],
        "degradation_detected": metrics["degradation_detected"],
        "episode_count": metrics["episode_count"],
        "taxonomy_modes": metrics.get("taxonomy_modes", {}),
    }


def _rewrite_char_delta_mean(episodes: list[dict[str, Any]]) -> float:
    deltas: list[float] = []
    for episode in episodes:
        if episode.get("variant") != "smelly":
            continue
        meta = episode.get("mitigation_meta") or {}
        if "rewrite_char_delta" in meta:
            deltas.append(float(meta["rewrite_char_delta"]))
    if not deltas:
        return 0.0
    return sum(deltas) / len(deltas)


def is_mitigation_beneficial(
    direct_rate: float,
    rewrite_rate: float,
    clarify_rate: float,
    *,
    threshold: float = MITIGATION_THRESHOLD,
) -> bool:
    """True when both oracle-free interventions improve materially vs direct."""
    if (
        rewrite_rate <= direct_rate - threshold
        and clarify_rate <= direct_rate - threshold
    ):
        return True
    return rewrite_rate == 0.0 and clarify_rate == 0.0 and direct_rate > 0.0


def _gate_detail(
    *,
    beneficial: bool,
    direct_rate: float,
    rewrite_rate: float,
    clarify_rate: float,
) -> str:
    if beneficial:
        return (
            "oracle-free rewrite/clarification reduced paired_degradation_rate vs direct "
            "under smell-blind "
            f"(direct={direct_rate:.3f}, rewrite={rewrite_rate:.3f}, "
            f"clarify={clarify_rate:.3f})"
        )
    return (
        "mitigation did not meet benefit threshold; do not claim always-positive "
        f"(direct={direct_rate:.3f}, rewrite={rewrite_rate:.3f}, "
        f"clarify={clarify_rate:.3f})"
    )


def build_mitigation_report(work_dir) -> dict[str, Any]:
    """Run smell-blind policy comparison for the conditional RQ3 extension."""
    from pathlib import Path

    root = Path(work_dir)
    root.mkdir(parents=True, exist_ok=True)

    happy_metrics, _ = run_eval(
        failure_mode=None,
        policy="direct",
        output_path=root / "happy_direct" / "metrics.json",
        traces_dir=root / "happy_direct" / "traces",
        episodes_path=root / "happy_direct" / "episodes.jsonl",
    )

    policy_results: dict[str, dict[str, Any]] = {}
    rewrite_episodes: list[dict[str, Any]] = []

    for policy in MITIGATION_POLICIES:
        policy_dir = root / "smell_blind" / policy
        metrics, episodes = run_eval(
            failure_mode="smell-blind",
            policy=policy,
            output_path=policy_dir / "metrics.json",
            traces_dir=policy_dir / "traces",
            episodes_path=policy_dir / "episodes.jsonl",
        )
        policy_results[policy] = _summary_metrics(metrics)
        if policy == "structured_rewrite":
            rewrite_episodes = episodes

    direct_rate = policy_results["direct"]["paired_degradation_rate"]
    rewrite_rate = policy_results["structured_rewrite"]["paired_degradation_rate"]
    clarify_rate = policy_results["targeted_clarification"]["paired_degradation_rate"]
    beneficial = is_mitigation_beneficial(direct_rate, rewrite_rate, clarify_rate)

    return {
        "direct": policy_results["direct"],
        "structured_rewrite": policy_results["structured_rewrite"],
        "targeted_clarification": policy_results["targeted_clarification"],
        "oracle_upper_bounds": {
            "admissible_for_rq3": False,
            "reason": "These policies read the clean pair and are development-only ceilings.",
            "oracle_rewrite": policy_results["oracle_rewrite_upper_bound"],
            "oracle_clarification": policy_results["oracle_clarification_upper_bound"],
        },
        "happy_direct": _summary_metrics(happy_metrics),
        "mitigation_beneficial": beneficial,
        "claim_status": "rq3_candidate" if beneficial else "no_oracle_free_benefit_in_stub",
        "overhead": {
            "clarification_requests_mean": 1.0,
            "rewrite_char_delta_mean": _rewrite_char_delta_mean(rewrite_episodes),
        },
        "gate": {
            "passed": beneficial,
            "detail": _gate_detail(
                beneficial=beneficial,
                direct_rate=direct_rate,
                rewrite_rate=rewrite_rate,
                clarify_rate=clarify_rate,
            ),
        },
    }
