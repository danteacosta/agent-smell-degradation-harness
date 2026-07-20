from pathlib import Path

from eval.dissertation_bundle import write_dissertation_bundle
from protocol.packaging import build_dissertation_bundle, render_bundle_summary
from protocol.reliability import synthetic_agreement_demo


def test_synthetic_agreement_demo_documents_limitation():
    demo = synthetic_agreement_demo(seed=42)
    assert 0.0 <= demo["agreement_rate"] <= 1.0
    assert demo["synthetic"] is True
    assert "not derived from human" in demo["limitation"].lower()


def test_build_dissertation_bundle_exports_required_sections(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    bundle = build_dissertation_bundle(repo_root, tmp_path / "work")

    assert bundle["design_spec_path"].endswith(
        "2026-07-20-agent-smell-degradation-harness-design.md"
    )
    assert bundle["pair_inventory"]
    assert bundle["intent_ids"]
    assert bundle["taxonomy_modes"]
    assert bundle["analysis_summary"]["effect_detected"] is True
    assert "mitigation_beneficial" in bundle["mitigation_summary"]
    assert bundle["paired_stats"]["proportion_diff"] > 0.0
    assert bundle["reliability"]["synthetic"] is True


def test_render_bundle_summary_includes_mitigation_and_limitation(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    bundle = build_dissertation_bundle(repo_root, tmp_path / "work")
    summary = render_bundle_summary(bundle)

    assert "Mitigation beneficial" in summary
    assert "Synthetic demo only" in summary


def test_write_dissertation_bundle_writes_json_and_summary(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    output_path = tmp_path / "dissertation_bundle.json"
    summary_path = tmp_path / "BUNDLE_SUMMARY.md"

    bundle = write_dissertation_bundle(
        repo_root,
        tmp_path / "work",
        output_path,
        summary_path,
    )

    assert output_path.exists()
    assert summary_path.exists()
    assert bundle["artifact_paths"]["mitigation_report"] == "eval/mitigation_report.json"
