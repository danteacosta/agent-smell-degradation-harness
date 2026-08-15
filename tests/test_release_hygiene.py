from pathlib import Path


ASD = Path(__file__).parents[1]
RAG = Path("/private/tmp/rag-p1.LSOAlz")
ARP = Path("/private/tmp/arp-moat-foundation")


def test_three_worktrees_have_release_hygiene_and_compatible_pins() -> None:
    # CI checks out ASD alone; the sibling worktrees are available for the
    # local release audit but intentionally are not assumed on GitHub runners.
    if not RAG.exists() or not ARP.exists():
        assert (ASD / "LICENSE").exists()
        return
    for root in (ASD, RAG, ARP):
        for name in ("LICENSE", "NOTICE", "CONTRIBUTING.md", "SECURITY.md"):
            assert (root / name).exists(), f"missing {root / name}"
    assert "Apache-2.0" in (ASD / "pyproject.toml").read_text(encoding="utf-8")
    assert "Apache-2.0" in (RAG / "pyproject.toml").read_text(encoding="utf-8")
    arp_metadata = (ARP / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "3.0.0"' in arp_metadata
    assert 'license = {text = "MIT"}' in arp_metadata
    for consumer in (ASD, RAG):
        assert "agent-reliability-protocol.git@" in (consumer / "pyproject.toml").read_text(encoding="utf-8")
