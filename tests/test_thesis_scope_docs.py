from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_masters_scope_freezes_conditional_claim_and_boundaries() -> None:
    scope = (ROOT / "docs" / "thesis" / "masters-scope.md").read_text(encoding="utf-8")
    for phrase in (
        "Acceptance-criteria generation",
        "planned conditional claims",
        "ΔPR-AUC >= 0.05",
        "unconditional floor is 60 independent",
        "12 projects",
        "6 test projects",
        "24 intents/6 projects is a pilot floor only",
        "two real provider/model configurations",
        "blinded primary human labels",
        "shadow pilot",
        "The product gate is a\ndemonstrator",
        "protocol-ready,\nempirically blocked",
    ):
        assert phrase in scope


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
