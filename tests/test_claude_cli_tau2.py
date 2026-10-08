import json
import os
from copy import deepcopy
import pytest
from agents.claude_cli_v2 import validate_stream as validate_text

MODEL='claude-sonnet-5-5'
PAYLOAD={'content':'hello','tool_calls':[]}

def stream():
    return [
        {'type':'system','subtype':'init','model':MODEL,'tools':['StructuredOutput'],'mcp_servers':[]},
        {'type':'assistant','request_id':'request-1','message':{'id':'message-1','model':MODEL,'content':[{'type':'tool_use','id':'output-1','name':'StructuredOutput','input':deepcopy(PAYLOAD)}]}},
        {'type':'user','message':{'role':'user','content':[{'type':'tool_result','tool_use_id':'output-1','content':'Structured output provided successfully'}]}},
        {'type':'result','subtype':'success','is_error':False,'num_turns':2,'result':json.dumps(PAYLOAD),'structured_output':deepcopy(PAYLOAD),'usage':{'input_tokens':2,'output_tokens':78},'modelUsage':{MODEL:{}}},
    ]

def encode(events): return '\n'.join(json.dumps(e) for e in events)

def test_accepts_one_generation_and_its_local_format_validation():
    from agents.claude_cli_tau2 import validate_structured_stream
    answer,usage=validate_structured_stream(encode(stream()),MODEL)
    assert json.loads(answer)==PAYLOAD
    assert usage=={'input_tokens':2,'output_tokens':78}
    with pytest.raises(RuntimeError): validate_text(encode(stream()),MODEL)

@pytest.mark.parametrize('fault',['native_tool','extra_generation','missing_output','mismatched_output','tool_error','wrong_tool_id','wrong_model','extra_tool','wrong_turns','failed_result'])
def test_rejects_actions_repairs_and_unverifiable_structured_results(fault):
    from agents.claude_cli_tau2 import validate_structured_stream
    events=stream()
    call=events[1]['message']['content'][0]
    result=events[-1]
    if fault=='native_tool': call['name']='Bash'
    if fault=='extra_generation': events.insert(2,deepcopy(events[1]))
    if fault=='missing_output': result.pop('structured_output')
    if fault=='mismatched_output': result['structured_output']['content']='changed'
    if fault=='tool_error': events[2]['message']['content'][0]['is_error']=True
    if fault=='wrong_tool_id': events[2]['message']['content'][0]['tool_use_id']='unrelated'
    if fault=='wrong_model': events[1]['message']['model']='claude-opus-5-5'
    if fault=='extra_tool': events[0]['tools'].append('Bash')
    if fault=='wrong_turns': result['num_turns']=3
    if fault=='failed_result': result['subtype']='error_max_structured_output_retries'
    with pytest.raises(RuntimeError): validate_structured_stream(encode(events),MODEL)

@pytest.mark.parametrize('fault',['extra_validation','missing_validation','validation_order','bad_usage','extra_mcp'])
def test_rejects_additional_activity_and_invalid_accounting(fault):
    from agents.claude_cli_tau2 import validate_structured_stream
    events=stream()
    if fault=='extra_validation': events.insert(3,deepcopy(events[2]))
    if fault=='missing_validation': events.pop(2)
    if fault=='validation_order': events[1],events[2]=events[2],events[1]
    if fault=='bad_usage': events[-1]['usage']['output_tokens']=True
    if fault=='extra_mcp': events[0]['mcp_servers']=[{'name':'unexpected'}]
    with pytest.raises(RuntimeError): validate_structured_stream(encode(events),MODEL)

def test_official_cli_contract_permits_only_formatter_and_preserves_one_attempt(tmp_path):
    from agents.claude_cli_tau2 import ClaudeStructuredCLIProvider
    from agents.providers import ProviderRequest
    executable=tmp_path/'fake-claude'
    recorded=tmp_path/'processes.jsonl'
    executable.write_text('#!/usr/bin/env python3\n'+
        'import sys,json,os\nfrom pathlib import Path\n'+
        f'record=Path({str(recorded)!r})\n'+
        "with record.open('a') as f: f.write(json.dumps({'args':sys.argv[1:],'structured_attempts':os.environ.get('MAX_STRUCTURED_OUTPUT_RETRIES'),'transport_retries':os.environ.get('CLAUDE_CODE_MAX_RETRIES')})+'\\n')\n"+
        "if sys.argv[1:]==['auth','status']: print(json.dumps({'loggedIn':True,'authMethod':'claude.ai','apiProvider':'firstParty','subscriptionType':'pro'}))\n"+
        f'else: print({encode(stream())!r})\n')
    executable.chmod(0o700)
    provider=ClaudeStructuredCLIProvider(executable=str(executable),model=MODEL,evidence_directory=tmp_path/'evidence')
    reply=provider.complete(ProviderRequest(prompt='Return structured hello',pair={},variant='tau2',task_family='policy_adequacy'))
    assert json.loads(reply)==PAYLOAD
    processes=[json.loads(line) for line in recorded.read_text().splitlines()]
    assert len(processes)==2
    generation=processes[1]; args=generation['args']
    assert args[args.index('--tools')+1]==''
    assert args[args.index('--allowedTools')+1]=='StructuredOutput'
    assert args[args.index('--max-turns')+1]=='1'
    assert generation['structured_attempts']=='1'
    assert generation['transport_retries']=='0'
    assert '--fallback-model' not in args
    assert json.loads(args[args.index('--json-schema')+1])['required']==['content','tool_calls']
    assert (tmp_path/'evidence/stdout.jsonl').stat().st_mode & 0o777==0o600
    assert provider.last_call_metadata['estimated_cost_usd'] is None

