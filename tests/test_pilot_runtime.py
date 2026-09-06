import importlib.util
import json

import pytest

from eval.pilot_preparation import write_preparation, digest
from test_pilot_preparation import candidates, control_seed


def api():
    assert importlib.util.find_spec('eval.pilot_runtime'), 'pilot runtime is missing'
    from eval import pilot_runtime
    return pilot_runtime


def inputs(tmp_path):
    p=api()
    specs=[{'id':kind,'kind':kind,'model':kind+'-model','model_version':'pinned',
            'api_key_env':'TEST_KEY','base_url':None if kind=='openai' else 'https://api.deepseek.com',
            'pricing_snapshot_date':'2026-09-02','pricing_source_ref':'frozen',
            'pricing':{'input_usd_per_1k':'0.0002','cached_input_usd_per_1k':'0.00002','output_usd_per_1k':'0.0012'}} for kind in ('openai','deepseek')]
    seeds=[{**control_seed(),'seed_id':f's{i}','source_intent_id':f'intent-{i}'} for i in range(6)]
    from label_plane.exploratory_judge import JudgeRequest,ReferenceConstraint,serialize_judge_request
    pool=[{'text_id':f'{i}-{j}','project_id':f'project-{i}','criteria':'bounded request','obligation_count':2,
           'old_responses':[], 'request':serialize_judge_request(JudgeRequest(digest([i,j])[:24],'bounded request',(ReferenceConstraint('c1','bounded request'),)))}
          for i in range(6) for j in range(3)]
    package=tmp_path/'package'
    write_preparation(candidates(),seeds,pool,[s['pricing'] for s in specs],package)
    auth={'schema_version':'pilot-authorization/v1','approved_cap_microusd':7000000,'repetitions':5,
          'exploratory_llm_scope_confirmed':True,'source':'user conversation 2026-09-06'}
    return package,specs,auth


def test_full_plan_has_exact_counts_and_is_frozen_before_dispatch(tmp_path):
    package,specs,auth=inputs(tmp_path)
    manifest=api().create_run(package,specs,auth,tmp_path/'run')
    assert manifest['counts']=={'intents':24,'projects':6,'base_episodes':240,'trajectories':480,
                                'duplicates':96,'screening_calls':60,'diagnostic_calls':96,
                                'generation_calls':1440,'judging_calls':1152,'total_calls':2748}
    assert manifest['budget']['within_cap']
    assert len(manifest['calls'])==2748
    assert len({x['id'] for x in manifest['calls']})==2748


def test_missing_authorization_blocks_run_creation(tmp_path):
    package,specs,auth=inputs(tmp_path)
    auth['exploratory_llm_scope_confirmed']=False
    with pytest.raises(ValueError):api().create_run(package,specs,auth,tmp_path/'run')
    assert not (tmp_path/'run').exists()


def test_generation_cannot_bypass_screening_admission_or_diagnostics(tmp_path):
    package,specs,auth=inputs(tmp_path)
    api().create_run(package,specs,auth,tmp_path/'run')
    with pytest.raises(ValueError):api().run_phase(tmp_path/'run','generation',provider_factory=lambda slot:pytest.fail('provider built before gates'))


def test_preflight_is_read_only_and_reports_missing_gates(tmp_path):
    package,specs,auth=inputs(tmp_path)
    api().create_run(package,specs,auth,tmp_path/'run')
    report=api().preflight(tmp_path/'run')
    assert report['decision']=='no_go'
    assert report['spent_microusd']==0
    assert 'admission_missing' in report['blockers']


def test_modified_prepared_request_is_rejected(tmp_path):
    package,specs,auth=inputs(tmp_path)
    (package/'requests.jsonl').write_text('{}\n')
    with pytest.raises(ValueError):api().create_run(package,specs,auth,tmp_path/'run')


def admit_fixture(directory,run):
    value={'schema_version':'pilot-admission/v1','package_sha256':run['package_sha256'],
           'review_scope':'AI-assisted exploratory; not independent human validation',
           'control_oracle_dispositions':'test fixture review only',
           'records':[{'intent_id':identifier,'decision':'admit_exploratory',
                       **{k:'test fixture evidence only' for k in ('rights_evidence','source_revision_evidence','independence_disposition','manipulation_disposition','review_evidence')}}
                      for identifier in sorted({t['intent_id'] for t in run['trajectories']})]}
    (directory/'admission.json').write_text(json.dumps(value))


def fake_factory(package,observed,*,miss_omissions=False):
    p=api()
    expected={p.render_request(case['request']):case['oracle']['expected_status']
              for case in p.read(package/'control-oracles.json')['cases']}
    class Provider:
        name='offline-rehearsal'
        def __init__(self,slot):self.slot=slot
        def complete(self,req):
            observed.append(req)
            self.last_call_metadata={'usage':{'input_tokens':100,'output_tokens':10,'cached_tokens':0,'total_tokens':110},
                                     'response_model':self.slot.model,'response_id':'fixture'}
            if req.prompt.startswith('T1 '):
                assert set(req.pair)=={'requirement','task_family','output_keys'}
                return json.dumps({'constraints':['bounded request'],'quantities':[],
                    'unresolved_references':[],'assumptions':[],'contradictions':[],
                    'conditional_semantics':[],'atomic_obligations':[{'constraint_index':1,'atom_type':'condition','status':'present'}]})
            if req.prompt.startswith('T2 '):
                return json.dumps({'validation_checks':['bounded request'],'planned_tools':[],'coverage_targets':['bounded request']})
            if req.prompt.startswith('Artifact'):return '{"criterion":"bounded request"}'
            if req.prompt.startswith('Treat INPUT'):
                fields=('version_a_issues','version_b_issues','uncertainty') if 'version_a_issues' in req.prompt else ('source_mismatch','context_leakage','ambiguity_issues')
                return json.dumps({k:[] for k in fields})
            data=json.loads(req.prompt.split('INPUT_JSON:\n')[1])
            assert set(data)=={'CRITERIA','REFERENCE'} and not req.pair
            status=expected.get(req.prompt,'covered')
            if miss_omissions and status=='omitted':status='covered'
            return json.dumps({'label':{'covered':'clean','omitted':'moderate','uncertain':'not_visible'}[status],
                               'status':status,'evidence':data['CRITERIA'][:60] if status=='covered' else ''})
    return Provider


