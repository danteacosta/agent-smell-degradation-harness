"""Offline-first discovery runner for real-source requirement-smell cases."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agents.live import LiveAgent
from agents.stub import StubAgent
from eval.identity import configuration_id_for, new_run_id
from eval.metrics import aggregate_metrics
from eval.runner import run_eval_with_agent
from eval.task_adapters import AcceptanceCriteriaAdapter, BehavioralCodeGenerationAdapter
from pairs.validate import validate_pair


REPO_ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_PAIRS_DIR = REPO_ROOT / "data" / "pairs" / "discovery"
DEFAULT_ARTIFACT_ROOT = REPO_ROOT / "artifacts" / "experiments"
DISCOVERY_TASK_FAMILIES = ("test_gen", "behavior_codegen")


def _json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_revision(repo_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def load_discovery_pairs(pairs_dir: Path = DISCOVERY_PAIRS_DIR) -> list[dict[str, Any]]:
    if pairs_dir == DISCOVERY_PAIRS_DIR:
        from data.pairs.discovery.loader import load_discovery_cases

        pairs = load_discovery_cases()
    else:
        pairs = []
        for path in sorted(pairs_dir.glob("arta-*.json")):
            pair = json.loads(path.read_text(encoding="utf-8"))
            validate_pair(pair, source=str(path))
            pairs.append(pair)
    if len(pairs) < 10:
        raise ValueError(f"discovery corpus requires at least 10 cases, found {len(pairs)}")
    for pair in pairs:
        if "behavior_codegen" not in pair.get("generation_contract", {}):
            raise ValueError(f"{pair['intent_id']}: missing behavior_codegen contract")
        execution = pair.get("oracle_spec", {}).get("behavior_codegen", {}).get("_execution")
        if not isinstance(execution, dict) or not execution.get("hidden_tests"):
            raise ValueError(f"{pair['intent_id']}: missing frozen behavior oracle")
    return pairs


def _corpus_manifest(pairs: list[dict[str, Any]], pairs_dir: Path) -> dict[str, Any]:
    def pair_path_for(pair: dict[str, Any]) -> Path:
        expected = pairs_dir / f"{pair['intent_id'].lower()}.json"
        if expected.is_file():
            return expected
        for candidate in sorted(pairs_dir.glob("arta-*.json")):
            payload = json.loads(candidate.read_text(encoding="utf-8"))
            if payload.get("intent_id") == pair["intent_id"]:
                return candidate
        raise FileNotFoundError(f"no discovery pair file for {pair['intent_id']}")

    records = []
    for pair in pairs:
        path = pair_path_for(pair)
        records.append(
            {
                "intent_id": pair["intent_id"],
                "source_intent_id": pair.get("source_intent_id"),
                "project_id": pair.get("project_id", pair.get("source", {}).get("project")),
                "source_sha256": pair.get("source_sha256"),
                "pair_sha256": _sha256(path),
                "provenance_url": pair.get("provenance_url", pair.get("source", {}).get("provenance_url")),
                "smell_type": pair.get("smell", {}).get("type"),
                "removed_condition": pair.get("removed_condition"),
                "natural_variant": pair.get("natural_variant"),
                "licensing_notes": pair.get("licensing_notes", pair.get("contamination_notes")),
            }
        )
    return {
        "schema_version": "requirements-smell-discovery-corpus/v1",
        "status": "discovery_only",
        "dataset": "ARTA",
        "dataset_revision": "493297655cd653f8ebc797ef5c3c7ee2f736ab4c",
        "case_count": len(records),
        "records": records,
    }


def _materialize_artifacts(
    *,
    bundle_dir: Path,
    pairs: list[dict[str, Any]],
    episodes: list[dict[str, Any]],
    metrics: dict[str, Any],
    run_config: dict[str, Any],
    pairs_dir: Path,
) -> None:
    generated_dir = bundle_dir / "generated-code"
    report_dir = bundle_dir / "test-reports"
    generated_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    pair_map = {pair["intent_id"]: pair for pair in pairs}
    grouped_code: dict[str, dict[str, str]] = {}
    for episode in episodes:
        if episode.get("task_family") != "behavior_codegen":
            continue
        intent_id = str(episode["intent_id"])
        variant = str(episode["variant"])
        artifact = episode.get("artifact", {})
        source = artifact.get("source_code") if isinstance(artifact, dict) else None
        if not isinstance(source, str):
            continue
        safe_id = intent_id.lower().replace("/", "-")
        code_path = generated_dir / f"{safe_id}__{variant}.py"
        code_path.write_text(source, encoding="utf-8")
        grouped_code.setdefault(intent_id, {})[variant] = source
        _json_write(
            report_dir / f"{safe_id}__{variant}.json",
            {
                "intent_id": intent_id,
                "variant": variant,
                "requirement_text": episode.get("requirement_text"),
                "removed_condition": pair_map[intent_id].get("removed_condition"),
                "behavior_status": episode.get("behavior_status"),
                "target_condition_failures": episode.get("target_condition_failures", 0),
                "unrelated_condition_failures": episode.get("unrelated_condition_failures", 0),
                "behavior_report": episode.get("behavior_report"),
                "source_sha256": _sha256(code_path),
            },
        )

    comparison_dir = bundle_dir / "comparisons"
    for intent_id, variants in grouped_code.items():
        clean = variants.get("clean", "").splitlines(keepends=True)
        smelly = variants.get("smelly", "").splitlines(keepends=True)
        diff = difflib.unified_diff(clean, smelly, fromfile="clean.py", tofile="smelly.py")
        pair = pair_map[intent_id]
        text = "".join(diff)
        comparison_dir.mkdir(parents=True, exist_ok=True)
        (comparison_dir / f"{intent_id.lower()}.md").write_text(
            "# " + intent_id + "\n\n"
            + "Removed condition: " + str(pair.get("removed_condition", "")) + "\n\n"
            + "```diff\n" + text + "```\n",
            encoding="utf-8",
        )

    _json_write(bundle_dir / "metrics.json", metrics)
    _json_write(bundle_dir / "run.json", run_config)
    (bundle_dir / "episodes.jsonl").write_text(
        "\n".join(json.dumps(episode, sort_keys=True) for episode in episodes) + "\n",
        encoding="utf-8",
    )
    _json_write(bundle_dir / "corpus-manifest.json", _corpus_manifest(pairs, pairs_dir))


def run_discovery(
    *,
    mode: str = "offline",
    replications: int = 1,
    run_id: str | None = None,
    repo_root: Path = REPO_ROOT,
    artifact_root: Path = DEFAULT_ARTIFACT_ROOT,
    model: str = "discovery-offline-v1",
) -> dict[str, Any]:
    if replications < 1:
        raise ValueError("replications must be >= 1")
    pairs = load_discovery_pairs(repo_root / "data" / "pairs" / "discovery")
    run_id = run_id or f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{new_run_id()}"
    bundle_dir = artifact_root / "runs" / run_id
    if bundle_dir.exists():
        raise FileExistsError(f"artifact bundle already exists: {bundle_dir}")

    work_dir = repo_root / "runs" / f"discovery-{run_id}"
    episodes: list[dict[str, Any]] = []
    replication_metrics: list[dict[str, Any]] = []
    for replication_id in range(replications):
        task_adapters = (
            AcceptanceCriteriaAdapter(),
            BehavioralCodeGenerationAdapter(allow_trusted_fixture=mode == "offline"),
        )
        if mode == "offline":
            agent: Any = StubAgent(failure_mode="smell-blind")
            run_model = "stub-smell-blind"
        elif mode == "live":
            if os.environ.get("AGENT_EXPERIMENT") != "1":
                raise ValueError("live discovery requires AGENT_EXPERIMENT=1")
            agent = LiveAgent(model=model)
            run_model = model
        else:
            raise ValueError("mode must be offline or live")
        metrics, rep_episodes = run_eval_with_agent(
            agent,
            pairs=pairs,
            output_path=work_dir / f"metrics_rep_{replication_id}.json",
            traces_dir=work_dir / f"traces_rep_{replication_id}",
            episodes_path=work_dir / f"episodes_rep_{replication_id}.jsonl",
            task_adapters=task_adapters,
            validators=(),
            experiment_id="requirements-smell-discovery",
            run_id=run_id,
            replication_id=replication_id,
            configuration_id=configuration_id_for(
                {"mode": mode, "model": run_model, "task_ids": [a.task_family for a in task_adapters]}
            ),
        )
        replication_metrics.append(metrics)
        episodes.extend(rep_episodes)

    aggregate = aggregate_metrics(episodes)
    run_config = {
        "schema_version": "requirements-smell-discovery-run/v1",
        "status": "discovery_only",
        "mode": mode,
        "model": model if mode == "live" else "stub-smell-blind",
        "run_id": run_id,
        "replications": replications,
        "case_count": len(pairs),
        "episode_count": len(episodes),
        "expected_episode_count": len(pairs) * 2 * len(DISCOVERY_TASK_FAMILIES),
        "task_families": list(DISCOVERY_TASK_FAMILIES),
        "source_revision": _git_revision(repo_root),
        "created_at": datetime.now(UTC).isoformat(),
        "replication_metrics": replication_metrics,
    }
    _materialize_artifacts(
        bundle_dir=bundle_dir,
        pairs=pairs,
        episodes=episodes,
        metrics=aggregate,
        run_config=run_config,
        pairs_dir=repo_root / "data" / "pairs" / "discovery",
    )
    return {"run_id": run_id, "bundle_dir": str(bundle_dir), "metrics": aggregate, **run_config}


def verify_artifacts(bundle_dir: Path) -> dict[str, Any]:
    required = ["run.json", "corpus-manifest.json", "metrics.json", "episodes.jsonl"]
    missing = [name for name in required if not (bundle_dir / name).is_file()]
    if missing:
        raise ValueError(f"artifact bundle missing: {', '.join(missing)}")
    run = json.loads((bundle_dir / "run.json").read_text(encoding="utf-8"))
    episodes = [
        json.loads(line)
        for line in (bundle_dir / "episodes.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    expected = int(run["expected_episode_count"])
    if len(episodes) != expected:
        raise ValueError(f"expected {expected} episodes, found {len(episodes)}")
    return {"status": "ok", "bundle_dir": str(bundle_dir), "episode_count": len(episodes)}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("offline", "live"), default="offline")
    parser.add_argument("--replications", type=int, default=1)
    parser.add_argument("--run-id")
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--verify-artifacts", action="store_true")
    parser.add_argument("--bundle-dir", type=Path)
    args = parser.parse_args(argv)

    if args.verify_artifacts:
        bundle_dir = args.bundle_dir
        if bundle_dir is None:
            candidates = [
                path for path in (DEFAULT_ARTIFACT_ROOT / "runs").glob("*")
                if path.is_dir() and (path / "run.json").is_file()
            ]
            if not candidates:
                raise SystemExit("no discovery artifact bundles found")
            bundle_dir = max(
                candidates,
                key=lambda path: json.loads((path / "run.json").read_text(encoding="utf-8")).get("created_at", ""),
            )
        print(json.dumps(verify_artifacts(bundle_dir), indent=2))
        return

    result = run_discovery(
        mode=args.mode,
        replications=args.replications,
        run_id=args.run_id,
        model=args.model,
    )
    print(json.dumps({"run_id": result["run_id"], "bundle_dir": result["bundle_dir"], "episode_count": result["episode_count"]}, indent=2))


if __name__ == "__main__":
    main()
