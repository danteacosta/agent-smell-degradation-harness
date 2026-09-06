"""Offline regression controls; runnable with unittest or pytest."""
import json
import subprocess
import sys
import unittest

from label_plane.judge_controls import build_controls, score_controls
from label_plane.exploratory_judge import parse_judge_response, validate_judge_request

CONFIG = "a" * 64


def records(always_clean=False):
    pack = build_controls()
    return [{"pack_sha256": pack["pack_sha256"], "configuration_sha256": CONFIG,
             "replication_id": 0, "occurrence_id": c["request"]["occurrence_id"],
             "raw_response": json.dumps({"label": "clean" if always_clean or c["oracle"]["covered"] else "moderate",
                                         "status": "covered" if always_clean or c["oracle"]["covered"] else "omitted"})}
            for c in pack["cases"]]


class JudgeControlsTests(unittest.TestCase):
    def test_pack_is_deterministic_blinded_and_balanced(self):
        pack = build_controls()
        self.assertEqual(pack, build_controls())
        self.assertEqual(len(pack["cases"]), 12)
        self.assertEqual(sum(c["oracle"]["covered"] for c in pack["cases"]), 6)
        for case in pack["cases"]:
            validate_judge_request(case["request"])
            self.assertNotIn("oracle", case["request"])
            self.assertNotIn(case["oracle"]["operation"], case["request"]["occurrence_id"])

    def test_exact_oracle_cannot_authorize_confirmation(self):
        report = score_controls(records(), [CONFIG], 1)
        self.assertFalse(report["confirmatory_eligible"])
        self.assertEqual(report["human_calibration"], "absent")
        self.assertEqual(report["configurations"][CONFIG]["correct_over_planned"], 1)

    def test_constant_clean_fails_negative_controls_despite_perfect_stability(self):
        score = score_controls(records(True), [CONFIG], 1)["configurations"][CONFIG]
        self.assertEqual(score["correct_over_planned"], 0.5)
        self.assertEqual(score["false_covered"], 6)
        self.assertEqual(score["order_switch_rate"], 0)
        self.assertEqual(score["by_operation"]["deleted"]["correct"], 0)

    def test_failures_missing_and_abstentions_do_not_disappear(self):
        rows = records()[:-1]
        rows[0]["raw_response"] = None
        rows[1]["raw_response"] = "not json"
        rows[2]["raw_response"] = '{"label":"not_visible","status":"uncertain"}'
        score = score_controls(rows, [CONFIG], 1)["configurations"][CONFIG]
        for key, expected in {"planned": 12, "missing": 1, "invalid_or_failed": 2,
                              "abstained": 1, "correct": 8}.items():
            self.assertEqual(score[key], expected)

    def test_empty_results_are_not_perfect_robustness(self):
        score = score_controls([], [CONFIG], 1)["configurations"][CONFIG]
        self.assertEqual(score["missing"], 12)
        self.assertIsNone(score["order_switch_rate"])
        self.assertEqual(score["correct_over_planned"], 0)

    def test_order_switch_is_counted(self):
        rows = records()
        rows[1]["raw_response"] = '{"label":"moderate","status":"omitted"}'
        score = score_controls(rows, [CONFIG], 1)["configurations"][CONFIG]
        self.assertEqual(score["order_switches"], 1)
        self.assertEqual(score["order_pairs_completed"], 3)

    def test_rejects_unplanned_or_malformed_records(self):
        for field, value in [("pack_sha256", "wrong"), ("configuration_sha256", "b"*64),
                             ("replication_id", True), ("replication_id", -1),
                             ("occurrence_id", "unknown"), ("raw_response", {})]:
            with self.subTest(field=field, value=value):
                rows = records()
                rows[0][field] = value
                with self.assertRaises(ValueError):
                    score_controls(rows, [CONFIG], 1)

    def test_rejects_duplicates_and_invalid_plans(self):
        with self.assertRaises(ValueError):
            score_controls(records() + records()[:1], [CONFIG], 1)
        for configs, reps in [([], 1), ([CONFIG, CONFIG], 1), (["model"], 1), ([CONFIG], True)]:
            with self.assertRaises(ValueError):
                score_controls([], configs, reps)

    def test_configurations_are_not_pooled(self):
        reports = score_controls(records(), [CONFIG, "b"*64], 1)["configurations"]
        self.assertEqual(reports[CONFIG]["completed"], 12)
        self.assertEqual(reports["b"*64]["missing"], 12)

    def test_compact_response_cannot_silently_drop_second_constraint(self):
        request = build_controls()["cases"][0]["request"]
        request["reference_constraints"].append({"constraint_id": "c2", "text": "The header is blue."})
        with self.assertRaisesRegex(ValueError, "exactly one"):
            parse_judge_response('{"label":"clean","status":"covered"}', request)

    def test_cli_emits_only_requests_without_oracles(self):
        result = subprocess.run([sys.executable, "scripts/judge_controls.py", "requests"],
                                capture_output=True, text=True, check=True)
        requests = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(requests), 12)
        for request in requests:
            validate_judge_request(request)


if __name__ == "__main__":
    unittest.main()
