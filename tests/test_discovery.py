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
    episodes = [
        json.loads(line)
        for line in (bundle / "episodes.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
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