@pytest.mark.parametrize('fault',['init_model','additional_model','result_before_validation','event_after_result'])
def test_rejects_model_drift_and_misordered_terminal_events(fault):
    from agents.claude_cli_tau2 import validate_structured_stream
    events=stream()
    if fault=='init_model': events[0]['model']='claude-opus-5-5'
    if fault=='additional_model': events[-1]['modelUsage']['claude-opus-5-5']={}
    if fault=='result_before_validation': events[2],events[3]=events[3],events[2]
    if fault=='event_after_result': events.append({'type':'rate_limit_event'})
    with pytest.raises(RuntimeError): validate_structured_stream(encode(events),MODEL)


def fake_cli(root, replies, *, failure=None, auth=None):
    executable=root/'claude'; recorded=root/'processes.jsonl'
    executable.write_text('#!/usr/bin/env python3\n'+
        'import sys,json,time\nfrom pathlib import Path\n'+
        f'record=Path({str(recorded)!r})\n'+
        "if sys.argv[1:]==['auth','status']:\n"+
        f" print({json.dumps(auth if auth is not None else {'loggedIn':True,'authMethod':'claude.ai','apiProvider':'firstParty','subscriptionType':'pro'})!r})\n"+
        'else:\n'+
        " count=len(record.read_text().splitlines()) if record.exists() else 0\n"+
        " with record.open('a') as f: f.write(json.dumps({'prompt':sys.stdin.read(),'args':sys.argv[1:]})+'\\n')\n"+
        (" sys.exit(2)\n" if failure=='nonzero' else " time.sleep(10)\n" if failure=='timeout' else '')+
        f' print({replies!r}[count])\n')
    executable.chmod(0o700)
    return executable,recorded

@pytest.mark.parametrize('failure',['nonzero','timeout','invalid_stream'])
def test_failed_process_or_stream_stops_the_bridge_without_a_second_generation(tmp_path,failure):
    from agents.claude_cli_tau2 import ClaudeStructuredCLIProvider
    from agents.tau2_subscription import SubscriptionBridge,STRUCTURED_PROTOCOL
    from scripts.tau2_subscription import TurnTransport
    broken=stream(); broken[1]['message']['content'][0]['name']='Bash'
    executable,recorded=fake_cli(tmp_path,[encode(broken)],failure=failure)
    evidence=tmp_path/'captures';evidence.mkdir()
    transport=TurnTransport(ClaudeStructuredCLIProvider,executable=str(executable),model=MODEL,
        out=evidence,timeout=.2 if failure=='timeout' else 3)
    bridge=SubscriptionBridge({'sub':transport},before_call=lambda _:None,max_calls=2,protocol=STRUCTURED_PROTOCOL)
    with pytest.raises((RuntimeError,TimeoutError)): bridge.complete(model='sub',messages=[])
    with pytest.raises(RuntimeError): bridge.complete(model='sub',messages=[])
    assert len(recorded.read_text().splitlines())==1
    assert bridge.receipts[0]['status']=='failed'
    for folder in evidence.iterdir():
        assert folder.stat().st_mode & 0o777==0o700
        assert {'attempt.json','stdout.jsonl','stderr.log'} <= {p.name for p in folder.iterdir()}
        assert all(p.stat().st_mode & 0o777==0o600 for p in folder.iterdir())


def test_invalid_authentication_shape_fails_before_generation(tmp_path):
    from agents.claude_cli_tau2 import ClaudeStructuredCLIProvider
    from agents.providers import ProviderRequest
    executable,recorded=fake_cli(tmp_path,[],auth=[])
    provider=ClaudeStructuredCLIProvider(executable=str(executable),model=MODEL)
    with pytest.raises(RuntimeError,match='authentication status unavailable'):
        provider.complete(ProviderRequest(prompt='hello',pair={},variant='tau2',task_family='policy_adequacy'))
    assert not recorded.exists()

