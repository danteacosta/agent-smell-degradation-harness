import json
import random

from scripts import confirmatory_power as cp


def test_pool_matches_the_published_estimate():
    pool = cp.observed_pool(cp.ROOT / "data/selection-abc-results/20261003", cp.ROOT / "data/abc-cases")
    assert len(pool) == 9 and sum(len(v) for v in pool.values()) == 44
    assert abs(cp.pool_estimate(pool) - 0.7254) < 1e-3
    assert all(s in (0.5, 1.0) for reqs in pool.values() for r in reqs for s in r)  # no reversal observed


def test_attenuation_and_noise():
    rng = random.Random(0)
    assert cp.attenuate([1.0, 0.5, 1.0], 1.0, rng) == [0.5, 0.5, 0.5]
    assert cp.attenuate([1.0, 0.5], 0.0, rng) == [1.0, 0.5]
    redrawn = [s for _ in range(2000) for s in cp.attenuate([0.5], 0.0, rng, noise=1.0)]
    assert set(redrawn) == {0.0, 1.0} and 0.4 < redrawn.count(1.0) / len(redrawn) < 0.6


def test_null_grid_rejects_rarely():
    pool = {"a": [[0.5] * 4, [1.0] * 4], "b": [[0.5] * 4, [1.0, 0.5, 0.5, 0.5]], "c": [[1.0] * 4]}
    row = cp.power_grid(pool, [(6, 3)], [1.0], [0.05], simulations=60, seed=1, n_boot=200, n_perm=400)[0]
    assert abs(row["mean_estimate"] - 0.5) < 0.02
    assert row["power_intent_p_below_05_optimistic"] <= 0.1
    assert row["power_project_p_below_05"] <= 0.1


def test_project_sign_flip_does_not_treat_requirements_as_independent():
    rows = []
    for project in ("p1", "p2"):
        for requirement in range(20):
            rows.append({
                "intent_id": f"{project}-r{requirement}",
                "project_id": project,
                "clean_severity": 0,
                "defective_severity": 1,
            })
    # Forty same-direction requirements still provide only two independent
    # project signs: the exact two-sided p-value is 2 / 2**2.
    assert cp.project_sign_flip_pvalue(rows) == 0.5


def test_project_sign_flip_preserves_original_requirement_weighting():
    rows = [
        {"intent_id": "a1", "project_id": "a", "clean_severity": 0, "defective_severity": 1},
        {"intent_id": "a2", "project_id": "a", "clean_severity": 0, "defective_severity": 1},
        {"intent_id": "b1", "project_id": "b", "clean_severity": 1, "defective_severity": 0},
    ]
    # Project a contributes twice to the equal-requirement estimand. The exact
    # distribution flips that whole contribution together, rather than first
    # changing the estimand to an equal-project mean.
    assert cp.project_sign_flip_pvalue(rows) == 1.0


def test_published_exploratory_result_has_project_level_sensitivity():
    from scripts import selected46_report as rep

    configs = rep.load_configs(cp.ROOT / "data/abc-cases")
    rows = rep.pairs(
        rep.load_results(cp.ROOT / "data/selection-abc-results/20261003", configs),
        configs,
        "A",
        "C",
        "drop",
    )
    assert len(rows) == 172
    assert len({row["intent_id"] for row in rows}) == 44
    assert len({row["project_id"] for row in rows}) == 9
    assert cp.project_sign_flip_pvalue(rows) == 0.00390625


def test_published_power_grid_uses_project_level_gate():
    report = json.loads((cp.ROOT / "data/confirmatory-planning/power.json").read_text())
    assert report["schema_version"] == "confirmatory-power/v2"
    assert report["decision_rule"].startswith("project-level exact sign flip")
    assert len(report["grid"]) == 64
    row = next(
        item
        for item in report["grid"]
        if item["noise"] == 0.14
        and item["attenuation_q"] == 5 / 9
        and item["projects"] == 8
        and item["requirements_per_project"] == 5
    )
    assert row["power_project_p_below_05"] == 0.835
    assert row["power_both_project"] == 0.835
    assert row["power_intent_p_below_05_optimistic"] == 0.963
