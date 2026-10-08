import tempfile
import json
import os
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.tau2_subscription import preflight, TurnTransport
from agents.tau2_subscription import PINNED_TAU2
from agents.tau2_subscription import quota_gate
from scripts import tau2_subscription as runner

class RunnerTests(unittest.TestCase):
    def test_public_cli_event_refreshes_claude_routes_without_refreshing_codex(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            quota, capture = root/'quota.json', root/'stdout.jsonl'
            quota.write_text(json.dumps({'sampled_at':time.time()-120, 'routes':{
                'claude-agent':{}, 'claude-user':{}, 'codex':{
                    'status':'allowed','extra_usage':False,'windows':[
                        {'name':'weekly','remaining_percent':90,'reset_at':time.time()+3600}]}}}))
            original_codex=json.loads(quota.read_text())['routes']['codex']
            capture.write_text(json.dumps({'type':'rate_limit_event','rate_limit_info':{
                'status':'allowed_warning','isUsingOverage':False,'unifiedWindows':{
                    'five_hour':{'utilization':0.06,'resetsAt':time.time()+3600},
                    'seven_day':{'utilization':0.01,'resetsAt':time.time()+7200},
                    'seven_day_sonnet':{'utilization':0.2,'resetsAt':time.time()+7200}}}})+'\n')
            runner.refresh_claude_quota(quota, capture, ['claude-agent','claude-user'])
            gate = quota_gate(quota, expected_windows={
                'claude-agent':['five_hour','weekly','seven_day_sonnet'], 'codex':['weekly']})
            gate('claude-agent')
            updated = json.loads(quota.read_text())
            self.assertEqual(updated['routes']['codex'], original_codex)
            with self.assertRaises(RuntimeError): gate('codex')
            self.assertEqual(os.stat(quota).st_mode & 0o777, 0o600)

    def test_turn_transport_updates_quota_before_the_next_turn(self):
        class Provider:
            last_call_metadata={'usage':{'input_tokens':1,'output_tokens':1}}
            def __init__(self, **kw): self.folder=kw['evidence_directory']
            def complete(self, request):
                self.folder.mkdir()
                (self.folder/'stdout.jsonl').write_text(json.dumps({
                    'type':'rate_limit_event','rate_limit_info':{'status':'allowed',
                    'isUsingOverage':False,'unifiedWindows':{'seven_day':{
                    'utilization':0.1,'resetsAt':time.time()+3600}}}})+'\n')
                return 'ok'
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); quota=root/'quota.json'
            quota.write_text(json.dumps({'sampled_at':time.time()-120,'routes':{'sub':{}}}))
            gate=quota_gate(quota,expected_windows={'sub':['weekly']})
            with self.assertRaises(RuntimeError): gate('sub')
            transport=TurnTransport(Provider,executable='unused',model='explicit',out=root,
                                    timeout=1,quota_path=quota,quota_aliases=['sub'])
            self.assertEqual(transport.complete(None),'ok')
            gate('sub')
            self.assertEqual(len(list(root.glob('*/quota-after.json'))),1)

    def test_missing_stale_and_overage_events_do_not_refresh_quota(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); quota, capture=root/'quota.json', root/'stdout.jsonl'
            initial='{"sampled_at":1,"routes":{"sub":{}}}'
            event={'type':'rate_limit_event','rate_limit_info':{'status':'allowed',
                'isUsingOverage':False,'unifiedWindows':{'seven_day':{
                    'utilization':0.1,'resetsAt':time.time()+3600}}}}
            for kind in ('missing','stale','extra','boolean','blocked'):
                quota.write_text(initial)
                current=json.loads(json.dumps(event))
                if kind=='extra': current['rate_limit_info']['isUsingOverage']=True
                if kind=='boolean': current['rate_limit_info']['unifiedWindows']['seven_day']['utilization']=False
                if kind=='blocked': current['rate_limit_info']['status']='rejected'
                capture.write_text('{}\n' if kind=='missing' else json.dumps(current)+'\n')
                if kind=='stale': os.utime(capture,(time.time()-120,time.time()-120))
                with self.assertRaises(RuntimeError):
                    runner.refresh_claude_quota(quota,capture,['sub'])
                self.assertEqual(quota.read_text(),initial)

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
