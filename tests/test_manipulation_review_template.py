"""Protect the real, unfilled manipulation-review handoff from silent drift."""
import hashlib
import json
from pathlib import Path
import unittest

from eval.manipulation_admission import (
    REQUIRED, candidate_inventory_sha256, prepare_manipulation_admission,
)

ROOT = Path(__file__).resolve().parents[1]


class ManipulationReviewTemplateTests(unittest.TestCase):
    def setUp(self):
        self.template = json.loads((ROOT / "data/prepilot/temporal-warning-manipulation-review-template.json").read_text(encoding="utf-8"))
        self.candidates = json.loads((ROOT / "data/prepilot/temporal-warning-source-drafts.json").read_text(encoding="utf-8"))

    def test_template_binds_current_materials_and_covers_each_candidate_twice(self):
        template = self.template
        raw = json.dumps(self.candidates, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.assertEqual(hashlib.sha256(raw).hexdigest(), template["candidate_content_sha256"])
        ids = [row["intent_id"] for row in self.candidates["records"]]
        self.assertEqual(template["expected_candidate_ids"], ids)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(template["review_slots"]), 2)
        for slot in template["review_slots"]:
            self.assertEqual([row["candidate_id"] for row in slot["reviews"]], ids)
        self.assertFalse(template["confirmatory_eligible"])

    def test_unfilled_forms_cannot_masquerade_as_independent_reviews(self):
        rows = [row for slot in self.template["review_slots"] for row in slot["reviews"]]
        for row in rows:
            self.assertEqual(set(row), set(REQUIRED))
            self.assertTrue(all(row[key] is None for key in REQUIRED if key != "candidate_id"))
        with self.assertRaisesRegex(ValueError, "reviewer_id"):
            prepare_manipulation_admission(rows, expected_candidate_ids=self.template["expected_candidate_ids"])
        # A slot's routing label is never accepted as a completed human judgment.
        self.assertEqual(len(candidate_inventory_sha256(self.template["expected_candidate_ids"])), 64)


if __name__ == "__main__":
    unittest.main()
