import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.tau2_subscription import preflight, TurnTransport
from agents.tau2_subscription import PINNED_TAU2

class RunnerTests(unittest.TestCase):
    def test_preflight_rejects_checkout_drift_before_importing_tau2(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"src/tau2").mkdir(parents=True)
            with patch("scripts.tau2_subscription.subprocess.check_output",
                       side_effect=["different",""]):
                with self.assertRaises(ValueError): preflight(root)
            with patch("scripts.tau2_subscription.subprocess.check_output",
                       side_effect=[PINNED_TAU2," M src/tau2/utils/llm_utils.py"]):
                with self.assertRaises(ValueError): preflight(root)

    def test_preflight_accepts_pinned_clean_checkout(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/"src/tau2").mkdir(parents=True)
            with patch("scripts.tau2_subscription.subprocess.check_output",
                       side_effect=[PINNED_TAU2,""]):
                preflight(root)

    def test_two_turns_have_distinct_private_evidence_directories(self):
        class Provider:
            last_call_metadata={"usage":{"input_tokens":1,"output_tokens":1}}
            def __init__(self,**kw):
                self.folder=kw["evidence_directory"]
            def complete(self,request):
                self.folder.mkdir(exist_ok=False)
                return "ok"
        with tempfile.TemporaryDirectory() as d:
            transport=TurnTransport(Provider,executable="unused",model="explicit",out=d,timeout=1)
            self.assertEqual(transport.complete(None),"ok")
            self.assertEqual(transport.complete(None),"ok")
            self.assertEqual(len(list(Path(d).iterdir())),2)

if __name__ == "__main__": unittest.main()
