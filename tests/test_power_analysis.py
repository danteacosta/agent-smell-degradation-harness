from protocol.power import estimate_sign_flip_power, sensitivity_table


def test_power_analysis_is_deterministic_and_cluster_based():
    first = estimate_sign_flip_power(simulations=20, seed=11)
    second = estimate_sign_flip_power(simulations=20, seed=11)
    assert first == second
    assert first["n_clusters"] == 12
    assert 0 <= first["estimated_power"] <= 1


def test_power_sensitivity_table_freezes_effect_grid():
    table = sensitivity_table((0.25, 0.5), simulations=10, seed=3)
    assert [row["standardized_effect"] for row in table] == [0.25, 0.5]
    assert all(row["method"].endswith("-v1") for row in table)
