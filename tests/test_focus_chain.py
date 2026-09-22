"""Behavior contracts for immutable source/criteria → executable collection."""
import json
from collections import Counter
from pathlib import Path
import pytest


def module():
    from scripts import focus_chain
    return focus_chain


def upstream():
    records=[]
    for model in ('gpt-5.6-luna','gpt-5.6-sol'):
        for repeat in range(1,4):
            for arm in ('A','B','C'):
                records.append({'artifact_id':f'{model}-{repeat}-{arm}', 'model':model,
                    'replication':repeat,'variant':arm,'status':'valid',
                    'criteria':['Append a trimmed title.']})
    return {'record':{'variants':{'A':'source A focus','B':'source B focus','C':'source C'}},'artifacts':records}


def test_schedule_preserves_every_upstream_slot_and_omits_uncertainties():
    m=module(); source=upstream()
    source['artifacts'][0].update(status='invalid_output', criteria=None)
    slots=m.make_schedule(source)
    assert len(slots)==54
    assert Counter(s['route'] for s in slots)=={'direct':18,'criteria_only':36}
    assert slots==m.make_schedule(source)
    assert len({s['slot_id'] for s in slots})==54
    assert sum(s['upstream_status']=='invalid_output' for s in slots)==2
    for slot in slots:
        prompt=m.generation_prompt(slot)
        if slot['route']=='criteria_only':
            assert 'source A focus' not in prompt and 'source B focus' not in prompt
            assert 'target_obligation' not in prompt and 'uncertainties' not in prompt
            if slot['upstream_status']=='valid': assert 'Append a trimmed title.' in prompt
        assert slot['slot_id'] not in prompt


@pytest.mark.parametrize('bad',['{}','{"html":""}','{"html":3}','{"html":"x","other":1}',
    '{"html":"x","html":"y"}',json.dumps({'html':'x'*40000}),'{"html":"\\ud800"}'])
def test_code_response_schema_fails_closed(bad):
    with pytest.raises(ValueError): module().parse_code(bad)


def test_code_response_preserves_exact_html_bytes():
    html='<!doctype html><html><input class="new-todo"></html>\n'
    assert module().parse_code(json.dumps({'html':html}))==html


def test_planned_denominators_keep_missing_and_do_not_count_infrastructure_as_defect():
    m=module()
    rows=[]
    for arm,status in [('A','pass'),('A','timeout'),('C','target_only_failure'),('C','not_attempted')]:
        rows.append({'route':'direct','code_model':'m','criteria_model':None,'variant':arm,'category':status,
                     'target_failed': False if status=='pass' else True if status=='target_only_failure' else None})
    report=m.summarize(rows)
    contrast=report['contrasts'][0]
    assert contrast['comparison']=='C-A'
    assert contrast['target_failure_difference_bounds']==[0.0,1.0]
    assert contrast['complete_executable_difference']==1.0
    assert report['groups'][0]['planned']==2


def source_packet(tmp_path, monkeypatch):
    m=module(); packet=tmp_path/'source'; packet.mkdir()
    source=upstream(); schedule=[]; results={'generations':{}}
    for artifact in source['artifacts']:
        slot={k:artifact[k] for k in ('artifact_id','model','replication','variant')}
        slot['intent_id']='todomvc-new-todo'; schedule.append(slot)
        parsed={'criteria':artifact['criteria'],'uncertainties':['Secret ambiguity, never operative']}
        results['generations'][slot['artifact_id']]={'status':'valid','value':parsed}
        m.write(packet/'calls'/('generation-'+slot['artifact_id']+'-response.txt'), json.dumps(parsed).encode())
    record={'id':'todomvc-new-todo',**source['record']}
    m.write(packet/'frozen/corpus.json',{'records':[record]})
    m.write(packet/'frozen/schedule.json',{'generations':schedule})
    m.write(packet/'results.json',results)
    m.write(packet/'receipt.json',{'files':m.inventory(packet)})
    monkeypatch.setattr(m,'UPSTREAM_RECEIPT',m.digest((packet/'receipt.json').read_bytes()))
    return packet


def test_upstream_load_verifies_original_bytes_and_all_eighteen_slots(tmp_path,monkeypatch):
    m=module(); packet=source_packet(tmp_path,monkeypatch)
    result=m.load_upstream(packet)
    assert len(result['artifacts'])==18
    assert all('uncertainties' not in artifact for artifact in result['artifacts'])
    (packet/'results.json').write_text('{}')
    with pytest.raises(ValueError,match='receipt'): m.load_upstream(packet)


