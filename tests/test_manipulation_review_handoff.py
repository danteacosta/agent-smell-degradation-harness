"""Exercise assignment isolation and drift rejection on the real review materials."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from eval.manipulation_review_handoff import prepare_assignment

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "data/prepilot/temporal-warning-manipulation-review-template.json"
CANDIDATES = ROOT / "data/prepilot/temporal-warning-source-drafts.json"


class ReviewHandoffTests(unittest.TestCase):
    def setUp(self):
        self.template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        self.candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))

    def test_each_assignment_contains_only_its_own_blank_forms(self):
        before = copy.deepcopy(self.template)
        for slot in ("reviewer_A", "reviewer_B"):
            packet = prepare_assignment(self.template, self.candidates, slot)
            self.assertEqual(packet["slot"], slot)
            self.assertNotIn("review_slots", packet)
            self.assertEqual(len(packet["reviews"]), len(self.candidates["records"]))
            self.assertFalse(packet["confirmatory_eligible"])
            packet["reviews"][0]["reason"] = "local answer"
        self.assertEqual(self.template, before)

    def test_candidate_content_drift_fails_even_with_identical_ids(self):
        self.candidates["extra"] = "changed source snapshot"
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            prepare_assignment(self.template, self.candidates, "reviewer_A")

    def test_rejects_completed_or_extra_fields_in_either_slot(self):
        for field, value in (("reason", "peer judgment"), ("generated_output", "leak")):
            for index in (0, 1):
                template = copy.deepcopy(self.template)
                template["review_slots"][index]["reviews"][0][field] = value
                with self.assertRaises(ValueError):
                    prepare_assignment(template, self.candidates, "reviewer_A")

    def test_rejects_missing_duplicate_or_unknown_slot(self):
        for names in (["reviewer_A"], ["reviewer_A", "reviewer_A"]):
            template = copy.deepcopy(self.template)
            template["review_slots"] = [
                {**template["review_slots"][0], "slot": name} for name in names]
            with self.assertRaises(ValueError):
                prepare_assignment(template, self.candidates, "reviewer_A")
        with self.assertRaises(ValueError):
            prepare_assignment(self.template, self.candidates, "unknown")

    def test_rejects_inventory_or_review_order_drift(self):
        for target in ("inventory", "rows"):
            template = copy.deepcopy(self.template)
            if target == "inventory":
                template["expected_candidate_ids"].reverse()
            else:
                template["review_slots"][0]["reviews"].reverse()
            with self.assertRaises(ValueError):
                prepare_assignment(template, self.candidates, "reviewer_A")

    def test_cli_preserves_existing_response_and_writes_single_slot(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "assignment.json"
            command = [sys.executable, "-m", "eval.manipulation_review_handoff",
                       "--template", str(TEMPLATE), "--candidates", str(CANDIDATES),
                       "--slot", "reviewer_B", "--output", str(output)]
            run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            packet = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(packet["slot"], "reviewer_B")
            self.assertNotIn("review_slots", packet)
            output.write_text("private completed response", encoding="utf-8")
            retry = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(retry.returncode, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "private completed response")


if __name__ == "__main__":
    unittest.main()
