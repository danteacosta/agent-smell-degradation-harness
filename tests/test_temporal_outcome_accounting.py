"""Check temporal diagnostic polarity, denominators and observed lead-time labels."""
import copy
import itertools
import unittest

from eval.temporal_diagnostics import analyze


def episode(identifier, defect, alert):
    return {"episode_id": identifier, "intent_id": identifier, "terminal_ms": 100,
            "terminal_defect": defect, "stages": [
                {"stage": stage, "available_ms": time, "alert": alert if stage == "T2" else False,
                 "cost_microusd": 0}
                for stage, time in (("T1", 10), ("T2", 30), ("T3", 50))]}


class TemporalOutcomeAccountingTests(unittest.TestCase):
    def test_full_confusion_accounting_and_label_polarity(self):
        rows = [episode(str(i), defect, alert)
                for i, (defect, alert) in enumerate(itertools.product((True, False), repeat=2))]
        result = analyze(rows)["horizons"]["T1+T2+T3"]
        self.assertEqual(result["positive_class"], "terminal_defect=true")
        self.assertEqual(result["defective_labeled_episodes"], 2)
        self.assertEqual(result["nondefective_labeled_episodes"], 2)
        for field in ("true_alerts", "false_alerts", "missed_defects", "nondefective_without_alert"):
            self.assertEqual(result[field], 1)
        self.assertEqual(result["recall"], 0.5)
        self.assertEqual(result["false_alert_rate"], 0.5)

    def test_unlabeled_alert_does_not_enter_either_rate_denominator(self):
        rows = [episode("positive", True, True), episode("negative", False, False),
                episode("unknown", None, True)]
        result = analyze(rows)["horizons"]["T1+T2"]
        self.assertEqual(result["alerts"], 2)
        self.assertEqual(result["outcome_labeled_episodes"], 2)
        self.assertEqual(result["recall"], 1)
        self.assertEqual(result["false_alert_rate"], 0)
        self.assertEqual(result["missing_stage_bounds"]["unlabeled_episodes"], 1)

    def test_missing_stage_keeps_recall_complete_case_and_bounds_separate(self):
        complete = episode("complete", True, True)
        incomplete = episode("incomplete", True, False)
        incomplete["stages"] = incomplete["stages"][:1]
        report = analyze([complete, incomplete])
        result = report["horizons"]["T1+T2"]
        self.assertEqual(result["rate_scope"], "complete_stage_labeled_episodes")
        self.assertEqual(result["defective_labeled_episodes"], 1)
        self.assertEqual(result["recall"], 1)
        bounds = result["missing_stage_bounds"]["defective"]
        self.assertEqual(bounds["labeled_episodes"], 2)
        self.assertEqual((bounds["alert_rate_lower"], bounds["alert_rate_upper"]), (0.5, 1))
        self.assertEqual(report["episodes"][1]["alert_outcome"], "no_observed_alert")

    def test_zero_denominators_remain_undefined(self):
        for rows in ([], [episode("unknown", None, True)]):
            for result in analyze(rows)["horizons"].values():
                self.assertIsNone(result["recall"])
                self.assertIsNone(result["false_alert_rate"])

    def test_lead_times_are_labeled_without_claiming_unobserved_earlier_alerts(self):
        rows = [episode("true", True, True), episode("false", False, True),
                episode("unknown", None, True), episode("none", True, False)]
        rows[0]["stages"] = rows[0]["stages"][1:]  # T1 unavailable.
        before = copy.deepcopy(rows)
        report = analyze(rows)
        self.assertEqual(report["output_plane"], "label_joined_diagnostics_not_features")
        self.assertEqual([r["alert_outcome"] for r in report["episodes"]],
                         ["true_alert", "false_alert", "unlabeled_alert", "no_observed_alert"])
        self.assertFalse(report["episodes"][0]["first_alert_prefix_complete"])
        self.assertEqual([r["lead_time_ms"] for r in report["episodes"]], [70, 70, 70, None])
        self.assertEqual(rows, before)
        self.assertFalse(report["confirmatory_eligible"])

    def test_asymmetric_rates_cannot_be_swapped_by_correctness_positive_convention(self):
        rows = [episode("p1", True, True), episode("p2", True, False),
                episode("n", False, True)]
        result = analyze(rows)["horizons"]["T1+T2"]
        self.assertEqual(result["recall"], 0.5)
        self.assertEqual(result["false_alert_rate"], 1)


if __name__ == "__main__":
    unittest.main()