def test_upstream_invalid_slot_stays_missing(tmp_path,monkeypatch):
    m=module(); packet=source_packet(tmp_path,monkeypatch)
    results=json.loads((packet/'results.json').read_text())
    first=next(iter(results['generations']))
    results['generations'][first]={'status':'invalid_output'}
    (packet/'results.json').write_text(json.dumps(results))
    (packet/'receipt.json').unlink()
    m.write(packet/'receipt.json',{'files':m.inventory(packet)})
    monkeypatch.setattr(m,'UPSTREAM_RECEIPT',m.digest((packet/'receipt.json').read_bytes()))
    source=m.load_upstream(packet)
    assert sum(s['upstream_status']=='invalid_output' for s in m.make_schedule(source))==2


def proof(tmp_path,monkeypatch):
    m=module()
    from eval.focus_chain_executor import ASSERTION_IDS
    image='sha256:'+'a'*64
    monkeypatch.setattr(m,'inspect_image',lambda _: image)
    cases=[]
    for name,category in m.QUALIFICATION_CASES.items():
        path=tmp_path/name; path.mkdir()
        failures={'mutant-no-focus':['initial_focus'],'mutant-no-clear':['input_cleared'],
                  'control-page-tamper':['initial_focus'], 'mutant-hidden-labels':['enter_append','trimmed_title'],
                  'mutant-no-trim':['trimmed_title','whitespace_rejected']}.get(name,[])
        apphash=m.digest((m.ROOT/'eval/fixtures/focus-chain'/f'{name}.html').read_bytes())
        report={'schema_version':'focus-chain-browser/v1','app_sha256':apphash,'status':'complete',
                'cases':[{'id':i,'status':'failed' if i in failures else 'passed'} for i in ASSERTION_IDS]}
        receipt={'image':image,'app_sha256':apphash,'returncode':int(bool(failures)),
                 'timed_out':False,'category':category}
        if category=='interface_error':
            report['status']='interface_error';receipt['returncode']=2
        m.write(path/'executor.json',receipt); m.write(path/'report.json',report)
        m.write(path/'initial-focus.png',b'\x89PNG\r\n\x1a\nfixture')
        cases.append({'id':name,'expected':category,'observed':category,'evidence_dir':str(path),
                      'receipt_sha256':m.digest((path/'executor.json').read_bytes()),
                      'report_sha256':m.digest((path/'report.json').read_bytes())})
    value={'schema_version':'focus-chain-qualification/v1','qualified':True,'image_id':image,
           'files':{name:m.digest((m.ROOT/name).read_bytes()) for name in m.RUNTIME_FILES},'cases':cases}
    q=tmp_path/'qualification.json';m.write(q,value)
    return q


def test_qualification_is_bound_to_exact_controls_files_and_image(tmp_path,monkeypatch):
    m=module(); q=proof(tmp_path,monkeypatch)
    assert m.verify_qualification(q)['qualified']
    value=json.loads(q.read_text());value['cases'][0]['observed']='target_only_failure';q.write_text(json.dumps(value))
    with pytest.raises(ValueError):m.verify_qualification(q)


def prepared(tmp_path,monkeypatch):
    m=module(); source=source_packet(tmp_path,monkeypatch); q=proof(tmp_path,monkeypatch)
    executable=tmp_path/'cli';executable.write_text('#!/bin/sh\nprintf "test-cli\\n"\n');executable.chmod(0o700)
    dest=tmp_path/'packet'
    m.prepare(source,dest,executable,q)
    return dest


def test_run_collects_before_executing_and_cannot_resume(tmp_path,monkeypatch):
    m=module(); packet=prepared(tmp_path,monkeypatch); calls=[]; executions=[]
    class Provider:
        last_call_metadata={'billing_mode':'chatgpt_subscription'}
        def __init__(self,**kwargs): self.kwargs=kwargs
        def complete(self,request):
            assert not executions
            calls.append(request.prompt)
            assert 'Secret ambiguity' not in request.prompt
            return json.dumps({'html':'<!doctype html><input class="new-todo">'})
    def executor(**kwargs):
        assert len(calls)==54
        executions.append(kwargs)
        return {'category':'pass','target_failed':False,'non_target_failed':[]}
    result=m.run(packet,provider_factory=Provider,executor=executor)
    assert result['planned']==54 and len(executions)==54
    m.verify(packet)
    with pytest.raises(FileExistsError): m.run(packet,provider_factory=Provider,executor=executor)
    assert len(calls)==54


