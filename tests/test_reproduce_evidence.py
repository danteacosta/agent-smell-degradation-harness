from __future__ import annotations

from scripts import reproduce_evidence


def test_every_public_row_matches_the_stated_number() -> None:
    rows = reproduce_evidence.build()
    assert [r for r in rows if r["status"] == "mismatch"] == []
    assert sum(r["status"] == "reproduced" for r in rows) == 6


def test_main_exits_nonzero_on_a_mismatch(monkeypatch) -> None:
    monkeypatch.setattr(reproduce_evidence, "build",
                        lambda: [{"row": "x", "stated": "1", "recomputed": "2", "status": "mismatch", "source": "s"}])
    assert reproduce_evidence.main([]) == 1
