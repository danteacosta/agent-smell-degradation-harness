from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_masters_scope_freezes_conditional_claim_and_boundaries() -> None:
    scope = (ROOT / "docs" / "thesis" / "masters-scope.md").read_text(encoding="utf-8")
    for phrase in (
        "Acceptance-criteria/test generation",
        "planned conditional claims",
        "ΔPR-AUC >= 0.05",
        "24 independent source intents",
        "6 projects",
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
    assert "24 independent source intents" in acquisition
    assert "no frozen human/adjudicated primary labels" in acquisition