def test_provider_error_stops_new_calls_but_retains_all_planned_slots(tmp_path,monkeypatch):
    m=module(); packet=prepared(tmp_path,monkeypatch); calls=[]
    class Provider:
        last_call_metadata={}
        def __init__(self,**kwargs):pass
        def complete(self,request):
            calls.append(request)
            raise TimeoutError('remote outcome ambiguous')
    def executor(**kwargs):raise AssertionError('no executable artifacts')
    report=m.run(packet,provider_factory=Provider,executor=executor)
    assert len(calls)==1 and report['planned']==54
    state=json.loads((packet/'results.json').read_text())
    assert Counter(r['category'] for r in state['rows'])=={'provider_error':1,'not_attempted':53}


def test_drift_prevents_provider_dispatch(tmp_path,monkeypatch):
    m=module(); packet=prepared(tmp_path,monkeypatch)
    (packet/'frozen/schedule.json').write_text('[]')
    with pytest.raises(ValueError,match='receipt'):m.run(packet)


def test_invalid_generation_does_not_trigger_repair_or_suppress_remaining_slots(tmp_path,monkeypatch):
    m=module(); packet=prepared(tmp_path,monkeypatch); calls=[];executions=[]
    class Provider:
        last_call_metadata={}
        def __init__(self,**kwargs):pass
        def complete(self,request):
            calls.append(request)
            return '{"html":"<html></html>"}' if len(calls)>1 else 'not JSON'
    def executor(**kwargs):
        executions.append(kwargs)
        return {'category':'interface_error'}
    result=m.run(packet,provider_factory=Provider,executor=executor)
    state=json.loads((packet/'results.json').read_text())
    assert len(calls)==54 and len(executions)==53 and result['stop_reason'] is None
    assert Counter(r['category'] for r in state['rows'])=={'invalid_output':1,'interface_error':53}
    assert all(r['target_failed'] is None for r in state['rows'])


def test_private_packet_and_executable_drift_fail_before_dispatch(tmp_path,monkeypatch):
    m=module();packet=prepared(tmp_path,monkeypatch)
    packet.chmod(0o755)
    with pytest.raises(ValueError,match='private'):m.run(packet)
    packet.chmod(0o700)
    (tmp_path/'cli').write_text('changed executable')
    with pytest.raises(ValueError,match='CLI drift'):m.run(packet)


@pytest.mark.parametrize('change',['files','image','report','cases'])
def test_qualification_rejects_drift_and_incomplete_controls(tmp_path,monkeypatch,change):
    m=module();q=proof(tmp_path,monkeypatch);value=json.loads(q.read_text())
    if change=='files':value['files'].pop(next(iter(value['files'])))
    elif change=='image':monkeypatch.setattr(m,'inspect_image',lambda _: 'sha256:'+'b'*64)
    elif change=='report':(Path(value['cases'][0]['evidence_dir'])/'report.json').write_text('{}')
    else:value['cases']=value['cases'][:-1]
    q.write_text(json.dumps(value))
    with pytest.raises(ValueError):m.verify_qualification(q)


@pytest.mark.parametrize('outcome',[{'category':'invented','target_failed':True},
    {'category':'timeout','target_failed':True}, {'category':'pass','target_failed':True,'non_target_failed':[]},
    {'category':'target_only_failure','target_failed':True,'non_target_failed':['input_cleared']},
    {'category':'non_target_only_failure','target_failed':False,'non_target_failed':['unknown']},
    {'category':'pass','target_failed':0,'non_target_failed':[]}])
def test_inconsistent_executor_outcomes_never_become_requirement_failures(outcome):
    result=module().validate_execution_outcome(outcome)
    assert result['category']=='browser_error' and 'target_failed' not in result


def test_validated_executor_preserves_real_failures():
    outcome={'category':'mixed_failure','target_failed':True,'non_target_failed':['input_cleared']}
    assert module().validate_execution_outcome(outcome)==outcome


def test_qualification_wrong_non_target_failure_cannot_qualify(tmp_path,monkeypatch):
    m=module();q=proof(tmp_path,monkeypatch);value=json.loads(q.read_text())
    case=next(c for c in value['cases'] if c['id']=='mutant-no-clear')
    report=Path(case['evidence_dir'])/'report.json'
    content=json.loads(report.read_text())
    for assertion in content['cases']:
        assertion['status']='failed' if assertion['id']=='trimmed_title' else 'passed'
    report.write_text(json.dumps(content));case['report_sha256']=m.digest(report.read_bytes())
    q.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='assertion'):m.verify_qualification(q)


def test_missing_label_control_is_required_as_infrastructure_not_defect():
    m=module()
    assert m.QUALIFICATION_CASES.get('control-interface-missing-label')=='interface_error'
    assert m.QUALIFICATION_FAILURES.get('control-interface-missing-label')==[]
    assert 'eval/fixtures/focus-chain/control-interface-missing-label.html' in m.RUNTIME_FILES
