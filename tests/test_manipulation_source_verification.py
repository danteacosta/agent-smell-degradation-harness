"""Offline source verification must fail closed without manufacturing review evidence."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from eval.manipulation_admission import REQUIRED
from eval.manipulation_review_handoff import prepare_assignment

ROOT = Path(__file__).resolve().parents[1]


class SourceVerificationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        texts = {"source.txt": "Preface\nSave café and retain audit logs.\nEnd",
                 "LICENSE": "Synthetic test license", "NOTICE": "Synthetic attribution"}
        for name, text in texts.items():
            (self.root / name).write_text(text, encoding="utf-8")
        clean = "Save café and retain audit logs."
        removed = " and retain audit logs"
        start = clean.index(removed)
        source = {"path": "source.txt", "license_path": "LICENSE", "notice_path": "NOTICE",
                  "start_char": len("Preface\n"), "end_char": len("Preface\n") + len(clean)}
        for key, hash_key in (("path", "sha256"), ("license_path", "license_sha256"),
                              ("notice_path", "notice_sha256")):
            source[hash_key] = hashlib.sha256((self.root / source[key]).read_bytes()).hexdigest()
        self.candidates = {"selection_frozen": False, "human_approvals": 0, "records": [{
            "intent_id": "synthetic-1", "project_id": "synthetic", "source": source,
            "variants": {"clean": clean, "defective": clean.replace(removed, "")},
            "manipulation": {"start": start, "end": start + len(removed), "text": removed},
            "target": {"constraint_id": "synthetic-1-c01"}}]}
        row = {key: "synthetic-1" if key == "candidate_id" else None for key in REQUIRED}
        self.template = {"schema_version": "manipulation-review-authoring-template/v1",
                         "status": "unfilled_not_admission_evidence", "confirmatory_eligible": False,
                         "expected_candidate_ids": ["synthetic-1"], "review_slots": [
                             {"slot": slot, "reviews": [copy.deepcopy(row)]}
                             for slot in ("reviewer_A", "reviewer_B")]}
        self.rebind()

    def rebind(self):
        raw = json.dumps(self.candidates, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
        self.template["candidate_content_sha256"] = hashlib.sha256(raw).hexdigest()

    def export(self, **kwargs):
        return prepare_assignment(self.template, self.candidates, "reviewer_A",
                                  include_materials=True, source_root=self.root, **kwargs)

    def test_verified_bytes_keep_all_human_judgments_blank(self):
        before = copy.deepcopy((self.template, self.candidates))
        packet = self.export()
        self.assertTrue(packet["source_files_reverified"])
        self.assertIn("not upstream authenticity", packet["source_verification_scope"])
        self.assertFalse(packet["confirmatory_eligible"])
        self.assertTrue(packet["materials_are_proposals_not_labels"])
        self.assertTrue(all(v is None for k, v in packet["reviews"][0].items()
                            if k != "candidate_id"))
        self.assertEqual(before, (self.template, self.candidates))

    def test_each_source_license_and_notice_byte_change_is_rejected(self):
        for name in ("source.txt", "LICENSE", "NOTICE"):
            with self.subTest(name=name):
                path = self.root / name
                original = path.read_bytes()
                path.write_bytes(original + b"drift")
                with self.assertRaises(ValueError):
                    self.export()
                path.write_bytes(original)

    def test_notice_metadata_must_be_paired(self):
        for key in ("notice_path", "notice_sha256"):
            with self.subTest(key=key):
                value = self.candidates["records"][0]["source"].pop(key)
                self.rebind()
                with self.assertRaisesRegex(ValueError, "supplied together"):
                    self.export()
                self.candidates["records"][0]["source"][key] = value

    def test_notice_is_optional_when_not_declared(self):
        source = self.candidates["records"][0]["source"]
        source.pop("notice_path")
        source.pop("notice_sha256")
        self.rebind()
        self.assertTrue(self.export()["source_files_reverified"])

    def test_source_and_notice_paths_cannot_escape_even_through_symlinks(self):
        with tempfile.TemporaryDirectory() as outside:
            external = Path(outside) / "outside.txt"
            external.write_text("outside", encoding="utf-8")
            (self.root / "linked").symlink_to(external)
            source = self.candidates["records"][0]["source"]
            for key in ("path", "license_path", "notice_path"):
                original = source[key]
                for value in (str(external), "linked"):
                    with self.subTest(key=key, value=value):
                        source[key] = value
                        self.rebind()
                        with self.assertRaises(ValueError):
                            self.export()
                source[key] = original

    def test_excerpt_deletion_identity_and_false_approvals_are_checked(self):
        original = copy.deepcopy(self.candidates)
        mutations = [lambda c: c["records"][0]["source"].update(end_char=9999),
                     lambda c: c["records"][0]["variants"].update(clean="invented excerpt"),
                     lambda c: c["records"][0]["variants"].update(defective="invented remainder"),
                     lambda c: c["records"][0]["target"].update(constraint_id="another-id"),
                     lambda c: c.update(human_approvals=1),
                     lambda c: c.update(selection_frozen=True)]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                self.candidates = copy.deepcopy(original)
                mutate(self.candidates)
                self.rebind()
                with self.assertRaises(ValueError):
                    self.export()

    def test_verification_requires_material_export(self):
        with self.assertRaisesRegex(ValueError, "requires include_materials"):
            prepare_assignment(self.template, self.candidates, "reviewer_A", source_root=self.root)

    def test_cli_verifies_before_creating_output(self):
        template, candidates, output = [self.root / name for name in
                                        ("template.json", "candidates.json", "assignment.json")]
        template.write_text(json.dumps(self.template), encoding="utf-8")
        candidates.write_text(json.dumps(self.candidates), encoding="utf-8")
        command = [sys.executable, "-m", "eval.manipulation_review_handoff",
                   "--template", str(template), "--candidates", str(candidates),
                   "--slot", "reviewer_A", "--include-materials", "--source-root", str(self.root),
                   "--output", str(output)]
        (self.root / "NOTICE").write_text("changed", encoding="utf-8")
        failed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(failed.returncode, 0)
        self.assertFalse(output.exists())
        (self.root / "NOTICE").write_text("Synthetic attribution", encoding="utf-8")
        passed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(passed.returncode, 0, passed.stderr)
        self.assertTrue(json.loads(output.read_text())["source_files_reverified"])


if __name__ == "__main__":
    unittest.main()
