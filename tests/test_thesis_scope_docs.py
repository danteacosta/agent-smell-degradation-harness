import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_machine_readable_protocol_records_claim_and_boundaries() -> None:
    precision = json.loads(
        (ROOT / "data" / "confirmatory" / "precision-plan.candidate.json").read_text(
            encoding="utf-8"
        )
    )
    sensitivity = json.loads(
        (
            ROOT
            / "data"
            / "confirmatory"
            / "precision-sensitivity.candidate.json"
        ).read_text(encoding="utf-8")
    )
    rubric = json.loads(
        (ROOT / "tasks" / "annotation_rubric.json").read_text(encoding="utf-8")
    )
    boundary = (ROOT / "docs" / "thesis-product-boundary.md").read_text(
        encoding="utf-8"
    )

    assert precision["status"] == "rejected"
    assert precision["simulation"]["method"].endswith("-v2")
    assert precision["decision"] == "rejected_do_not_freeze"
    assert sensitivity["status"] == "historical_v2_diagnostic_rejected_for_freeze"
    assert "v3" in sensitivity["interpretation"]
    assert precision["design"]["intents"] >= 60
    assert precision["design"]["projects"] >= 12
    assert precision["design"]["minimum_test_projects"] >= 6
    assert precision["design"]["minimum_test_intents"] >= 24
    assert precision["assumptions"]["practical_margin"] == 0.05
    assert rubric["duplicate_subset_fraction"] == 0.2
    assert rubric["secondary_llm_judges"] == "exploratory_only"
    assert "conditional claim" in boundary
    assert "non-confirmatory" in boundary


def test_boundary_links_external_gate_and_non_confirmatory_status() -> None:
    boundary = (ROOT / "docs" / "thesis-product-boundary.md").read_text(encoding="utf-8")
    acquisition = (ROOT / "docs" / "research" / "confirmatory-data-acquisition.md").read_text(encoding="utf-8")
    assert "planned confirmatory experiment" in boundary
    assert "non-confirmatory" in boundary
    assert "60 independent intents" in acquisition
    assert "220 intents/36 projects failed the v3" in acquisition
    assert "288-intent/36-project design is only an unfrozen central-effect candidate" in acquisition
    assert "latent score parameter, not a ΔPR-AUC effect size" in acquisition
    assert "no frozen human/adjudicated primary labels" in acquisition


def test_e2e_endpoint_is_not_mislabeled_as_the_h1_estimand() -> None:
    boundary = (ROOT / "docs" / "thesis-product-boundary.md").read_text(
        encoding="utf-8"
    )
    matrix = (
        ROOT / "docs" / "thesis" / "e2e-evidence-matrix-20260925.md"
    ).read_text(encoding="utf-8")

    for text in (boundary, matrix):
        prose = " ".join(text.split())
        assert "target-failure contrast" in prose
        assert "does not estimate `H1.ordinal_delta`" in prose
        assert "primary, co-primary, or construct-validation" in prose


def test_roadmap_reports_current_six_project_e2e_boundary() -> None:
    roadmap = (
        ROOT / "docs" / "research" / "research-product-roadmap.md"
    ).read_text(encoding="utf-8")
    prose = " ".join(roadmap.split())

    assert "informative browser outcomes in six projects" in prose
    assert "53 of 54" in prose
    assert "target-failure contrast" in prose
    assert "does not estimate `H1.ordinal_delta`" in prose


def test_prepilot_launch_pack_preserves_claim_boundary() -> None:
    launch = (ROOT / "docs" / "research" / "prepilot-launch-pack.md").read_text(encoding="utf-8")
    for phrase in (
        "non-confirmatory 120-episode",
        "two distinct real provider/model configurations",
        "It cannot support H1 or H2",
        "Credentials never enter that file",
        "The rejected 220/36 candidate must not be frozen",
    ):
        assert phrase in launch
