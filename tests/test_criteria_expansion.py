import copy
import json
from pathlib import Path
import pytest
from scripts import criteria_expansion as m


def corpus():
    records = []
    for p in range(4):
        for i in range(3):
            a = f'Project {p} case {i}: display title. Display version. Display links.'
            text = ' Display links.'
            records.append({'id': f'p{p}i{i}', 'project_id': f'p{p}',
                'source': {'url':'https://example.org/file', 'revision':'a'*40, 'license':'MIT', 'license_url':'https://example.org/LICENSE', 'path':'source.txt','sha256':'a'*64,'locator':f'case{i}'},
                'variants': {'A':a, 'B':a.replace('display title','show title'), 'C':a[:-len(text)]},
                'obligations':[{'id':k,'text':v} for k,v in [('title','Display title'),('version','Display version'),('links','Display links')]],
                'target_obligation_id':'links','omission':{'start':len(a)-len(text),'end':len(a),'text':text}})
    return records


def test_balanced_schedule_and_private_prompts():
    records = m.validate_corpus(corpus())
    schedule = m.make_schedule(records)
    assert len(schedule['generations']) == 216
    assert len(schedule['judgments']) == 648
    assert schedule == m.make_schedule(records)
    for slot in schedule['generations']:
        record = next(r for r in records if r['id'] == slot['intent_id'])
        prompt = m.generation_prompt(record['variants'][slot['variant']])
        assert 'target_obligation_id' not in prompt
        if slot['variant'] == 'C': assert 'Display links' not in prompt
    prompt = m.judge_prompt(records[0], {'criteria':['Display title'], 'uncertainties':[]})
    assert 'target_obligation_id' not in prompt
    assert 'project_id' not in prompt


@pytest.mark.parametrize('fault', ['duplicate','deletion','target','projects'])
def test_rejects_invalid_corpus(fault):
    records = corpus()
    if fault == 'duplicate': records[1]['id'] = records[0]['id']
    if fault == 'deletion': records[0]['variants']['C'] += ' changed'
    if fault == 'target': records[0]['target_obligation_id'] = 'missing'
    if fault == 'projects': records[0]['project_id'] = 'extra'
    with pytest.raises(ValueError): m.validate_corpus(records)


def vote(label='supported', evidence='Display links'):
    return {'obligations':{'links':{'label':label,'evidence':evidence,'reason':'Explanation'}},'additions':[]}


def test_literal_evidence_only_from_criteria():
    artifact={'criteria':['Display links'], 'uncertainties':['Display title']}
    assert m.parse_judgment(json.dumps(vote()), artifact, ['links'])
    with pytest.raises(ValueError): m.parse_judgment(json.dumps(vote(evidence='Display title')), artifact,['links'])
    with pytest.raises(ValueError): m.parse_judgment(json.dumps(vote('absent')),artifact,['links'])


def test_unknown_bounds_and_project_pairing():
    rows=[]
    for project in ['p1','p2','p3','p4']:
        for arm,label in [('A','supported'),('B','supported'),('C','absent')]:
            for repeat in range(1,4):
                rows.append({'project_id':project,'intent_id':project,'model':'model','replication':repeat,'variant':arm,'primary':label})
    report=m.paired_effects(rows)
    assert report['C-A']['secondary_pooled']['complete_cell_mean'] == -1
    assert report['C-A']['secondary_pooled']['conditional_project_resampling_spread'] == [-1,-1]
    rows[6]['primary']='unclear'
    report=m.paired_effects(rows)
    assert report['C-A']['secondary_pooled']['complete_cells']==3
    assert report['C-A']['secondary_pooled']['bounds']==pytest.approx([-1,-11/12])


def test_overlap_exclusion_is_generator_specific_and_fail_closed():
    luna = {'model':'gpt-5.6-luna', 'primary':None,
            'votes':['supported','supported','absent']}
    assert m.overlap_excluded_label(luna) is None
    luna['primary'] = 'supported'
    assert m.overlap_excluded_label(luna) == 'supported'

    sol = {'model':'gpt-5.6-sol', 'primary':None,
           'votes':['supported','absent','supported']}
    assert m.overlap_excluded_label(sol) == 'supported'
    sol['votes'][2] = 'absent'
    assert m.overlap_excluded_label(sol) is None
    sol['votes'][2] = None
    assert m.overlap_excluded_label(sol) is None


def test_target_identity_does_not_change_judge_prompt():
    record=corpus()[0]; artifact={'criteria':['Display title'],'uncertainties':[]}
    before=m.judge_prompt(record,artifact)
    record['target_obligation_id']='title'
    assert m.judge_prompt(record,artifact)==before


def freeze_packet(tmp_path):
    root=tmp_path/'sources'; root.mkdir()
    records=corpus(); content='\n'.join(r['variants']['A'] for r in records)
    (root/'source.txt').write_text(content); (root/'LICENSE').write_text('MIT')
    for r in records:
        r['source'].update(sha256=m.digest(content.encode()),license_path='LICENSE')
    (root/'corpus.json').write_text(json.dumps({'records':records}))
    executable=tmp_path/'cli'; executable.write_text('#!/bin/sh\necho fake-cli\n'); executable.chmod(0o700)
    packet=tmp_path/'packet'; m.prepare(root/'corpus.json',packet,executable)
    return packet


