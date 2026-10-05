"""Exercise the real wrapper without making provider calls."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ConfirmatoryScreeningWrapperTest(unittest.TestCase):
    def run_wrapper(self, reserve_result):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            wrapper = root / "scripts/run_confirmatory_screening.sh"
            shutil.copyfile(ROOT / "scripts/run_confirmatory_screening.sh", wrapper)
            fake_python = root / "python"
            fake_python.write_text(
                f"#!{sys.executable}\n"
                "import json, os, pathlib, sys\n"
                "if len(sys.argv) < 2 or sys.argv[1] != 'scripts/llm_screening_panel.py':\n"
                "    os.execv(os.environ['REAL_PYTHON'], [os.environ['REAL_PYTHON'], *sys.argv[1:]])\n"
                "mode = sys.argv[2]\n"
                "out = pathlib.Path(sys.argv[sys.argv.index('--out') + 1])\n"
                "option = 'reserve' if 'reserve' in out.name else 'w2024'\n"
                "with open(os.environ['CALL_LOG'], 'a') as log:\n"
                "    log.write(json.dumps([mode, option]) + '\\n')\n"
                "if mode == 'prepare':\n"
                "    out.mkdir(parents=True)\n"
                "else:\n"
                "    result = json.loads(os.environ['RESERVE_RESULT']) if option == 'reserve' else {'status': 'complete'}\n"
                "    (out / 'results.json').write_text(json.dumps(result))\n"
                "    print(json.dumps(result))\n"
            )
            fake_python.chmod(0o755)
            log = root / "calls.jsonl"
            evidence = root / "evidence"
            env = dict(
                os.environ,
                PYTHON=str(fake_python),
                REAL_PYTHON=sys.executable,
                CALL_LOG=str(log),
                RESERVE_RESULT=json.dumps(reserve_result),
                EVIDENCE_ROOT=str(evidence),
            )
            process = subprocess.run(
                ["bash", str(wrapper), "both"], env=env,
                capture_output=True, text=True, timeout=20,
            )
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            results = [json.loads(path.read_text()) for path in evidence.glob("*/results.json")]
            return process, calls, results

    def assert_stops_after_reserve(self, reserve_result):
        process, calls, results = self.run_wrapper(reserve_result)
        self.assertNotEqual(process.returncode, 0, process.stdout)
        self.assertEqual(calls, [["prepare", "reserve"], ["run", "reserve"]])
        self.assertEqual(results, [reserve_result])

    def test_failed_controls_stop_before_second_option(self):
        self.assert_stops_after_reserve({"status": "stopped_controls_failed"})

    def test_unknown_status_stops_before_second_option(self):
        self.assert_stops_after_reserve({"status": "unexpected"})

    def test_missing_status_stops_before_second_option(self):
        self.assert_stops_after_reserve({})

    def test_complete_results_allow_both_options(self):
        process, calls, results = self.run_wrapper({"status": "complete"})
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(calls, [
            ["prepare", "reserve"], ["run", "reserve"],
            ["prepare", "w2024"], ["run", "w2024"],
        ])
        self.assertEqual(results, [{"status": "complete"}, {"status": "complete"}])


if __name__ == "__main__":
    unittest.main()
