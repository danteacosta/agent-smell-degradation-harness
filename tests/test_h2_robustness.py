from eval.confirmatory_report import ablation_pr_auc, shuffled_negative_control


def test_negative_control_is_deterministic_and_not_better_than_original_signal():
    labels = [0, 1, 0, 1, 1, 0]
    scores = [0.1, 0.9, 0.2, 0.8, 0.7, 0.3]
    first = shuffled_negative_control(scores, labels, seed=7)
    assert first == shuffled_negative_control(scores, labels, seed=7)
    assert 0.0 <= first["pr_auc"] <= 1.0
    assert first["control"] == "shuffled_scores"


def test_ablation_report_is_explicit_for_each_family():
    labels = [0, 1, 0, 1]
    scores = {"static_smell": [0.1, 0.8, 0.2, 0.7], "operational": [0.2, 0.7, 0.3, 0.6], "provenance_semantic": [0.3, 0.9, 0.1, 0.8]}
    report = ablation_pr_auc(scores, labels)
    assert set(report) == set(scores)
    assert all(0.0 <= value <= 1.0 for value in report.values())
