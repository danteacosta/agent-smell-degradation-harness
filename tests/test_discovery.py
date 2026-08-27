from __future__ import annotations

import json

from data.pairs.discovery.loader import load_discovery_cases
from eval.discovery import run_discovery, verify_artifacts


def test_discovery_corpus_has_twelve_cases_across_six_projects():
    cases = load_discovery_cases()

    assert len(cases) == 12
    assert len({case["project_id"] for case in cases}) == 6
    assert all(case["natural_variant"] is False for case in cases)


def test_offline_discovery_materializes_both_variants_and_behavior_results(tmp_path):
    result = run_discovery(
        mode="offline",
        replications=1,
        run_id="test-discovery",
        artifact_root=tmp_path,
    )
    bundle = tmp_path / "runs" / "test-discovery"

    assert result["episode_count"] == 48
    assert verify_artifacts(bundle)["episode_count"] == 48
    assert result["verification"]["schema_version"] == "requirements-smell-verification/v1"
    assert (bundle / "verification" / "decisions.jsonl").is_file()
    assert (bundle / "verification" / "metrics.json").is_file()
    assert (bundle / "verification" / "README.md").is_file()
    evaluation_metadata = [
        json.loads(line)
        for line in (bundle / "evaluation-metadata.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(evaluation_metadata) == 48
    assert all(set(row) == {"artifact_completed_at", "episode_id"} for row in evaluation_metadata)
    assert all(row["artifact_completed_at"] for row in evaluation_metadata)
    episodes = [
        json.loads(line)
        for line in (bundle / "episodes.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert all(episode.get("provenance_path") is None for episode in episodes)
    assert all("/Users/" not in json.dumps(episode) for episode in episodes)
    behavior = [episode for episode in episodes if episode["task_family"] == "behavior_codegen"]
    assert sum(episode["behavior_status"] == "passed" for episode in behavior if episode["variant"] == "clean") == 12
    assert sum(episode["behavior_status"] == "failed_target_condition" for episode in behavior if episode["variant"] == "smelly") == 12
    assert len(list((bundle / "generated-code").glob("*.py"))) == 24
    assert len(list((bundle / "comparisons").glob("*.md"))) == 12
    assert len(list((bundle / "observable-traces").glob("*.jsonl"))) == 48
    assert result["verification"]["eligible_count"] == 24
    for path in (bundle / "generated-code").glob("*.py"):
        content = path.read_bytes()
        assert content.endswith(b"\n")
        assert not content.endswith(b"\n\n")
    comparison = (bundle / "comparisons" / "arta-ertms-001.md").read_text(encoding="utf-8")
    assert "```diff\n" in comparison
    assert "\n-" in comparison
    assert "\n+" in comparison
    assert "allow'+" not in comparison


def test_offline_discovery_reports_deterministic_repeat_stability(tmp_path):
    result = run_discovery(
        mode="offline",
        replications=5,
        run_id="test-discovery-repeated",
        artifact_root=tmp_path,
    )
    bundle = tmp_path / "runs" / "test-discovery-repeated"

    assert result["episode_count"] == 240
    assert result["expected_episode_count"] == 240
    verification = result["verification"]
    assert verification["decision_count"] == 240
    assert verification["behavior_decision_count"] == 120
    assert verification["non_behavior_decision_count"] == 120
    assert verification["raw_eligible_count"] == 120
    assert verification["unique_eligible_count"] == 24
    assert verification["eligible_count"] == 24
    assert verification["replication_stability"]["observed_replications"] == [0, 1, 2, 3, 4]
    assert verification["replication_stability"]["all_repetitions_agree"] is True
    run = json.loads((bundle / "run.json").read_text(encoding="utf-8"))
    assert run["replication_kind"] == "deterministic_pipeline_repeat"
    assert run["independent_replication_claim"] is False
    assert run["expected_episode_count"] == 240
    assert (bundle / "evaluation-metadata.jsonl").is_file()
