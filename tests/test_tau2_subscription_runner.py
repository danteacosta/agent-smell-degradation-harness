import tempfile
import json
import os
import time
import unittest
import pytest
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

def test_preflight_records_the_selected_structured_protocol(tmp_path, capsys):
    root=tmp_path/'tau2'; root.mkdir()
    data=tmp_path/'data'; (data/'tau2/domains/airline').mkdir(parents=True)
    (data/'tau2/domains/airline/policy.md').write_text('policy')
    with patch.object(runner,'preflight'):
        runner.main(['--tau2',str(root),'--data',str(data),'--claude-structured-output'])
    assert json.loads(capsys.readouterr().out)['protocol']=='tau2-subscription-json/v3-claude-structured'

def test_latest_blocked_quota_event_cannot_reuse_earlier_allowed_event(tmp_path):
    quota=tmp_path/'quota.json';capture=tmp_path/'stdout.jsonl'
    original='{"sampled_at":1,"routes":{"sub":{}}}';quota.write_text(original)
    allowed={'type':'rate_limit_event','rate_limit_info':{'status':'allowed','isUsingOverage':False,
        'unifiedWindows':{'seven_day':{'utilization':.1,'resetsAt':time.time()+3600}}}}
    blocked=json.loads(json.dumps(allowed));blocked['rate_limit_info']['status']='rejected'
    capture.write_text(json.dumps(allowed)+'\n'+json.dumps(blocked)+'\n')
    with pytest.raises(RuntimeError): runner.refresh_claude_quota(quota,capture,['sub'])
    assert quota.read_text()==original


def test_stale_or_future_route_cannot_borrow_fresh_global_timestamp(tmp_path):
    import pytest
    quota=tmp_path/'quota.json';now=time.time()
    for sampled in (now-120,now+120):
        quota.write_text(json.dumps({'sampled_at':now,'routes':{'sub':{'sampled_at':sampled,
            'status':'allowed','extra_usage':False,'windows':[{'name':'weekly','remaining_percent':90,'reset_at':now+3600}]}}}))
        with pytest.raises(RuntimeError): quota_gate(quota,expected_windows={'sub':['weekly']})('sub')

@pytest.mark.skipif(not os.environ.get('TAU2_CHECKOUT'),reason='pinned tau2 runtime required')
@pytest.mark.parametrize('structured',[False,True])
def test_runner_opt_in_selects_claude_transport_and_preserves_codex(tmp_path,monkeypatch,structured):
    import sys
    from contextlib import contextmanager
    from types import SimpleNamespace
    from agents.claude_cli_v2 import ClaudeCLIProvider
    from agents.claude_cli_tau2 import ClaudeStructuredCLIProvider
    from agents.codex_cli import CodexCLIProvider
    from agents.tau2_subscription import PROTOCOL,STRUCTURED_PROTOCOL
    root=Path(os.environ['TAU2_CHECKOUT']);sys.path.insert(0,str(root/'src'))
    from tau2 import run as native
    data=tmp_path/'data';(data/'tau2/domains/airline').mkdir(parents=True)
    (data/'tau2/domains/airline/policy.md').write_text('policy')
    out=tmp_path/'out';captured=[]
    @contextmanager
    def capture_install(bridge): captured.append(bridge);yield
    monkeypatch.setattr(runner,'install',capture_install)
    monkeypatch.setattr(native,'get_tasks',lambda *a,**kw:[object()])
    monkeypatch.setattr(native,'run_single_task',lambda *a,**kw:SimpleNamespace(model_dump=lambda **kw:{'fixture':True}))
    args=['--tau2',str(root),'--data',str(data),'--execute','--task-id','0',
        '--agent-provider','claude','--agent-model','claude-sonnet-5-5','--user-provider','codex',
        '--user-model','gpt-6-astra','--claude-executable','unused','--codex-executable','unused',
        '--quota',str(tmp_path/'quota.json'),'--out',str(out),'--max-calls','4',
        '--agent-windows','five_hour,weekly','--user-windows','weekly']
    if structured: args.append('--claude-structured-output')
    runner.main(args)
    assert captured[0].routes['subscription-agent'].provider_class is (ClaudeStructuredCLIProvider if structured else ClaudeCLIProvider)
    assert captured[0].routes['subscription-user'].provider_class is CodexCLIProvider
    started=json.loads((out/'started.json').read_text())
    assert started['protocol']==(STRUCTURED_PROTOCOL if structured else PROTOCOL)
    assert started['claude_structured_output'] is structured
    assert out.stat().st_mode & 0o777==0o700
    assert all(p.stat().st_mode & 0o777==0o600 for p in out.iterdir())
