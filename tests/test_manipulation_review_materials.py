"""Review inputs are projected from the pinned candidate snapshot, never label metadata."""
import copy
import hashlib
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


class ReviewMaterialProjectionTests(unittest.TestCase):
    def setUp(self):
        self.template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        self.candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))

    def rebind(self):
        raw = json.dumps(self.candidates, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
        self.template["candidate_content_sha256"] = hashlib.sha256(raw).hexdigest()

    def test_materials_cover_exact_inputs_and_do_not_mutate_the_source(self):
        original = copy.deepcopy(self.candidates)
        packet = prepare_assignment(self.template, self.candidates, "reviewer_A",
                                    include_materials=True)
        self.assertEqual([m["candidate_id"] for m in packet["materials"]],
                         self.template["expected_candidate_ids"])
        for material, candidate in zip(packet["materials"], self.candidates["records"]):
            self.assertEqual(material["reference_excerpt"], candidate["variants"]["clean"])
            self.assertEqual(material["proposed_remainder"], candidate["variants"]["defective"])
            self.assertEqual(material["source_reference"]["sha256"], candidate["source"]["sha256"])
            self.assertEqual(set(material), {"candidate_id", "project_id", "source_reference",
                                             "reference_excerpt", "proposed_remainder"})
        self.assertTrue(packet["materials_are_proposals_not_labels"])
        self.assertFalse(packet["source_files_reverified"])
        self.assertFalse(packet["confirmatory_eligible"])
        packet["materials"][0]["source_reference"]["url"] = "local edit"
        self.assertEqual(self.candidates, original)

    def test_outcomes_exposure_and_proposed_target_answers_are_not_copied(self):
        sentinel = "PRIVATE-OUTCOME-SENTINEL"
        candidate = self.candidates["records"][0]
        candidate["generated_output"] = sentinel
        candidate["review"]["private_judgment"] = sentinel
        candidate["exposure"]["private_note"] = sentinel
        candidate["target"]["obligation"] = sentinel
        candidate["source"]["private_metadata"] = sentinel
        self.rebind()
        packet = prepare_assignment(self.template, self.candidates, "reviewer_B",
                                    include_materials=True)
        self.assertNotIn(sentinel, json.dumps(packet))
        self.assertNotIn("reviewer_A", json.dumps(packet))

    def test_default_remains_form_only_and_nested_locator_payloads_are_rejected(self):
        packet = prepare_assignment(self.template, self.candidates, "reviewer_A")
        self.assertNotIn("materials", packet)
        self.candidates["records"][0]["source"]["url"] = {"generated_output": "leak"}
        self.rebind()
        with self.assertRaisesRegex(ValueError, "scalar locators"):
            prepare_assignment(self.template, self.candidates, "reviewer_A",
                               include_materials=True)

    def test_cli_attaches_materials_and_preserves_blank_judgments(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "assignment.json"
            command = [sys.executable, "-m", "eval.manipulation_review_handoff",
                       "--template", str(TEMPLATE), "--candidates", str(CANDIDATES),
                       "--slot", "reviewer_B", "--include-materials", "--output", str(output)]
            run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            packet = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(len(packet["materials"]), len(packet["reviews"]))
            for row in packet["reviews"]:
                self.assertTrue(all(value is None for key, value in row.items()
                                    if key != "candidate_id"))


if __name__ == "__main__":
    unittest.main()
