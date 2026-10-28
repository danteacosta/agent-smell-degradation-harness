"""Smoke tests for scripts/qp4_prospective_power.py (offline)."""
from scripts import qp4_prospective_power as pw


def test_requirement_table_has_25_rows_in_unit_interval():
    rows = pw.requirement_table()
    assert len(rows) == 25
    for r in rows:
        for k in ("complete1", "incomplete1", "incomplete5", "recovery"):
            assert 0.0 <= r[k] <= 1.0


def test_sign_flip_extremes():
    assert pw.sign_flip([[0.5], [0.5], [0.5]]) == 2 / 8
    assert pw.sign_flip([[0.0], [0.0]]) == 1.0


def test_simulate_is_deterministic():
    rows = pw.requirement_table()
    a = pw.simulate(rows, 10, 5, 1.0, 3)
    b = pw.simulate(rows, 10, 5, 1.0, 3)
    assert a == b
    assert set(a["power"]) == {"H-a", "H-b", "H-c"}
