"""Protect execution-plan denominators without imputing absent observations."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from eval.temporal_diagnostics import analyze

ROOT = Path(__file__).resolve().parents[1]


def episode(identifier="seen"):
    return {"episode_id": identifier, "intent_id": identifier, "terminal_ms": 100,
            "terminal_defect": False, "stages": [
                {"stage": s, "available_ms": t, "alert": False, "cost_microusd": 0}
                for s, t in (("T1", 10), ("T2", 30), ("T3", 50))]}


class TemporalCohortReconciliationTests(unittest.TestCase):
    def test_missing_entire_episode_remains_in_plan_without_fake_label_or_cost(self):
        rows = [episode()]
        before = copy.deepcopy(rows)
        report = analyze(rows, expected_episode_ids=["missing", "seen"])
        self.assertEqual(report["cohort_reconciliation"]["missing_episode_ids"], ["missing"])
        for horizon in report["horizons"].values():
            self.assertEqual(horizon["planned_episodes"], 2)
            self.assertEqual(horizon["supplied_episodes"], 1)
            self.assertEqual(horizon["missing_entire_episodes"], 1)
            self.assertEqual(horizon["complete_stage_episodes"], 1)
            self.assertEqual(horizon["missing_stage_episodes"], 0)
            self.assertIsNone(horizon["cost_microusd"])
            self.assertEqual(horizon["known_cost_microusd"], 0)
            self.assertEqual(horizon["missing_stage_bounds"]["nondefective"]["labeled_episodes"], 1)
            self.assertEqual(horizon["rate_scope"], "complete_stage_labeled_episodes")
        self.assertEqual(rows, before)
        self.assertFalse(report["confirmatory_eligible"])

    def test_no_plan_does_not_assert_complete_execution_coverage(self):
        report = analyze([episode()])
        self.assertEqual(report["cohort_reconciliation"]["scope"], "supplied_rows_only")
        self.assertIsNone(report["cohort_reconciliation"]["missing_episode_ids"])
        self.assertIsNone(report["horizons"]["T1"]["missing_entire_episodes"])
        self.assertEqual(report["horizons"]["T1"]["cost_microusd"], 0)

    def test_rejects_unknown_observations_and_malformed_plans(self):
        for plan in (["different"], ["seen", "seen"], [" seen"], [""], [1], "seen"):
            with self.subTest(plan=plan), self.assertRaises(ValueError):
                analyze([episode()], expected_episode_ids=plan)

    def test_empty_and_fully_missing_plans_preserve_undefined_rates(self):
        for plan in ([], ["missing"]):
            report = analyze([], expected_episode_ids=plan)
            self.assertEqual(report["cohort_reconciliation"]["missing_episode_ids"], plan)
            for horizon in report["horizons"].values():
                self.assertEqual(horizon["planned_episodes"], len(plan))
                self.assertIsNone(horizon["recall"])
                self.assertIsNone(horizon["false_alert_rate"])

    def test_plan_commitment_preserves_order_and_does_not_attest_authenticity(self):
        plan = ["missing", "seen"]
        report = analyze([episode()], expected_episode_ids=plan)
        commitment = report["cohort_reconciliation"]
        self.assertEqual(commitment["expected_episode_ids_sha256"], hashlib.sha256(
            json.dumps(plan, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest())
        self.assertFalse(commitment["plan_authenticity_verified"])
        reversed_report = analyze([episode()], expected_episode_ids=list(reversed(plan)))
        self.assertNotEqual(commitment["expected_episode_ids_sha256"],
                            reversed_report["cohort_reconciliation"]["expected_episode_ids_sha256"])

    def test_accounting_separates_partial_from_entirely_absent_episodes(self):
        partial = episode("partial")
        partial["stages"] = partial["stages"][:1]
        result = analyze([episode(), partial],
                         expected_episode_ids=["seen", "partial", "absent"])
        horizon = result["horizons"]["T1+T2"]
        self.assertEqual(horizon["planned_episodes"],
                         horizon["complete_stage_episodes"] + horizon["missing_stage_episodes"]
                         + horizon["missing_entire_episodes"])

    def test_cli_reconciles_plan_and_preserves_existing_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data, plan, output = [root / name for name in ("episodes.jsonl", "plan.json", "report.json")]
            data.write_text(json.dumps(episode()) + "\n", encoding="utf-8")
            plan.write_text(json.dumps(["seen", "absent"]), encoding="utf-8")
            command = [sys.executable, "-m", "eval.temporal_diagnostics", "--episodes", str(data),
                       "--expected-episode-ids", str(plan), "--output", str(output)]
            run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(output.read_text())["cohort_reconciliation"]["missing_episode_ids"],
                             ["absent"])
            original = output.read_bytes()
            retry = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(retry.returncode, 0)
            self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
