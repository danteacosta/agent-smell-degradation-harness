from __future__ import annotations

from pathlib import Path
from typing import Any

from eval.analysis_report import build_analysis_report
from mitigation.tradeoff import build_mitigation_report
from pairs.loader import list_intent_ids, load_all_pairs
from protocol.paired_stats import export_paired_stats, pair_degradation_outcomes
from protocol.reliability import synthetic_agreement_demo


def _pair_inventory(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "intent_id": pair["intent_id"],
            "smell_type": pair["smell"]["type"],
            "smell_category": pair["smell"]["category"],
        }
        for pair in pairs
    ]


def _analysis_summary(analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "effect_detected": analysis["effect_detected"],
        "observability_gate_passed": analysis["observability_gate_passed"],
        "smell_blind_paired_degradation_rate": analysis["smell_blind"][
            "paired_degradation_rate"
        ],
        "happy_paired_degradation_rate": analysis["happy"]["paired_degradation_rate"],
        "paired_stats": analysis["paired_stats"],
    }


def _mitigation_summary(mitigation: dict[str, Any]) -> dict[str, Any]:
    return {
        "mitigation_beneficial": mitigation["mitigation_beneficial"],
        "direct_paired_degradation_rate": mitigation["direct"]["paired_degradation_rate"],
        "rewrite_paired_degradation_rate": mitigation["rewrite"]["paired_degradation_rate"],
        "clarify_paired_degradation_rate": mitigation["clarify"]["paired_degradation_rate"],
        "overhead": mitigation["overhead"],
        "gate": mitigation["gate"],
    }


def build_dissertation_bundle(repo_root: Path, work_dir: Path) -> dict[str, Any]:
    """Aggregate thesis-facing protocol artifacts into one exportable bundle."""
    pairs = load_all_pairs()
    analysis = build_analysis_report(work_dir / "analysis")
    mitigation = build_mitigation_report(work_dir / "mitigation")

    pair_outcomes = pair_degradation_outcomes(
        _load_smell_blind_episodes(work_dir / "analysis")
    )
    paired_stats = export_paired_stats(
        analysis["smell_blind"]["oracle_pass_rate_clean"],
        analysis["smell_blind"]["oracle_pass_rate_smelly"],
        pair_outcomes=pair_outcomes,
    )

    design_spec = (
        repo_root
        / "docs"
        / "superpowers"
        / "specs"
        / "2026-07-20-agent-smell-degradation-harness-design.md"
    )

    return {
        "design_spec_path": str(design_spec.relative_to(repo_root)),
        "pair_inventory": _pair_inventory(pairs),
        "intent_ids": list_intent_ids(pairs),
        "taxonomy_modes": analysis["smell_blind"].get("taxonomy_modes", {}),
        "analysis_summary": _analysis_summary(analysis),
        "mitigation_summary": _mitigation_summary(mitigation),
        "paired_stats": paired_stats,
        "reliability": synthetic_agreement_demo(),
        "artifact_paths": {
            "analysis_report": "eval/analysis_report.json",
            "mitigation_report": "eval/mitigation_report.json",
        },
    }


def _load_smell_blind_episodes(analysis_work_dir: Path) -> list[dict[str, Any]]:
    import json

    episodes_path = analysis_work_dir / "smell_blind" / "episodes.jsonl"
    if not episodes_path.exists():
        return []
    return [
        json.loads(line)
        for line in episodes_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def render_bundle_summary(bundle: dict[str, Any]) -> str:
    """Human-readable markdown summary for thesis export."""
    reliability = bundle["reliability"]
    mitigation = bundle["mitigation_summary"]
    analysis = bundle["analysis_summary"]
    lines = [
        "# Dissertation bundle summary",
        "",
        f"Design spec: `{bundle['design_spec_path']}`",
        "",
        "## Pair inventory",
        "",
        f"- Intents: {', '.join(bundle['intent_ids'])}",
        f"- Count: {len(bundle['pair_inventory'])}",
        "",
        "## Taxonomy modes (smell-blind)",
        "",
    ]
    for mode, count in sorted(bundle["taxonomy_modes"].items()):
        lines.append(f"- `{mode}`: {count}")
    lines.extend(
        [
            "",
            "## Analysis",
            "",
            f"- Effect detected: {analysis['effect_detected']}",
            f"- Observability gate passed: {analysis['observability_gate_passed']}",
            f"- Smell-blind paired degradation rate: "
            f"{analysis['smell_blind_paired_degradation_rate']:.3f}",
            "",
            "## Mitigation (H5)",
            "",
            f"- Mitigation beneficial: {mitigation['mitigation_beneficial']}",
            f"- Direct paired degradation rate: "
            f"{mitigation['direct_paired_degradation_rate']:.3f}",
            f"- Rewrite paired degradation rate: "
            f"{mitigation['rewrite_paired_degradation_rate']:.3f}",
            f"- Clarify paired degradation rate: "
            f"{mitigation['clarify_paired_degradation_rate']:.3f}",
            f"- Clarify steps (mean): {mitigation['overhead']['clarify_steps_mean']}",
            "",
            "## Reliability (synthetic)",
            "",
            f"- Agreement rate: {reliability['agreement_rate']} "
            f"({reliability['limitation']})",
            "",
        ]
    )
    return "\n".join(lines) + "\n"
