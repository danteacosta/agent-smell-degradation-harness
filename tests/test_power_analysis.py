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
    assert first["method"].endswith("-v3")
    assert first["evaluation_scope"] == "test_partition_only"
    assert first["cluster_key"] == "project_id"
    assert first["design"]["intents"] == 60
    assert first["design"]["projects"] == 10
    assert first["design"]["split_project_quotas"] == {
        "train": 5,
        "calibration": 2,
        "test": 3,
    }
    assert 0 <= first["degenerate_rate"] <= 1
    assert first["median_ci_width"] >= 0


def test_h2_precision_uses_only_frozen_test_projects():
    result = simulate_h2_precision(
        intents=150,
        projects=30,
        simulations=2,
        bootstrap_draws=20,
        seed=13,
    )
    assert result["design"]["split_project_quotas"]["test"] == 9
    assert result["design"]["expected_test_intents"] == 45


def test_h2_precision_power_uses_every_planned_simulation_as_denominator():
    result = simulate_h2_precision(
        intents=6,
        projects=3,
        simulations=20,
        bootstrap_draws=20,
        seed=0,
    )

    assert result["completed_simulations"] == 11
    assert result["supported_simulations"] == 1
    assert result["estimated_margin_power"] == 1 / 20
    assert result["inferentially_valid_simulations"] == result["completed_simulations"]
    assert result["invalid_simulations"] == 9


def test_h2_precision_rejects_simulations_that_can_resample_one_class():
    result = simulate_h2_precision(
        intents=12,
        projects=6,
        simulations=20,
        bootstrap_draws=20,
        seed=0,
    )

    assert result["bootstrap_degenerate_support_simulations"] > 0
    assert result["inferentially_valid_simulations"] + result["invalid_simulations"] == 20
    assert result["invalid_simulations"] == (
        result["observed_single_class_simulations"]
        + result["bootstrap_degenerate_support_simulations"]
    )
    assert result["estimated_margin_power"] == result["supported_simulations"] / 20
