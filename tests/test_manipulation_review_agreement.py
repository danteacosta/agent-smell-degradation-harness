"""Hand-computed synthetic decisions test descriptive reporting, never thesis labels."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from eval.manipulation_review_agreement import summarize_agreement

ROOT = Path(__file__).resolve().parents[1]


def rows_for(pairs):
    return [{"candidate_id": f"c-{i}", "reviewer_id": reviewer,
             "removed_span": "after approval", "target_constraint_id": f"c-{i}-c01",
             "dependent_constraint_ids": [], "non_target_obligations_preserved": True,
             "plausible_remainder": True, "decision": decision, "reason": "Synthetic test only."}
            for i, pair in enumerate(pairs) for reviewer, decision in zip(("r-1", "r-2"), pair)]


class AgreementTests(unittest.TestCase):
    def summarize(self, rows, n):
        return summarize_agreement(rows, expected_candidate_ids=[f"c-{i}" for i in range(n)])

    def test_hand_computed_confusion_and_kappa(self):
        rows = rows_for([("admit", "admit"), ("admit", "exclude"),
                         ("exclude", "exclude"), ("uncertain", "uncertain")])
        report = self.summarize(rows, 4)
        decision = report["decision_agreement"]
        self.assertEqual(decision["matrix_rows_reviewer_0_columns_reviewer_1"],
                         [[1, 1, 0], [0, 1, 0], [0, 0, 1]])
        self.assertEqual(decision["observed_agreement"], 3 / 4)
        self.assertEqual(decision["expected_agreement_from_marginals"], 5 / 16)
        self.assertAlmostEqual(decision["cohen_kappa_unweighted_nominal"], 7 / 11)
        self.assertEqual(report["field_agreement"]["decision"]["candidate_denominator"], 4)
        self.assertEqual(report["field_agreement"]["decision"]["agreeing_candidates"], 3)
        self.assertFalse(report["confirmatory_eligible"])

    def test_constant_consensus_is_not_a_defined_kappa(self):
        report = self.summarize(rows_for([("admit", "admit")] * 3), 3)
        self.assertEqual(report["decision_agreement"]["observed_agreement"], 1)
        self.assertIsNone(report["decision_agreement"]["cohen_kappa_unweighted_nominal"])
        self.assertEqual(report["decision_agreement"]["kappa_undefined_reason"], "degenerate_marginals")

    def test_systematic_disagreement_can_be_negative(self):
        report = self.summarize(rows_for([("admit", "exclude"), ("exclude", "admit")]), 2)
        self.assertEqual(report["decision_agreement"]["cohen_kappa_unweighted_nominal"], -1)

    def test_same_reviewer_pair_required_without_selective_case_deletion(self):
        rows = rows_for([("admit", "exclude"), ("exclude", "admit")])
        rows[-1]["reviewer_id"] = "r-3"
        with self.assertRaisesRegex(ValueError, "same two reviewers"):
            self.summarize(rows, 2)
        with self.assertRaises(ValueError):
            self.summarize(rows_for([("admit", "exclude")]), 2)
        with self.assertRaises(ValueError):
            self.summarize([], 0)

    def test_blank_leaked_and_duplicate_reviews_fail_validation(self):
        for mutation in (lambda r: r.update(decision=None),
                         lambda r: r.update(provider="forbidden"),
                         lambda r: r.update(reviewer_id="R-1")):
            rows = rows_for([("admit", "exclude")])
            mutation(rows[-1])
            with self.assertRaises(ValueError):
                self.summarize(rows, 1)

    def test_per_field_agreement_preserves_evidence_and_ignores_dependency_order(self):
        rows = rows_for([("admit", "admit"), ("exclude", "exclude")])
        rows[0]["dependent_constraint_ids"] = ["x", "y"]
        rows[1]["dependent_constraint_ids"] = ["y", "x"]
        rows[-1]["removed_span"] = "different span"
        before = copy.deepcopy(rows)
        report = self.summarize(list(reversed(rows)), 2)
        self.assertEqual(report["field_agreement"]["dependent_constraint_ids"]["agreement_rate"], 1)
        self.assertEqual(report["field_agreement"]["removed_span"]["agreement_rate"], 0.5)
        self.assertEqual(rows, before)
        self.assertEqual(report, self.summarize(rows, 2))

    def test_cli_preserves_existing_output_and_rejects_invalid_input_before_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reviews, ids, output = [root / name for name in ("reviews.json", "ids.json", "report.json")]
            rows = rows_for([("admit", "exclude")])
            reviews.write_text(json.dumps(rows), encoding="utf-8")
            ids.write_text('["c-0"]', encoding="utf-8")
            command = [sys.executable, "-m", "eval.manipulation_review_agreement",
                       "--reviews", str(reviews), "--expected-candidate-ids", str(ids),
                       "--output", str(output)]
            passed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(passed.returncode, 0, passed.stderr)
            original = output.read_bytes()
            repeated = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertEqual(output.read_bytes(), original)
            invalid_output = root / "invalid.json"
            rows[-1]["decision"] = None
            reviews.write_text(json.dumps(rows), encoding="utf-8")
            failed = subprocess.run(command[:-1] + [str(invalid_output)], cwd=ROOT,
                                    capture_output=True, text=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertFalse(invalid_output.exists())


if __name__ == "__main__":
    unittest.main()