class FakeProvider:
    mode='valid'
    def __init__(self,**kwargs): self.last_call_metadata={}; self.kwargs=kwargs
    def complete(self,request):
        self.kwargs['evidence_directory'].mkdir(mode=0o700,exist_ok=False)
        prompt=request.prompt
        if 'calibration batch' in prompt:
            if self.mode=='bad_calibration': return '{}'
            cases,_=m.calibration()
            return json.dumps({c['id']:{'obligations':{k:{'label':label,'evidence':None if label=='absent' else c['artifact']['criteria'][0],'reason':'Fixture'} for k,label in c['expected'].items()},'additions':['PDF'] if c['id']=='fixture-08' else []} for c in cases})
        if prompt.startswith('Produce'):
            if self.mode=='provider_error': raise RuntimeError('infrastructure')
            if self.mode=='invalid_generation': return '{}'
            return json.dumps({'criteria':['Display title. Display version. Display links.'],'uncertainties':[]})
        artifact=json.loads(prompt.split('Artifact JSON:\n')[1])
        obligations=json.loads(prompt.split('Obligations JSON:\n')[1].split('\nArtifact JSON:')[0])
        return json.dumps({'obligations':{o['id']:{'label':'supported','evidence':artifact['criteria'][0],'reason':'Literal'} for o in obligations},'additions':[]})


@pytest.mark.parametrize('mode,calls,generations', [('bad_calibration',3,0),('valid',867,216),('invalid_generation',219,216)])
def test_observable_call_budget_and_immutable_rerun(tmp_path,mode,calls,generations):
    packet=freeze_packet(tmp_path)
    class Provider(FakeProvider): pass
    Provider.mode=mode
    result=m.run(packet,Provider)
    assert result['calls_attempted']==calls
    assert sum(v for k,v in result['generations'].items() if k!='not_attempted')==generations
    m.verify(packet)
    with pytest.raises(FileExistsError): m.run(packet,Provider)


def test_provider_failure_stops_dispatch_and_drains(tmp_path):
    packet=freeze_packet(tmp_path)
    class Provider(FakeProvider): mode='provider_error'
    result=m.run(packet,Provider)
    assert 4<=result['calls_attempted']<=7
    assert result['stop_reason']=='provider_infrastructure_error'
    assert result['judgments']=={'not_attempted':648}
    m.verify(packet)


def test_calibration_signed_conditional_composite_reference():
    cases,prompt=m.calibration()
    assert len(cases)==8
    assert cases[0]['expected']['o3']=='supported'  # Negative obligation is supported.
    assert 'Expose passwords.' in cases[2]['artifact']['criteria'][0]
    assert cases[2]['expected']['o3']=='absent'  # Opposite policy is not support.
    assert cases[7]['expected']['o2']=='unclear'  # Missing prefix is partial coverage.
    assert 'prefixed with v' not in cases[7]['artifact']['criteria'][0]
    assert 'expected' not in prompt


def test_complete_cell_sensitivity_never_pairs_repeat_indices():
    rows=[]
    for arm,labels in [('A',['supported','absent','supported']),('B',['supported']*3),('C',['absent','supported','absent'])]:
        for rep,label in enumerate(labels,1):
            rows.append({'project_id':'p','intent_id':'i','model':'m','replication':rep,'variant':arm,'primary':label})
    first=m.paired_effects(rows)
    for row in rows:
        if row['variant']=='C': row['replication']=4-row['replication']
    assert m.paired_effects(rows)==first
    assert first['C-A']['secondary_pooled']['complete_cell_mean']==pytest.approx(-1/3)
    rows[-1]['primary']=None
    missing=m.paired_effects(rows)['C-A']['secondary_pooled']
    assert missing['complete_cells']==0
    assert missing['complete_cell_mean'] is None
    assert missing['bounds']==pytest.approx([-1/3,0])


def test_prepare_rejects_changed_license_and_source(tmp_path):
    packet=freeze_packet(tmp_path)
    corpus_path=tmp_path/'sources/corpus.json'
    value=json.loads(corpus_path.read_text())
    value['records'][0]['source']['license_sha256']='0'*64
    corpus_path.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='license hash'):
        m.prepare(corpus_path,tmp_path/'second',tmp_path/'cli')
    assert not (tmp_path/'second').exists()
    (packet/'frozen/requests'/next((packet/'frozen/requests').iterdir()).name).write_text('{}')
    with pytest.raises(ValueError,match='receipt inventory'):
        m.run(packet,FakeProvider)
    assert not (packet/'run-started.json').exists()


def test_calibration_optional_preference_omission_and_hardening():
    cases,prompt=m.calibration()
    assert 'Prefer blue text' in cases[0]['artifact']['criteria'][0]
    assert 'blue' not in cases[4]['artifact']['criteria'][0]
    assert cases[4]['expected']['o1']=='supported'
    assert 'title must use blue text' in cases[7]['artifact']['criteria'][0]
    assert cases[7]['expected']['o1']=='supported'
    assert 'report it in additions independently of coverage' in prompt