def test_complete_sequential_rehearsal_preserves_counts_blinding_and_timing(tmp_path):
    package,specs,auth=inputs(tmp_path); p=api(); directory=tmp_path/'run'
    run=p.create_run(package,specs,auth,directory); observed=[]
    factory=fake_factory(package,observed)
    p.run_phase(directory,'screening',provider_factory=factory)
    assert p.preflight(directory)['decision']=='no_go'
    admit_fixture(directory,run)
    p.run_phase(directory,'diagnostics',provider_factory=factory)
    assert p.preflight(directory)['decision']=='go_exploratory'
    p.run_phase(directory,'generation',provider_factory=factory)
    files=list(directory.glob('*.execution.json'))
    assert len(files)==480
    for path in files:
        execution=p.read(path)
        times=[s['available_ms'] for s in execution['temporal']['stages']]
        assert len(times)==3 and times==sorted(times) and times[-1]<execution['temporal']['terminal_ms']
        assert execution['temporal']['terminal_defect'] is None
        assert execution['execution']['provider_meta']['context_management']['compaction_count']==0
    p.run_phase(directory,'judging',provider_factory=factory)
    counts=p.read(directory/'judging.json')['counts']
    assert counts['self']['completed']==counts['cross']['completed']==576
    assert len(observed)==2748
    before=len(observed)
    p.run_phase(directory,'screening',provider_factory=factory)
    p.run_phase(directory,'judging',provider_factory=factory)
    assert len(observed)==before
    before_files={str(f):f.stat().st_mtime_ns for f in directory.iterdir()}
    assert p.preflight(directory)['completed_calls']==2748
    assert {str(f):f.stat().st_mtime_ns for f in directory.iterdir()}==before_files


def test_bad_diagnostic_gate_cannot_dispatch_generation(tmp_path):
    package,specs,auth=inputs(tmp_path); p=api(); directory=tmp_path/'run'
    run=p.create_run(package,specs,auth,directory); observed=[]
    factory=fake_factory(package,observed,miss_omissions=True)
    p.run_phase(directory,'screening',provider_factory=factory)
    admit_fixture(directory,run)
    p.run_phase(directory,'diagnostics',provider_factory=factory)
    assert p.read(directory/'diagnostics.json')['decision']=='pause'
    tampered=p.read(directory/'diagnostics.json'); tampered['decision']='continue'
    (directory/'diagnostics.json').write_text(json.dumps(tampered))
    with pytest.raises(ValueError):p.run_phase(directory,'generation',provider_factory=lambda slot:pytest.fail('gate bypass'))


def test_runtime_does_not_invent_t2_alert_from_future_terminal_label():
    p=api()
    interpretation={'constraints':['Only the owner may delete reports.'],'quantities':[],
                    'unresolved_references':[],'assumptions':[],'contradictions':[],
                    'conditional_semantics':[],'atomic_obligations':[{'constraint_index':1,'atom_type':'condition','status':'present'}]}
    assert p.stage_alert('T1',interpretation,[]) is False
    assert p.stage_alert('T2',{'validation_checks':['format date'],'coverage_targets':['format date'],'planned_tools':[]},[{'stage':'T1','payload':interpretation}]) is True


def test_missing_ledger_never_starts_a_new_budget(tmp_path):
    package,specs,auth=inputs(tmp_path); p=api(); directory=tmp_path/'run'
    p.create_run(package,specs,auth,directory)
    (directory/'ledger.jsonl').unlink()
    with pytest.raises(ValueError):p.run_phase(directory,'screening',provider_factory=lambda slot:pytest.fail('budget reset'))


def test_offline_preparation_does_not_require_optional_provider_sdk(tmp_path,monkeypatch):
    from importlib.metadata import PackageNotFoundError
    package,specs,auth=inputs(tmp_path); p=api()
    def unavailable(name):raise PackageNotFoundError(name)
    monkeypatch.setattr(p,'package_version',unavailable)
    run=p.create_run(package,specs,auth,tmp_path/'run')
    assert run['environment']['openai'] is None
    assert p.preflight(tmp_path/'run')['completed_calls']==0


def test_incomplete_trajectory_is_preserved_and_cannot_be_retimed(tmp_path):
    package,specs,auth=inputs(tmp_path); p=api(); directory=tmp_path/'run'
    run=p.create_run(package,specs,auth,directory); observed=[]
    factory=fake_factory(package,observed)
    p.run_phase(directory,'screening',provider_factory=factory); admit_fixture(directory,run)
    p.run_phase(directory,'diagnostics',provider_factory=factory)
    class BadArtifact(factory):
        def complete(self,req):
            result=super().complete(req)
            return '{"criterion":"'+'x'*900+'"}' if req.prompt.startswith('Artifact') else result
    with pytest.raises(ValueError):p.run_phase(directory,'generation',provider_factory=BadArtifact)
    assert len(list(directory.glob('*.incomplete.json')))==1
    count=len(observed)
    with pytest.raises(ValueError):p.run_phase(directory,'generation',provider_factory=factory)
    assert len(observed)==count
