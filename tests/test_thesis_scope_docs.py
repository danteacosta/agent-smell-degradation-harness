import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_machine_readable_protocol_freezes_claim_and_boundaries() -> None:
    precision = json.loads(
        (ROOT / "data" / "confirmatory" / "precision-plan.candidate.json").read_text(
            encoding="utf-8"
        )
    )
    rubric = json.loads(
        (ROOT / "tasks" / "annotation_rubric.json").read_text(encoding="utf-8")
    )
    boundary = (ROOT / "docs" / "thesis-product-boundary.md").read_text(
        encoding="utf-8"
    )

    assert precision["status"] == "candidate"
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
    assert "current\n   conservative candidate is 220 intents/36 projects" in acquisition
    assert "no frozen human/adjudicated primary labels" in acquisition


def test_prepilot_launch_pack_preserves_claim_boundary() -> None:
    launch = (ROOT / "docs" / "research" / "prepilot-launch-pack.md").read_text(encoding="utf-8")
    for phrase in (
        "non-confirmatory 120-episode",
        "two distinct real provider/model configurations",
        "It cannot support H1 or H2",
        "Credentials never enter that file",
        "The current 220/36 candidate may increase or decrease",
    ):
        assert phrase in launch
