import json
import pytest
from agents.claude_cli_v2 import validate_stream
MODEL='claude-sonnet-4-6'


def events():
 return [{'type':'system','subtype':'init','model':MODEL,'tools':[],'mcp_servers':[]},
 {'type':'system','subtype':'thinking_tokens','estimated_tokens':50,'estimated_tokens_delta':50},
 {'type':'assistant','message':{'model':MODEL,'content':[{'type':'text','text':'answer'}]}},
 {'type':'result','subtype':'success','is_error':False,'num_turns':1,'result':'answer','usage':{'input_tokens':1,'output_tokens':1},'modelUsage':{MODEL:{}}}]


def test_text_completion_accepts_bounded_non_action_thinking_telemetry():
 raw='\n'.join(map(json.dumps,events()))
 assert validate_stream(raw,MODEL)[0]=='answer'


@pytest.mark.parametrize('mutation', ['negative','boolean','missing','unknown','tool_payload','non_monotonic','bad_delta'])
def test_telemetry_validation_does_not_allow_actions_or_invalid_counts(mutation):
 es=events();e=es[1]
 if mutation=='negative':e['estimated_tokens']=-1
 if mutation=='boolean':e['estimated_tokens']=True
 if mutation=='missing':del e['estimated_tokens_delta']
 if mutation=='unknown':e['subtype']='task_started'
 if mutation=='tool_payload':e['tool_use']={'name':'Read'}
 if mutation=='non_monotonic':es.insert(2,{**e,'estimated_tokens':20,'estimated_tokens_delta':0})
 if mutation=='bad_delta':e['estimated_tokens_delta']=99
 with pytest.raises(RuntimeError):validate_stream('\n'.join(map(json.dumps,es)),MODEL)


def test_versioned_adapter_accepts_telemetry_through_a_tool_free_cli_process(tmp_path):
 from test_claude_cli import cli,req
 from agents.claude_cli_v2 import ClaudeCLIProvider
 provider=ClaudeCLIProvider(executable=cli(tmp_path,telemetry=True),model=MODEL,evidence_directory=tmp_path/'capture')
 assert provider.complete(req())=='answer'
 assert provider.last_call_metadata['response_model']==MODEL
 assert (tmp_path/'capture/metadata.json').exists()