@pytest.mark.skipif(not os.environ.get('TAU2_CHECKOUT'),reason='pinned tau2 runtime required')
def test_structured_cli_tool_roundtrip_refreshes_quota_and_blocks_reserve(tmp_path):
    import os,sys,time
    from types import SimpleNamespace
    from agents.claude_cli_tau2 import ClaudeStructuredCLIProvider
    from agents.tau2_subscription import SubscriptionBridge,STRUCTURED_PROTOCOL,quota_gate,install
    from scripts.tau2_subscription import TurnTransport,preflight
    from pathlib import Path
    root=Path(os.environ['TAU2_CHECKOUT']);preflight(root);sys.path.insert(0,str(root/'src'))
    from tau2.utils.llm_utils import generate
    from tau2.data_model.message import UserMessage,ToolMessage
    from tau2.domains.airline.environment import get_environment
    environment=get_environment();user_id=next(iter(environment.tools.db.users))
    payloads=[{'content':'','tool_calls':[{'name':'get_user_details','arguments':{'user_id':user_id}}]},
              {'content':'Lookup done.','tool_calls':[]}]
    replies=[]
    for i,payload in enumerate(payloads):
        events=stream(); events[1]['message']['content'][0]['input']=payload
        events[-1]['structured_output']=payload;events[-1]['result']=json.dumps(payload)
        events.insert(-1,{'type':'rate_limit_event','rate_limit_info':{'status':'allowed','isUsingOverage':False,
            'unifiedWindows':{'five_hour':{'utilization':.1,'resetsAt':time.time()+3600},
                             'seven_day':{'utilization':.1 if i==0 else 1,'resetsAt':time.time()+7200}}}})
        replies.append(encode(events))
    executable,recorded=fake_cli(tmp_path,replies)
    quota=tmp_path/'quota.json';quota.write_text(json.dumps({'sampled_at':time.time(),'routes':{'sub':{
        'status':'allowed','extra_usage':False,'windows':[{'name':'five_hour','remaining_percent':90,'reset_at':time.time()+3600},
        {'name':'weekly','remaining_percent':90,'reset_at':time.time()+7200}]}}}))
    evidence=tmp_path/'captures';evidence.mkdir()
    transport=TurnTransport(ClaudeStructuredCLIProvider,executable=str(executable),model=MODEL,
        out=evidence,timeout=3,quota_path=quota,quota_aliases=['sub'])
    bridge=SubscriptionBridge({'sub':transport},before_call=quota_gate(quota,expected_windows={'sub':['five_hour','weekly']}),
        max_calls=3,protocol=STRUCTURED_PROTOCOL)
    schema={'type':'function','function':{'name':'get_user_details','parameters':{'type':'object'}}}
    history=[UserMessage(role='user',content='Look up my profile.')]
    with install(bridge):
        reply=generate(model='sub',messages=history,tools=[SimpleNamespace(openai_schema=schema)],num_retries=0)
        assert reply.tool_calls[0].arguments=={'user_id':user_id}
        details=environment.tools.get_user_details(**reply.tool_calls[0].arguments)
        history.extend([reply,ToolMessage(role='tool',id=reply.tool_calls[0].id,content=details.model_dump_json())])
        final=generate(model='sub',messages=history,num_retries=0)
        assert final.content=='Lookup done.'
        with pytest.raises(RuntimeError,match='quota'): generate(model='sub',messages=history,num_retries=0)
    generations=[json.loads(line) for line in recorded.read_text().splitlines()]
    assert len(generations)==2
    assert 'tool' in generations[1]['prompt'] and reply.tool_calls[0].id in generations[1]['prompt']
    assert all(r['status']=='completed' and r['protocol']==STRUCTURED_PROTOCOL for r in bridge.receipts)
    assert reply.cost is None and final.cost is None
    assert len(list(evidence.glob('*/quota-after.json')))==2


def test_one_generation_can_arrive_as_multiple_blocks_with_matching_ids():
    from agents.claude_cli_tau2 import validate_structured_stream
    events=stream()
    thinking=deepcopy(events[1]);thinking['message']['content']=[{'type':'thinking','thinking':'private'}]
    text=deepcopy(events[1]);text['message']['content']=[{'type':'text','text':'Formatting reply.'}]
    events[1:1]=[thinking,text]
    answer,_=validate_structured_stream(encode(events),MODEL)
    assert json.loads(answer)==PAYLOAD

@pytest.mark.parametrize('identity',['message','request','missing_message','missing_request'])
def test_blocks_from_distinct_or_unverifiable_generations_are_rejected(identity):
    from agents.claude_cli_tau2 import validate_structured_stream
    events=stream(); extra=deepcopy(events[1])
    extra['message']['content']=[{'type':'text','text':'Another generation'}]
    if identity=='message': extra['message']['id']='message-2'
    if identity=='request': extra['request_id']='request-2'
    if identity=='missing_message': extra['message'].pop('id')
    if identity=='missing_request': extra.pop('request_id')
    events.insert(1,extra)
    with pytest.raises(RuntimeError): validate_structured_stream(encode(events),MODEL)

def test_repeated_identical_block_after_validation_cannot_bypass_ordering():
    from agents.claude_cli_tau2 import validate_structured_stream
    events=stream()
    thinking=deepcopy(events[1]);thinking['message']['content']=[{'type':'thinking','thinking':'private'}]
    events.insert(1,thinking)
    events.insert(-1,deepcopy(thinking))
    with pytest.raises(RuntimeError): validate_structured_stream(encode(events),MODEL)
