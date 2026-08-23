from protocol.power import estimate_sign_flip_power, sensitivity_table, simulate_h2_precision


def test_power_analysis_is_deterministic_and_cluster_based():
    first = estimate_sign_flip_power(simulations=20, seed=11)
    second = estimate_sign_flip_power(simulations=20, seed=11)
    assert first == second
    assert first["n_clusters"] == 12
    assert 0 <= first["estimated_power"] <= 1


def test_power_sensitivity_table_freezes_effect_grid():
    table = sensitivity_table((0.25, 0.5), simulations=10, seed=3)
    assert [row["standardized_effect"] for row in table] == [0.25, 0.5]
    assert all(row["method"].endswith("-v2") for row in table)


def test_large_h1_design_uses_bounded_monte_carlo_randomization():
    result = estimate_sign_flip_power(
        n_clusters=60, simulations=3, seed=5, monte_carlo_draws=200
    )
    assert "monte_carlo" in result["method"]
    assert result["monte_carlo_draws"] == 200


def test_h2_precision_simulation_is_deterministic_and_project_clustered():
    first = simulate_h2_precision(
        intents=60, projects=10, simulations=5, bootstrap_draws=30, seed=7
    )
    second = simulate_h2_precision(
        intents=60, projects=10, simulations=5, bootstrap_draws=30, seed=7
    )
    assert first == second
    assert first["design"] == {"intents": 60, "projects": 10}
    assert 0 <= first["degenerate_rate"] <= 1
    assert first["median_ci_width"] >= 0
