"""Reproducible offline scientific pre-pilot export."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from agents.stub import StubAgent
from eval.identity import configuration_id_for
from eval.manifest import build_manifest
from eval.runner import run_eval_with_agent
from eval.task_adapters import AcceptanceCriteriaAdapter, TraceabilityAdapter
from label_plane.datasets import validate_design_metadata
from pairs.loader import load_all_pairs
from agent_reliability_protocol import GateDecision, RunManifest, export_contract

PREPILOT_INTENT_COUNT = 12
PREPILOT_REPLICATIONS = 5


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def _twelve_intents() -> list[dict[str, Any]]:
    source = load_all_pairs()
    if len(source) != PREPILOT_INTENT_COUNT:
        raise ValueError(
            "prepilot requires 12 independent source intents; "
            f"found {len(source)} (refusing to pad or rename duplicates)"
        )
    intent_ids = [str(pair.get("intent_id", "")) for pair in source]
    if len(set(intent_ids)) != PREPILOT_INTENT_COUNT or not all(intent_ids):
        raise ValueError("prepilot requires 12 unique, non-empty source intent IDs")

    # Validate the complete experimental design before any agent execution.
    # The source-pair files are expanded only into their declared clean/smelly
    # variants and fixed replications; no synthetic source intent is created.
    design_records: list[dict[str, Any]] = []
    for pair in source:
        source_intent = str(pair["intent_id"])
        smell = pair.get("smell") if isinstance(pair.get("smell"), dict) else {}
        project_id = pair.get("project_id", pair.get("project", ""))
        defect_family = smell.get("category", smell.get("type", ""))
        for variant, requirement_key in (
            ("clean", "clean_requirement"),
            ("smelly", "smelly_requirement"),
        ):
            requirement_text = pair.get(requirement_key, "")
            for replication_id in range(PREPILOT_REPLICATIONS):
                design_records.append(
                    {
                        "source_intent_id": source_intent,
                        "project_id": project_id,
                        "variant": variant,
                        "replication_id": replication_id,
                        "defect_family": defect_family,
                        "source": pair.get("source", source_intent),
                        "requirement_text": requirement_text,
                    }
                )
    validate_design_metadata({"records": design_records})
    return [copy.deepcopy(pair) for pair in source]


def _group_splits(intent_ids: list[str], k: int = 3) -> dict[str, Any]:
    unique = sorted(intent_ids)
    folds = [[] for _ in range(k)]
    for index, intent_id in enumerate(unique):
        folds[index % k].append(intent_id)
    reports = []
    for index, test_intents in enumerate(folds):
        train = [intent for intent in unique if intent not in test_intents]
        calibration = train[index % len(train) :: 3] or train[:1]
        selection = [intent for intent in train if intent not in calibration] or train[:1]
        reports.append(
            {
                "fold": index,
                "test_intents": test_intents,
                "selection_intents": selection,
                "calibration_intents": calibration,
                "threshold_path": {"fit_intents": calibration, "threshold": 0.5},
            }
        )
    return {"group_by": "intent_id", "folds": reports}


def _analysis(episodes: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    clean = [episode["oracle_passed"] for episode in episodes if episode["variant"] == "clean"]
    smelly = [episode["oracle_passed"] for episode in episodes if episode["variant"] == "smelly"]
    e1 = sum(clean) / len(clean) - sum(smelly) / len(smelly)
    e2 = sum(episode["has_semantic_provenance"] for episode in episodes) / len(episodes)
    estimands = {
        "E1_clean_minus_smelly_pass_rate": e1,
        "E2_accepted_provenance_coverage": e2,
    }
    boundary_map = {
        "E1": {"estimand": "clean minus smelly oracle pass rate", "value": e1},
        "E2": {"estimand": "traceability-validated provenance coverage", "value": e2},
    }
    return estimands, boundary_map


def run_pre_pilot(*, output_root: Path, run_id: str = "prepilot-v4") -> dict[str, str | int]:
    """Create the fixed 12 intents × 2 variants × 5 replications offline export."""
    run_dir = output_root / run_id
    pairs = _twelve_intents()
    adapters = (AcceptanceCriteriaAdapter(),)
    validators = (TraceabilityAdapter(),)
    config = {
        "mode": "offline-prepilot",
        "intent_count": PREPILOT_INTENT_COUNT,
        "variants": ["clean", "smelly"],
        "replications": PREPILOT_REPLICATIONS,
        "task_ids": [adapter.task_family for adapter in adapters],
    }
    configuration_id = configuration_id_for(config)
    manifest = build_manifest(config, repo_root=Path(__file__).resolve().parents[1])
    protocol_manifest = RunManifest(
        schema_version="2.0.5",
        experiment_id="agent-smell-prepilot",
        run_id=run_id,
        created_at=manifest["timestamp"],
        git_sha=manifest.get("git_sha") or "unknown",
        harness_name="agent-smell-degradation-harness",
        harness_version="0.1.0",
        dataset_id="mesaflow-v4",
        dataset_hash=manifest["pairs_hash"],
        configuration_hash=configuration_id,
        model_provider="stub",
        model_name="deterministic-stub",
        model_version="1",
        random_seed=0,
        replication_count=PREPILOT_REPLICATIONS,
        environment={"mode": "offline"},
        decision=GateDecision.passed(),
        metadata={"format": "agent-reliability-protocol"},
        configuration=config,
    )
    manifest["protocol_next"] = protocol_manifest.to_dict()
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    export_contract(protocol_manifest, run_dir / "protocol_manifest.json")

    episodes: list[dict[str, Any]] = []
    for replication_id in range(PREPILOT_REPLICATIONS):
        _, replication = run_eval_with_agent(
            StubAgent(failure_mode="smell-blind"),
            pairs=pairs,
            output_path=run_dir / "analysis" / f"metrics_rep_{replication_id}.json",
            traces_dir=run_dir / "traces" / f"rep-{replication_id}",
            task_adapters=adapters,
            validators=validators,
            experiment_id="agent-smell-prepilot",
            run_id=run_id,
            replication_id=replication_id,
            configuration_id=configuration_id,
        )
        episodes.extend(replication)
    _write_jsonl(run_dir / "episodes.jsonl", episodes)
    _write_jsonl(run_dir / "labels.jsonl", [
        {"episode_id": episode["episode_id"], "oracle_passed": episode["oracle_passed"], "semantic_label": episode["semantic_label"]}
        for episode in episodes
    ])
    events: list[dict[str, Any]] = []
    for episode in episodes:
        artifact_path = run_dir / "artifacts" / f"{episode['episode_id']}.json"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(json.dumps(episode["artifact"], sort_keys=True) + "\n")
        for line in Path(episode["provenance_path"]).read_text().splitlines():
            if line:
                events.append(json.loads(line))
    _write_jsonl(run_dir / "events.jsonl", events)
    _write_jsonl(run_dir / "features" / "pre_final.jsonl", [
        {"episode_id": episode["episode_id"], "has_semantic_provenance": episode["has_semantic_provenance"]}
        for episode in episodes
    ])
    estimands, boundary_map = _analysis(episodes)
    analysis_dir = run_dir / "analysis"
    (analysis_dir / "estimands.json").write_text(json.dumps(estimands, indent=2) + "\n")
    (analysis_dir / "boundary_map.json").write_text(json.dumps(boundary_map, indent=2) + "\n")
    (analysis_dir / "group_splits.json").write_text(
        json.dumps(_group_splits([pair["intent_id"] for pair in pairs]), indent=2) + "\n"
    )
    return {"run_dir": str(run_dir), "episode_count": len(episodes)}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run offline reproducible scientific pre-pilot")
    parser.add_argument("--output-root", type=Path, default=Path("runs"))
    parser.add_argument("--run-id", default="prepilot-v4")
    args = parser.parse_args(argv)
    run_pre_pilot(output_root=args.output_root, run_id=args.run_id)


if __name__ == "__main__":
    main()
