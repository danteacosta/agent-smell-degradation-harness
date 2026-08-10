from pathlib import Path


ASD = Path(__file__).parents[1]
RAG = Path("/private/tmp/rag-p1.LSOAlz")
ARP = Path("/private/tmp/arp-moat-foundation")


def test_three_worktrees_have_release_hygiene_and_compatible_pins() -> None:
    for root in (ASD, RAG, ARP):
        for name in ("LICENSE", "NOTICE", "CONTRIBUTING.md", "SECURITY.md"):
            assert (root / name).exists(), f"missing {root / name}"
    assert "Apache-2.0" in (ASD / "pyproject.toml").read_text(encoding="utf-8")
    assert "Apache-2.0" in (RAG / "pyproject.toml").read_text(encoding="utf-8")
    arp_metadata = (ARP / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "2.0.6"' in arp_metadata
    assert 'license = {text = "MIT"}' in arp_metadata
    for consumer in (ASD, RAG):
        assert "agent-reliability-protocol.git@v2.0.6" in (consumer / "pyproject.toml").read_text(encoding="utf-8")
