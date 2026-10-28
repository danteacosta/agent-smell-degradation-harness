"""Smoke tests for scripts/qp4_prospective_power.py (offline)."""
from scripts import qp4_prospective_power as pw


def test_requirement_table_has_25_rows_in_unit_interval():
    rows = pw.requirement_table()
    assert len(rows) == 25
    for r in rows:
        for k in ("complete_score", "incomplete_score", "complete1", "incomplete1", "incomplete5", "recovery"):
            assert 0.0 <= r[k] <= 1.0


def test_sign_flip_extremes():
    assert pw.sign_flip([[0.5], [0.5], [0.5]]) == 2 / 8
    assert pw.sign_flip([[0.0], [0.0]]) == 1.0


def test_simulate_is_deterministic():
    rows = pw.requirement_table()
    a = pw.simulate(rows, 10, 5, 1.0, 3)
    b = pw.simulate(rows, 10, 5, 1.0, 3)
    assert a == b
    assert {"H-a", "H-b", "H-c"} <= set(a["power"])


def test_sign_flip_is_invariant_to_positive_scaling():
    # Regression for the v1 error: scaling every contrast by f > 0 cannot change p.
    groups = [[0.3, -0.1], [0.2], [0.05, 0.4], [-0.2], [0.1]]
    for f in (0.5, 0.1, 3.0):
        assert pw.sign_flip([[f * v for v in g] for g in groups]) == pw.sign_flip(groups)


def test_attenuation_reduces_power_on_common_draws():
    rows = pw.requirement_table()
    full = pw.simulate(rows, 16, 8, 1.0, 60)
    half = pw.simulate(rows, 16, 8, 0.5, 60)
    null = pw.simulate(rows, 16, 8, 0.0, 60)
    for h in ("H-a", "H-b"):
        assert null["power"][h] <= half["power"][h] <= full["power"][h]
    assert abs(null["mean_effect"]["H-a"]) < 1e-12


def test_holm_two():
    assert pw.holm_two(0.01, 0.04) == (True, True)
    assert pw.holm_two(0.03, 0.04) == (False, False)
    assert pw.holm_two(0.04, 0.02) == (True, True)
    assert pw.holm_two(0.02, 0.06) == (True, False)
