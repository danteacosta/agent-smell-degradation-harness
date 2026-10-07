import json
from pathlib import Path
import pytest
from scripts import claude55_shared_omission as study
from scripts import shared_omission_e2e as so


def stream(five=0.1, week=0.1):
    return json.dumps({'type':'rate_limit_event','rate_limit_info':{'status':'allowed_warning',
        'isUsingOverage':False,'unifiedWindows':{'five_hour':{'utilization':five,'resetsAt':9999999999},
        'seven_day':{'utilization':week,'resetsAt':9999999999}}}})


def packet(tmp_path):
    ta=study.ma.ta
    root=tmp_path/'run';parent=tmp_path/'parent';page=tmp_path/'page';page.write_text('page')
    control={'qualified':True,'expected':{'broken_save':'assertion_alarm','keeps_rule':'quiet','lost_rule':'assertion_alarm'},
        'observed':{'broken_save':'assertion_alarm','keeps_rule':'quiet','lost_rule':'assertion_alarm'},'runner_sha256':ta.sha256_file(ta.RUNNER)}
    ta.put(root/'controls/controls.json',control)
    manifest={'schema_version':so.SCHEMA,'model':'gpt-6-astra','code_context_role':'confirmed_mutant',
        'selected_mutants':{'case':'slot'},'cases':[{'case':'case','roles':{'mutant':['slot']},
        'artifacts':{'slot':{'artifact_path':str(page),'artifact_sha256':ta.sha256_file(page)}}}],
        'script_sha256':ta.sha256_file(Path(study.ma.__file__)), 'test_anchor_script_sha256':ta.sha256_file(Path(ta.__file__)),
        'extension_script_sha256':ta.sha256_file(Path(so.__file__)), 'image':ta.IMAGE,'runner_sha256':ta.sha256_file(ta.RUNNER),
        'schedule':[{'call_id':'one','case':'case'}]}
    ta.put(parent/'frozen/manifest.json',manifest);ta.put(parent/'frozen/controls.json',control)
    ta.put(parent/'frozen/prompts/one.txt','public prompt');ta.put(parent/'frozen/receipt.json',{'files':ta.inventory(parent/'frozen')})
    exe=tmp_path/'fake';exe.write_text('fake executable');baseline=tmp_path/'quota';baseline.write_text(stream())
    before=ta.inventory(parent);out=root/'study';study.prepare(out,parent,baseline,exe)
    assert ta.inventory(parent)==before
    return out,baseline,parent,exe


def fake_provider(monkeypatch,quota):
    class Provider:
        def __init__(self,**kwargs):self.capture=kwargs['evidence_directory']
        def complete(self,request):
            assert request.prompt=='public prompt'
            study.ma.ta.put(self.capture/'stdout.jsonl',stream(*quota))
            return 'not a suite'
    monkeypatch.setattr(study,'ClaudeCLIProvider',Provider)


def test_new_models_and_frozen_inputs(tmp_path):
    out,baseline,parent,exe=packet(tmp_path)
    assert study.MODELS==('claude-sonnet-5-5','claude-opus-5-5')
    assert len(study.verify(out)['schedule'])==2
    for model in study.MODELS:
        assert (out/model/'frozen/prompts/one.txt').read_bytes()==(parent/'frozen/prompts/one.txt').read_bytes()
    with pytest.raises(FileExistsError):study.prepare(out,parent,baseline,exe)


def test_quota_exhaustion_preserves_attempt_and_only_unattempted_resume(tmp_path,monkeypatch):
    out,baseline,_,_=packet(tmp_path);fake_provider(monkeypatch,(1,.1))
    with pytest.raises(RuntimeError):study.generate(out,baseline)
    assert len(study.attempts(out))==1
    stop=json.loads((out/'quota-segments/000/stopped.json').read_text())
    assert stop['resume_after_reset'] is True
    with pytest.raises(RuntimeError,match='reset'):study.generate(out,baseline)
    # Authorize the simulated next window only after reset+60, keeping prior evidence unchanged.
    stop['reset_at']=1;(out/'quota-segments/000/stopped.json').write_text(json.dumps(stop))
    receipt=out/'quota-segments/000/receipt.json';data=json.loads(receipt.read_text())
    data['files']['quota-segments/000/stopped.json']=study.ma.ta.sha256_file(out/'quota-segments/000/stopped.json')
    receipt.write_text(json.dumps(data))
    fake_provider(monkeypatch,(.1,.1));study.generate(out,baseline)
    assert len(study.attempts(out))==2
    assert (out/'generation-completed.json').exists()
    with pytest.raises(FileExistsError):study.generate(out,baseline)


def test_weekly_reserve_and_drift_refuse_before_call(tmp_path,monkeypatch):
    out,baseline,_,_=packet(tmp_path);fake_provider(monkeypatch,(.1,.7))
    baseline.write_text(stream(.1,.7))
    with pytest.raises(RuntimeError):study.generate(out,baseline)
    assert not study.attempts(out)
    (out/study.MODELS[0]/'frozen/prompts/one.txt').write_text('changed')
    with pytest.raises((RuntimeError,ValueError)):study.verify(out)


def test_unrelated_adapter_failure_at_zero_is_not_resumable(tmp_path,monkeypatch):
    out,baseline,_,_=packet(tmp_path)
    class WrongModel:
        def __init__(self,**kwargs):self.capture=kwargs['evidence_directory']
        def complete(self,request):
            study.ma.ta.put(self.capture/'stdout.jsonl',stream(1,.1))
            raise RuntimeError('Claude stream rejected: model switch')
    monkeypatch.setattr(study,'ClaudeCLIProvider',WrongModel)
    with pytest.raises(RuntimeError,match='model switch'):study.generate(out,baseline)
    stop=json.loads((out/'quota-segments/000/stopped.json').read_text())
    assert stop['resume_after_reset'] is False
    (out/'quota-segments/000/receipt.json').unlink()
    with pytest.raises(RuntimeError,match='receipt'):study.verify(out)


def test_last_slot_weekly_breach_cannot_mark_complete(tmp_path,monkeypatch):
    out,baseline,_,_=packet(tmp_path);counter=[]
    class Provider:
        def __init__(self,**kwargs):self.capture=kwargs['evidence_directory']
        def complete(self,request):
            counter.append(1);study.ma.ta.put(self.capture/'stdout.jsonl',stream(.1,.7 if len(counter)==2 else .1))
            return 'not a suite'
    monkeypatch.setattr(study,'ClaudeCLIProvider',Provider)
    with pytest.raises(RuntimeError):study.generate(out,baseline)
    assert len(study.attempts(out))==2
    assert not (out/'generation-completed.json').exists()


def test_active_generation_refuses_verification_and_evaluation(tmp_path):
    out,_,_,_=packet(tmp_path);(out/'quota-active.lock').write_text('active')
    with pytest.raises(RuntimeError,match='active'):study.verify(out)
    with pytest.raises(RuntimeError,match='active'):study.execute(out)
