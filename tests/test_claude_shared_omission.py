import json
import pytest
from scripts.claude_shared_omission import quota_snapshot, require_capacity, interleaved_schedule


def stream(five=.17, week=.03):
 return json.dumps({'type':'rate_limit_event','rate_limit_info':{'status':'allowed','isUsingOverage':False,'unifiedWindows':{'five_hour':{'utilization':five,'resetsAt':9999999999},'seven_day':{'utilization':week,'resetsAt':9999999999}}}})


def test_quota_allows_below_threshold_and_stops_at_thirty_remaining():
 assert require_capacity(quota_snapshot(stream()), now=1)['seven_day']['remaining_percent']==97
 for five,week in ((.7,.03),(.17,.7),(.8,.9)):
  with pytest.raises(RuntimeError):require_capacity(quota_snapshot(stream(five,week)),now=1)


@pytest.mark.parametrize('raw',['', stream(-.1,.03),stream(.17,1.1),stream().replace('false','true'),stream().replace('allowed','rejected')])
def test_unknown_invalid_or_overage_quota_fails_closed(raw):
 with pytest.raises(RuntimeError):require_capacity(quota_snapshot(raw),now=1)


def test_expired_window_cannot_authorize_generation():
 with pytest.raises(RuntimeError):require_capacity(quota_snapshot(stream()),now=9999999999)


def test_schedule_interleaves_models_without_repeating_slots():
 schedule=interleaved_schedule({'sonnet':[{'call_id':'a'},{'call_id':'b'}],'opus':[{'call_id':'a'},{'call_id':'b'}]})
 assert schedule==[('sonnet','a'),('opus','a'),('sonnet','b'),('opus','b')]


def test_frozen_replication_stops_before_second_slot_at_reserve(tmp_path):
 from pathlib import Path
 import sys
 from scripts import claude_shared_omission as study
 from scripts import shared_omission_e2e as so
 from scripts import mutation_adequacy as ma
 root=tmp_path/'run'
 ma.ta.put(root/'controls/controls.json',{'qualified':True,'expected':{'broken_save':'assertion_alarm','keeps_rule':'quiet','lost_rule':'assertion_alarm'},'observed':{'broken_save':'assertion_alarm','keeps_rule':'quiet','lost_rule':'assertion_alarm'},'runner_sha256':ma.ta.sha256_file(ma.ta.RUNNER)})
 parent=tmp_path/'original'
 page=tmp_path/'page.html';page.write_text('<p>public fixture</p>')
 manifest={'schema_version':so.SCHEMA,'model':'gpt-6-astra','code_context_role':'confirmed_mutant','selected_mutants':{'case':'slot'},'cases':[{'case':'case','roles':{'mutant':['slot']},'artifacts':{'slot':{'artifact_path':str(page),'artifact_sha256':ma.ta.sha256_file(page)}}}],
 'script_sha256':ma.ta.sha256_file(Path(ma.__file__)),'test_anchor_script_sha256':ma.ta.sha256_file(Path(ma.ta.__file__)),'extension_script_sha256':ma.ta.sha256_file(Path(so.__file__)),'image':ma.ta.IMAGE,'runner_sha256':ma.ta.sha256_file(ma.ta.RUNNER),'schedule':[{'call_id':'one','case':'case'}]}
 ma.ta.put(parent/'frozen/manifest.json',manifest)
 ma.ta.put(parent/'frozen/controls.json',json.loads((root/'controls/controls.json').read_text()))
 ma.ta.put(parent/'frozen/prompts/one.txt','public prompt')
 ma.ta.put(parent/'frozen/receipt.json',{'files':ma.ta.inventory(parent/'frozen')})
 before=ma.ta.inventory(parent)
 executable=tmp_path/'fake';executable.write_text(f'''#!{sys.executable}
import json,sys
if sys.argv[1:]==['auth','status']:
 print(json.dumps({{'loggedIn':True,'authMethod':'claude.ai','apiProvider':'firstParty','subscriptionType':'pro'}}));sys.exit(0)
assert sys.stdin.read()=='public prompt'
model=sys.argv[sys.argv.index('--model')+1]
for event in [{{'type':'system','subtype':'init','model':model,'tools':[],'mcp_servers':[]}},{{'type':'assistant','message':{{'model':model,'content':[{{'type':'text','text':'not a suite'}}]}}}},{{'type':'rate_limit_event','rate_limit_info':{{'status':'allowed','isUsingOverage':False,'unifiedWindows':{{'five_hour':{{'utilization':.7,'resetsAt':9999999999}},'seven_day':{{'utilization':.1,'resetsAt':9999999999}}}}}}}},{{'type':'result','subtype':'success','is_error':False,'num_turns':1,'result':'not a suite','usage':{{'input_tokens':1,'output_tokens':1}},'modelUsage':{{model:{{}}}}}}]:print(json.dumps(event))
''');executable.chmod(0o700)
 baseline=tmp_path/'quota';baseline.write_text(stream())
 out=root/'study'
 study.prepare(out,parent,baseline,executable)
 with pytest.raises(RuntimeError,match='reserve'):study.generate(out)
 stop=json.loads((out/'stopped.json').read_text())
 assert stop['attempted']==1 and stop['planned']==2
 assert len(list(out.glob('*/calls/*/attempt.json')))==1
 assert not (out/'generation-completed.json').exists()
 assert ma.ta.inventory(parent)==before
 with pytest.raises(FileExistsError):study.generate(out)


def test_model_specific_quota_window_also_stops_collection():
 data=json.loads(stream())
 data['rate_limit_info']['unifiedWindows']['seven_day_opus']={'utilization':.9,'resetsAt':9999999999}
 with pytest.raises(RuntimeError,match='reserve'):
  require_capacity(quota_snapshot(json.dumps(data)),now=1)
