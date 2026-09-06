"""Explicitly authorized exploratory pilot; preflight never dispatches a call.

Private inputs, review/oracle data and terminal judgments remain separate from
the provider-visible generation context and pre-final observations.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
from importlib.metadata import PackageNotFoundError, version as package_version
import json
import os
from pathlib import Path
import random
import sys
import time

from agents.providers import ProviderRequest
from agents.staged_runtime import StagedProviderRuntime, _render_generation_prompt, _semantic_plan_diagnostics
from eval.live_judge_controls import _write, _append, _provider, prepare_private_output
from eval.pilot_ledger import CAP, PilotLedger, PilotStop, envelope
from eval.pilot_preparation import audit_candidates, digest, render_request, verify_preparation
from eval.provider_runtime_config import parse_provider_slot
from label_plane.exploratory_judge import JudgeRequest, ReferenceConstraint, serialize_judge_request, validate_judge_request
from label_plane.judge_prompt_comparison import parse_evidence_response, _unique_keys

ROOT = Path(__file__).resolve().parents[1]
LIMITS = {'T1':384, 'T2':256, 'artifact':256}
CONTEXT_BYTES = {'T1':1500, 'T2':1024, 'artifact':768}
TEMPLATES = {
    'T1': 'T1 Requirement:\n{requirement}\nReturn JSON only with arrays: constraints, quantities, unresolved_references, assumptions, contradictions, conditional_semantics, atomic_obligations. List ALL explicit obligations, including conditions, exceptions, limits and permissions, in constraints. Do not invent omitted information. Use concise full clauses, not keyword summaries. Each atomic_obligations item has constraint_index (1-based), atom_type="condition", status="present" or "uncertain". One item per constraint. Other arrays may be empty. No hidden reasoning or extra keys.',
    'T2': 'T2 Interpretation:\n{interpretation_json}\nReturn JSON only with arrays of strings: validation_checks, planned_tools, coverage_targets. Provide checks and coverage for ALL interpreted obligations, preserving their conditions and limits. Use concise full clauses. planned_tools may be empty. No extra keys or hidden reasoning.',
    'artifact': 'Artifact\nRequirement:{requirement}\nPlan:{plan_json}\nReturn JSON only with exactly these keys: {output_keys}. Write actionable acceptance criteria preserving all explicit obligations, including conditions, exceptions and limits. Do not invent absent information. Full concise sentences, no markdown or hidden reasoning.',
    'retry':'No retries are authorized.'}
SOURCE_FILES = ('eval/pilot_runtime.py','eval/pilot_ledger.py','eval/pilot_preparation.py',
    'eval/exploratory_cost.py','eval/provider_runtime_config.py','eval/live_judge_controls.py',
    'agents/staged_runtime.py','agents/providers.py','agents/checkpoints.py',
    'protocol/context_management.py','protocol/atomic_obligations.py','protocol/conditional_semantics.py',
    'label_plane/exploratory_judge.py','label_plane/judge_prompt_comparison.py')


def read(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=_unique_keys)


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def runtime_environment():
    try: sdk=package_version('openai')
    except PackageNotFoundError: sdk=None
    return {'python':sys.version,'openai':sdk}


def request(prompt, limit):
    return ProviderRequest(prompt, {}, 'opaque', 'test_gen', limit)


def _authorization(auth):
    if (auth.get('schema_version') != 'pilot-authorization/v1'
        or type(auth.get('approved_cap_microusd')) is not int or auth['approved_cap_microusd'] != CAP
        or type(auth.get('repetitions')) is not int or auth['repetitions'] != 5
        or auth.get('exploratory_llm_scope_confirmed') is not True
        or not isinstance(auth.get('source'), str) or not auth['source'].strip()):
        raise ValueError('explicit US$7 / five-repetition / exploratory scope attestation required')


def _slots(specs):
    slots = [parse_provider_slot(spec) for spec in specs]
    if len(slots)!=2 or {s.kind for s in slots}!={'openai','deepseek'} or len({s.id for s in slots})!=2:
        raise ValueError('two distinct OpenAI/DeepSeek slots required')
    return {s.id:s for s in slots}


def create_run(package, specs, authorization, output, *, _carryover=None):
    _authorization(authorization)
    package = Path(package).resolve()
    verify_preparation(package)
    slots = _slots(specs)
    rows = read(package/'corpus-candidates.json')['records']
    audit = audit_candidates(rows)
    reviews = read(package/'screening-requests.json')
    diagnostic = [json.loads(line) for line in (package/'requests.jsonl').read_text().splitlines()]
    if len(reviews)!=30 or len(diagnostic)!=48:
        raise ValueError('screening/diagnostic inventory mismatch')
    frozen_prices = read(package/'prices.json')
    for slot, price in zip(slots.values(), frozen_prices, strict=True):
        if any(str(slot.pricing.to_dict()[k]) != str(price[k]) for k in ('input_usd_per_1k','cached_input_usd_per_1k','output_usd_per_1k')):
            raise ValueError('prepared prices differ from provider slots')
    package_hash = file_hash(package/'manifest.json')
    calls, trajectories = [], []

    def add(identifier, slot, phase, bound, limit, prompt=None):
        call = dict(id=identifier,slot=slot,phase=phase,input_bound=bound,output_bound=limit)
        if prompt is not None: call['prompt_sha256']=digest(prompt)
        calls.append(call)

    for row in reviews:
        for slot in slots:
            limit=384 if _carryover and row['kind']=='source_faithfulness' else 192
            add('screen:'+row['review_id']+':'+slot,slot,'screening',len(row['prompt'].encode())+64,limit,row['prompt'])
    for row in diagnostic:
        prompt=render_request(row['request'])
        for slot in slots:
            add('diag:'+row['request']['occurrence_id']+':'+slot,slot,'diagnostics',len(prompt.encode())+64,96,prompt)
    for row in rows:
        for variant,field in (('clean','clean_requirement'),('smelly','defective_requirement')):
            for repetition in range(5):
                for slot in slots:
                    identifier=digest([package_hash,row['source_intent_id'],variant,repetition,slot])[:24]
                    trajectories.append(dict(id=identifier,intent_id=row['source_intent_id'],project_id=row['project_id'],variant=variant,repetition=repetition,slot=slot))
                    requirement=row[field]
                    t1=_render_generation_prompt(TEMPLATES['T1'],requirement=requirement)
                    t2=_render_generation_prompt(TEMPLATES['T2'],interpretation_json='')
                    final=_render_generation_prompt(TEMPLATES['artifact'],requirement=requirement,plan_json='',output_keys=['criterion'])
                    for stage,bound in (('T1',len(t1.encode())+64),('T2',len(t2.encode())+CONTEXT_BYTES['T1']+64),('artifact',len(final.encode())+CONTEXT_BYTES['T2']+64)):
                        add(identifier+':'+stage,slot,'generation',bound,LIMITS[stage],t1 if stage=='T1' else None)
    trajectories.sort(key=lambda t:digest(['trajectory-order/v1',t['id']]))
    duplicate_ids=set(random.Random(0).sample([t['id'] for t in trajectories],96))
    occurrences=[]
    by_id={r['source_intent_id']:r for r in rows}
    for trajectory in trajectories:
        reference=by_id[trajectory['intent_id']]['reference_constraint']['text']
        empty=serialize_judge_request(JudgeRequest('opaque','x',(ReferenceConstraint('c1',reference),)))
        bound=len(render_request(empty).encode())+CONTEXT_BYTES['artifact']+64
        for copy in range(2 if trajectory['id'] in duplicate_ids else 1):
            occurrence=digest(['pilot-judge',trajectory['id'],copy])[:24]
            occurrences.append(dict(id=occurrence,trajectory_id=trajectory['id'],duplicate=bool(copy)))
            for slot in slots: add('judge:'+occurrence+':'+slot,slot,'judging',bound,96)
    occurrences.sort(key=lambda o:digest(['judge-order/v1',o['id']]))
    if _carryover:
        prior_calls={c['id']:c for c in _carryover['calls']}
        current_calls={c['id']:c for c in calls}
        reused=0
        for identifier in _carryover['completed']:
            if identifier in current_calls:
                if current_calls[identifier]!=prior_calls[identifier]: raise ValueError('changed call cannot reuse predecessor evidence')
                reused+=1
            else: calls.append({**prior_calls[identifier],'phase':'screening_history'})
        if reused!=48 or len(calls)!=2760: raise ValueError('revision must retain 48 pair reviews and replace only 12 oracle reviews')
    budget=envelope(calls,{s.id:s.pricing for s in slots.values()})
    if not budget['within_cap']: raise ValueError(f'full pilot envelope exceeds US$7: {budget["reserved_microusd"]} microUSD')
    body={'schema_version':'pilot-run/v1','package':str(package),'package_sha256':package_hash,
          'authorization':authorization,'providers':specs,'calls':calls,'budget':budget,
          'trajectories':trajectories,'occurrences':occurrences,
          'source_sha256':{name:file_hash(ROOT/name) for name in SOURCE_FILES},
          'environment':runtime_environment(),
          'prompt_templates':TEMPLATES,'stage_limits':LIMITS,'context_bytes':CONTEXT_BYTES,
          'claim_level':'exploratory_llm_only','confirmatory_authorized':False,
          'identity_limitation':'requested and returned model identifiers; no independent immutable-weights verification',
          'counts':dict(intents=24,projects=audit['project_count'],base_episodes=240,trajectories=480,duplicates=96,
                        screening_calls=60,diagnostic_calls=96,generation_calls=1440,judging_calls=1152,total_calls=2748)}
    if _carryover:
        body['supersedes']=_carryover['origin']
        body['counts'].update(screening_calls=72,total_calls=2760,reused_screening_calls=48)
    output=prepare_private_output(output)
    _write(output/'launch.json',body)
    _write(output/'launch-integrity.json',{'sha256':digest(body)})
    with PilotLedger(output/'ledger.jsonl',calls,{s.id:s.pricing for s in slots.values()},approval=True) as ledger:
        if _carryover:
            for identifier,row in _carryover['completed'].items(): ledger.adopt_completed(identifier,row,_carryover['origin']['ledger_head_before'])
    return body


def revise_screening(previous, package, output):
    """One narrow pre-diagnostic revision, preserving all costs and raw evidence.

    This intentionally validates predecessor data, not its old executable code:
    current code is frozen anew. A successor is inactive until its predecessor
    has durably stopped with a link to the successor's exact launch hash.
    """
    previous=Path(previous).resolve(); package=Path(package).resolve()
    old=read(previous/'launch.json')
    if old.get('schema_version')!='pilot-run/v1' or old.get('supersedes'):
        raise ValueError('only the initial screening revision is supported')
    if digest(old)!=read(previous/'launch-integrity.json')['sha256']: raise ValueError('predecessor launch integrity mismatch')
    _authorization(old['authorization']); slots=_slots(old['providers'])
    verify_preparation(old['package']); verify_preparation(package)
    if file_hash(Path(old['package'])/'manifest.json')!=old['package_sha256']: raise ValueError('predecessor package changed')
    for name in ('corpus-candidates.json','reference-constraints.json','natural-sample-with-history.json','prices.json'):
        if read(Path(old['package'])/name)!=read(package/name): raise ValueError('revision changes corpus, reference, sampling or prices')
    if not (previous/'ledger.jsonl').is_file(): raise ValueError('predecessor ledger missing')
    with PilotLedger(previous/'ledger.jsonl',old['calls'],{s.id:s.pricing for s in slots.values()},approval=True) as ledger:
        expected={c['id'] for c in old['calls'] if c['phase']=='screening'}
        if set(ledger.completed)!=expected or len(expected)!=60: raise ValueError('requires exactly the initial 60 screening calls; no diagnostic outcomes')
        carry={'calls':old['calls'],'completed':ledger.completed,
               'origin':{'directory':str(previous),'launch_sha256':file_hash(previous/'launch.json'),'ledger_head_before':ledger.head}}
        body=create_run(package,old['providers'],old['authorization'],output,_carryover=carry)
        try: ledger.stop('superseded_by:'+digest(body))
        except PilotStop:
            # Only an acknowledged durable stop activates the successor.
            if ledger.pending: raise
        _load(output)
        return body


def _load(directory):
    directory=Path(directory)
    run=read(directory/'launch.json')
    if digest(run)!=read(directory/'launch-integrity.json')['sha256']: raise ValueError('launch integrity mismatch')
    _authorization(run['authorization'])
    verify_preparation(run['package'])
    if file_hash(Path(run['package'])/'manifest.json')!=run['package_sha256']: raise ValueError('package manifest changed')
    if any(file_hash(ROOT/name)!=expected for name,expected in run['source_sha256'].items()):
        raise ValueError('runtime source changed after freeze')
    if run['environment']!=runtime_environment():
        raise ValueError('runtime environment changed after freeze')
    if not (directory/'ledger.jsonl').is_file():
        raise ValueError('frozen run ledger missing; cannot create a new budget')
    if run.get('supersedes'):
        from eval.pilot_ledger import inspect_ledger
        prior=Path(run['supersedes']['directory']); old=read(prior/'launch.json')
        if file_hash(prior/'launch.json')!=run['supersedes']['launch_sha256']: raise ValueError('predecessor launch changed')
        old_slots=_slots(old['providers'])
        report,_=inspect_ledger(prior/'ledger.jsonl',old['calls'],{s.id:s.pricing for s in old_slots.values()})
        last=json.loads((prior/'ledger.jsonl').read_text().splitlines()[-1])
        if (report['state']!='stopped' or report['pending_count'] or last['event']!='stop'
            or last['prev']!=run['supersedes']['ledger_head_before']
            or last['data']['reason']!='superseded_by:'+digest(run)):
            raise ValueError('successor inactive until predecessor is durably stopped')
    return run,_slots(run['providers'])


def _admission_blockers(directory,run):
    path=Path(directory)/'admission.json'
    if not path.exists(): return ['admission_missing']
    admission=read(path)
    expected={t['intent_id'] for t in run['trajectories']}
    records=admission.get('records',[])
    if (admission.get('schema_version')!='pilot-admission/v1' or admission.get('package_sha256')!=run['package_sha256']
        or admission.get('review_scope')!='AI-assisted exploratory; not independent human validation'
        or len(records)!=24 or {r.get('intent_id') for r in records}!=expected): return ['admission_invalid']
    for row in records:
        for field in ('rights_evidence','source_revision_evidence','independence_disposition','manipulation_disposition','review_evidence'):
            if not isinstance(row.get(field),str) or not row[field].strip(): return ['admission_evidence_missing']
        if row.get('decision')!='admit_exploratory': return ['candidate_not_admitted']
    if not admission.get('control_oracle_dispositions'): return ['control_review_missing']
    return []


def _gates(directory,run,completed):
    blockers=_admission_blockers(directory,run)
    for phase in ('screening','diagnostics'):
        ids={c['id'] for c in run['calls'] if c['phase']==phase}
        if not ids.issubset(completed): blockers.append(phase+'_incomplete')
    diagnostic=Path(directory)/'diagnostics.json'
    if not diagnostic.exists(): blockers.append('diagnostic_gate_not_passed')
    elif 'diagnostics_incomplete' not in blockers:
        expected=_diagnostic_report(run,completed)
        if read(diagnostic)!=expected or expected['decision']!='continue': blockers.append('diagnostic_gate_not_passed')
    return blockers


def preflight(directory):
    run,slots=_load(directory)
    # Read-only inspection: no lock files, reservations, adapters or keys resolved.
    from eval.pilot_ledger import inspect_ledger
    report,completed=inspect_ledger(Path(directory)/'ledger.jsonl',run['calls'],{s.id:s.pricing for s in slots.values()})
    blockers=_gates(directory,run,completed)
    if report['state']!='ready': blockers.append('ledger_stopped_or_pending')
    return {'decision':'no_go' if blockers else 'go_exploratory','blockers':blockers,
            'confirmatory_authorized':False,**report,'counts':run['counts']}


def _judge_request(row):
    return validate_judge_request(row)


def _collect_screening(directory,run,ledger,providers):
    rows=read(Path(run['package'])/'screening-requests.json')
    results=[]
    for row in rows:
        fields={'version_a_issues','version_b_issues','uncertainty'} if row['kind']=='manipulation' else {'source_mismatch','context_leakage','ambiguity_issues'}
        for slot,provider in providers.items():
            identifier='screen:'+row['review_id']+':'+slot
            raw=ledger.complete(identifier,provider,request(row['prompt'],ledger.plan[identifier]['output_bound']))
            try:
                parsed=json.loads(raw,object_pairs_hook=_unique_keys)
                if set(parsed)!=fields or any(not isinstance(v,list) or any(not isinstance(x,str) for x in v) for v in parsed.values()): raise ValueError('screening schema')
                valid=True
            except (ValueError,TypeError): parsed=None; valid=False
            results.append(dict(review_id=row['review_id'],kind=row['kind'],slot=slot,valid=valid,response=parsed))
    _write(Path(directory)/'screening.json',{'schema_version':'pilot-screening/v1','results':results,
           'automatic_admission':False,'valid_responses':sum(r['valid'] for r in results)})


def _collect_diagnostics(directory,run,ledger,providers):
    package=Path(run['package'])
    rows=[json.loads(line) for line in (package/'requests.jsonl').read_text().splitlines()]
    for row in rows:
        identifier=row['request']['occurrence_id']
        for slot,provider in providers.items():
            ledger.complete('diag:'+identifier+':'+slot,provider,request(render_request(row['request']),96))
    _write(Path(directory)/'diagnostics.json',_diagnostic_report(run,ledger.completed))


def _diagnostic_report(run,completed):
    package=Path(run['package'])
    rows=[json.loads(line) for line in (package/'requests.jsonl').read_text().splitlines()]
    oracles={c['request']['occurrence_id']:c['oracle'] for c in read(package/'control-oracles.json')['cases']}
    counts={s['id']:Counter(omission_detected=0,false_omission=0,partial_abstained=0,invalid=0) for s in run['providers']}
    results=[]
    for row in rows:
        identifier=row['request']['occurrence_id']
        for slot in counts:
            raw=completed['diag:'+identifier+':'+slot]['response']
            try:
                _,grounded=parse_evidence_response(raw,_judge_request(row['request']))
                value=json.loads(raw)
                if not grounded: raise ValueError('ungrounded quote')
            except ValueError: value=None; counts[slot]['invalid']+=1
            oracle=oracles.get(identifier)
            if oracle and value:
                operation=oracle['operation']; status=value['status']
                counts[slot]['omission_detected']+=int(operation=='long_omitted' and status=='omitted')
                counts[slot]['false_omission']+=int(operation in {'long_covered','concise_covered','distributed_covered'} and status=='omitted')
                counts[slot]['partial_abstained']+=int(operation=='insufficient' and status=='uncertain')
            results.append(dict(occurrence_id=identifier,slot=slot,block=row['block'],response=value))
    decision='continue' if all(c['omission_detected']>=5 and c['false_omission']<=1 and c['invalid']==0 and c['partial_abstained']>=5 for c in counts.values()) else 'pause'
    return {'decision':decision,'counts':counts,'results':results,
            'units':'six source seeds, eighteen complete variants, six partial excerpts per judge; natural sample is not accuracy'}


def stage_alert(stage,payload,observed):
    """Frozen lexical/uncertainty diagnostic, never a semantic truth label."""
    if stage=='T1':
        return bool(payload.get('unresolved_references') or payload.get('assumptions') or payload.get('contradictions'))
    if stage=='T2':
        interpretation=next(e['payload'] for e in observed if e['stage']=='T1')
        pair={'generation_contract':{'test_gen':{'output_keys':['criterion']}}}
        return bool(_semantic_plan_diagnostics(pair,'test_gen',interpretation,payload)['errors'])
    if stage=='T3': return bool(payload['errors'])
    raise ValueError('unknown stage')


def _collect_generation(directory,run,ledger,providers):
    package=Path(run['package']); directory=Path(directory)
    rows={r['source_intent_id']:r for r in read(package/'corpus-candidates.json')['records']}
    for trajectory in run['trajectories']:
        identifier=trajectory['id']; output=directory/(identifier+'.execution.json')
        if output.exists(): continue
        events=directory/(identifier+'.events.jsonl')
        if events.exists() or any(identifier+':'+s in ledger.completed for s in LIMITS):
            raise ValueError('interrupted trajectory: preserve original timing; manual reconciliation required')
        row=rows[trajectory['intent_id']]; provider=providers[trajectory['slot']]
        pair={'clean_requirement':row['clean_requirement'],'smelly_requirement':row['defective_requirement'],
              'generation_contract':{'test_gen':{'output_keys':['criterion']}}}
        origin=time.monotonic(); observed=[]
        def sink(stage,payload):
            if stage in {'T1','T2'}:
                context={k:payload[k] for k in ('constraints','atomic_obligations')} if stage=='T1' else payload
                if len(json.dumps(context,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())>CONTEXT_BYTES[stage]:
                    raise ValueError('stage context exceeds frozen byte bound; no truncation')
            alert=stage_alert(stage,payload,observed)
            event={'stage':stage,'available_ms':(time.monotonic()-origin)*1000,'alert':alert,
                   'cost_microusd':0 if stage=='T3' else ledger.completed[identifier+':'+stage]['actual_cost_microusd'],
                   'payload':payload}
            _append(events,event); observed.append(event)
        def complete(req,stage,attempt):
            return ledger.complete(identifier+':'+stage,provider,req)
        try:
            execution=StagedProviderRuntime(provider,stage_completion=complete,prompt_templates=TEMPLATES,
                checkpoint_sink=sink,stage_output_tokens=LIMITS,max_stage_attempts=1).execute(pair,trajectory['variant'],'test_gen')
            terminal_ms=(time.monotonic()-origin)*1000
            # Bound the escaped CRITERIA value inside the judge's JSON, not just
            # the first artifact serialization (quotes/backslashes expand).
            if len(json.dumps(json.dumps(execution.artifact,ensure_ascii=True),ensure_ascii=True).encode())>CONTEXT_BYTES['artifact']:
                raise ValueError('artifact exceeds frozen byte bound; no truncation')
            _write(output,{'trajectory':trajectory,'execution':asdict(execution),'temporal':{
                'episode_id':identifier,'intent_id':trajectory['intent_id'],'terminal_ms':terminal_ms,'terminal_defect':None,
                'stages':[{k:v for k,v in e.items() if k!='payload'} for e in observed]}})
        except Exception:
            _write(directory/(identifier+'.incomplete.json'),{'trajectory_id':identifier,'completed_stages':[e['stage'] for e in observed],
                    'state':'incomplete; no automatic retry; raw response/accounting preserved in ledger'})
            raise
    from eval.temporal_diagnostics import analyze
    temporal=[read(directory/(t['id']+'.execution.json'))['temporal'] for t in run['trajectories']]
    if not (directory/'generation.json').exists():
        _write(directory/'generation.json',{'completed_trajectories':len(temporal),
               'temporal':analyze(temporal),'policy':'uncertainty-and-lexical-plan-coverage/v1',
               'lineage_increment_limitation':'T3 rechecks the same plan; this deterministic policy cannot establish added provenance value'})


def _collect_judging(directory,run,ledger,providers):
    directory=Path(directory)
    rows={r['source_intent_id']:r for r in read(Path(run['package'])/'corpus-candidates.json')['records']}
    trajectories={t['id']:t for t in run['trajectories']}
    results=[]; counts={relation:Counter(planned=576,completed=0,invalid=0) for relation in ('self','cross')}
    for occurrence in run['occurrences']:
        trajectory=trajectories[occurrence['trajectory_id']]
        artifact=read(directory/(trajectory['id']+'.execution.json'))['execution']['artifact']
        criteria=json.dumps(artifact,ensure_ascii=True)
        reference=rows[trajectory['intent_id']]['reference_constraint']['text']
        judge=JudgeRequest(occurrence['id'],criteria,(ReferenceConstraint('c1',reference),))
        for slot,provider in providers.items():
            relation='self' if slot==trajectory['slot'] else 'cross'
            raw=ledger.complete('judge:'+occurrence['id']+':'+slot,provider,request(render_request(serialize_judge_request(judge)),96))
            try:
                _,grounded=parse_evidence_response(raw,judge)
                if not grounded: raise ValueError('ungrounded quote')
                value=json.loads(raw); counts[relation][value['label']]+=1
            except ValueError: value=None; counts[relation]['invalid']+=1
            counts[relation]['completed']+=1
            results.append(dict(occurrence_id=occurrence['id'],slot=slot,relation=relation,duplicate=occurrence['duplicate'],response=value))
    _write(directory/'judging.json',{'counts':counts,'results':results,'human_truth':False})


def run_phase(directory,phase,*,provider_factory=None,environ=None):
    if phase not in {'screening','diagnostics','generation','judging'}: raise ValueError('unknown phase')
    directory=Path(directory); run,slots=_load(directory)
    with PilotLedger(directory/'ledger.jsonl',run['calls'],{s.id:s.pricing for s in slots.values()},approval=True) as ledger:
        if phase=='diagnostics' and (_admission_blockers(directory,run) or any(c['id'] not in ledger.completed for c in run['calls'] if c['phase']=='screening')):
            raise ValueError('screening and documented admission required before diagnostics')
        if phase in {'generation','judging'} and _gates(directory,run,ledger.completed): raise ValueError('pilot gates not passed')
        if phase=='judging' and any(not (directory/(t['id']+'.execution.json')).exists() for t in run['trajectories']): raise ValueError('generation incomplete')
        if (directory/(phase+'.json')).exists(): return ledger.report()
        env=dict(os.environ if environ is None else environ)
        if provider_factory is None and runtime_environment()['openai'] is None: raise ValueError('provider SDK missing')
        if provider_factory is None and any(not env.get(s.api_key_env) for s in slots.values()): raise ValueError('required private provider credential missing')
        providers={s.id:provider_factory(s) if provider_factory else _provider(s,env) for s in slots.values()}
        {'screening':_collect_screening,'diagnostics':_collect_diagnostics,'generation':_collect_generation,'judging':_collect_judging}[phase](directory,run,ledger,providers)
        return ledger.report()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['create','revise-screening','preflight','screening','diagnostics','generation','judging'])
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--package',type=Path); parser.add_argument('--config',type=Path); parser.add_argument('--authorization',type=Path)
    parser.add_argument('--env-file',type=Path)
    parser.add_argument('--previous-run',type=Path)
    args=parser.parse_args()
    if args.phase=='create':
        if not all((args.package,args.config,args.authorization)): parser.error('create requires package, config and authorization')
        value=create_run(args.package,read(args.config)['providers'],read(args.authorization),args.run)
        report={'counts':value['counts'],'budget':value['budget'],'state':'frozen; not admitted'}
    elif args.phase=='revise-screening':
        if not args.package or not args.previous_run: parser.error('revision requires package and previous-run')
        value=revise_screening(args.previous_run,args.package,args.run)
        report={'counts':value['counts'],'budget':value['budget'],'state':'revised; prior charges retained; admission pending'}
    elif args.phase=='preflight': report=preflight(args.run)
    else:
        env=dict(os.environ)
        if args.env_file:
            from label_plane.private_env import load_private_env
            load_private_env(args.env_file,environ=env)
        report=run_phase(args.run,args.phase,environ=env)
    # Never print content, identities, private hashes or credentials.
    print(json.dumps({k:v for k,v in report.items() if k!='ledger_head'},indent=2))


if __name__=='__main__':
    try: main()
    except (PilotStop, ValueError):
        # SDK exceptions can contain response bodies. Keep them out of terminal
        # logs; the private journal preserves observations and pending charges.
        print(json.dumps({'state':'blocked_or_stopped','action':'inspect private preflight/journal; do not reset or retry ambiguous calls'}))
        raise SystemExit(2) from None
