"""Frozen, sequential auxiliary study; cannot reopen the failed pilot gate."""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
import fcntl
import hashlib
from importlib.metadata import distributions
import json
import os
from pathlib import Path
import subprocess
import sys

from agents.providers import ProviderRequest
from eval.exploratory_cost import TokenBounds
from eval.live_judge_controls import _provider, _write, prepare_private_output
from eval.pilot_ledger import CAP, PilotLedger, PilotStop, envelope, inspect_ledger
from eval.pilot_preparation import digest
from eval.provider_runtime_config import parse_provider_slot
from label_plane.judge_prompt_comparison import _unique_keys
from label_plane.private_env import load_private_env
from label_plane.scoped_judge import OPERATIONS, build_cases, build_prompt, parse_response

ROOT=Path(__file__).resolve().parents[1]
OUTPUT_LIMIT=512
AUXILIARY_CAP=1_000_000
EARLIER_UNRESOLVED=218
SOURCE_DIRS=('agents','eval','feature_plane','label_plane','observability','protocol',
             'agent_harness','pairs','taxonomy','baselines','mitigation','wedge','replay','gates')


def read(path):
    path=Path(path)
    if path.is_symlink():raise ValueError('symlink evidence rejected')
    return json.loads(path.read_text(),object_pairs_hook=_unique_keys)


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_hashes():
    return {str(p.relative_to(ROOT)):file_hash(p) for directory in SOURCE_DIRS
            for p in sorted((ROOT/directory).rglob('*.py'))}


def environment():
    return {'python':sys.version,'packages':sorted(
        (d.metadata['Name'],d.version) for d in distributions() if d.metadata['Name'])}


@contextmanager
def parent_lock(parent):
    path=Path(parent)/'ledger.jsonl.lock'
    if path.is_symlink() or not path.is_file():raise ValueError('parent lock missing')
    with path.open('rb') as handle:
        fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield


def parent_snapshot(parent):
    parent=Path(parent).resolve()
    launch=read(parent/'launch.json')
    if (launch.get('schema_version')!='pilot-run/v1'
        or read(parent/'launch-integrity.json')!={'sha256':digest(launch)}
        or launch['authorization'].get('approved_cap_microusd')!=CAP
        or launch['authorization'].get('exploratory_llm_scope_confirmed') is not True
        or read(parent/'diagnostics.json').get('decision')!='pause'):
        raise ValueError('a preserved failed exploratory pilot is required')
    slots={s['id']:parse_provider_slot(s) for s in launch['providers']}
    prices={k:s.pricing for k,s in slots.items()}
    if len(slots)!=2 or {s.kind for s in slots.values()}!={'openai','deepseek'}:
        raise ValueError('two provider slots required')
    report,completed=inspect_ledger(parent/'ledger.jsonl',launch['calls'],prices)
    if report['state']!='ready':raise PilotStop('parent budget is unresolved')
    if envelope(launch['calls'],prices)!=launch['budget']:
        raise ValueError('parent envelope mismatch')
    remaining=sum(prices[c['slot']].reservation_microusd(
        TokenBounds(c['input_bound'],c['output_bound']))
        for c in launch['calls'] if c['id'] not in completed)
    snapshot={'directory':str(parent),'files':{name:file_hash(parent/name) for name in
              ('launch.json','launch-integrity.json','diagnostics.json','ledger.jsonl')},
              'ledger_head':report['ledger_head'],'spent_microusd':report['spent_microusd'],
              'remaining_direct_microusd':remaining,
              'retained_contingency_microusd':launch['budget']['contingency_microusd']}
    return snapshot,launch['providers']


def claim_path(parent):
    parent=Path(parent).resolve()
    return parent.parent/(parent.name+'.scoped-study-claim.json')


def planned_calls(cases,specs):
    calls=[]
    for split in ('development','evaluation'):
        for index,case in enumerate(c for c in cases if c['oracle']['split']==split):
            arms=('v2','v3') if index%2==0 else ('v3','v2')
            slots=specs if index%2==0 else list(reversed(specs))
            for arm in arms:
                prompt=build_prompt(case['item'],arm)
                for spec in slots:
                    calls.append({'id':f'{case["id"]}:{arm}:{spec["id"]}',
                        'slot':spec['id'],'phase':split,
                        'input_bound':len(prompt.encode())+64,'output_bound':OUTPUT_LIMIT,
                        'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest()})
    return calls


def create_study(parent,seeds,output,*,approval=False):
    if approval is not True:raise ValueError('explicit auxiliary study approval required')
    cases=build_cases(seeds)
    counts=Counter(s['split'] for s in seeds)
    if counts!={'development':2,'evaluation':4}:
        raise ValueError('freeze two development and four evaluation sources')
    if any(len({s['project_id'] for s in seeds if s['split']==split})!=2 for split in counts):
        raise ValueError('both source projects must occur in each split')
    output=Path(output).resolve()
    with parent_lock(parent):
        if claim_path(parent).exists():raise FileExistsError('parent already has an auxiliary study claim')
        snapshot,specs=parent_snapshot(parent)
        calls=planned_calls(cases,specs)
        prices={s['id']:parse_provider_slot(s).pricing for s in specs}
        auxiliary=envelope(calls,prices)['reserved_microusd']
        combined=(snapshot['spent_microusd']+snapshot['remaining_direct_microusd']
                  +snapshot['retained_contingency_microusd']+auxiliary+EARLIER_UNRESOLVED)
        if auxiliary>AUXILIARY_CAP or combined>CAP:
            raise ValueError('auxiliary or shared pilot envelope exceeds authorization')
        manifest={'schema_version':'scoped-judge-study/v1','claim_level':'auxiliary_development',
            'main_pilot_released':False,'parent':snapshot,'providers':specs,'seeds':seeds,
            'cases':cases,'calls':calls,'source_sha256':source_hashes(),'environment':environment(),
            'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'budget':{'auxiliary_cap_microusd':AUXILIARY_CAP,
                      'auxiliary_reserved_microusd':auxiliary,'combined_reserved_microusd':combined,
                      'shared_cap_microusd':CAP,'earlier_unresolved_retained_microusd':EARLIER_UNRESOLVED},
            'limitations':['AI-assisted source construction, not human truth',
                'bundled prompt/scope/inventory intervention; no single-component causal attribution',
                'evaluation locators may have appeared in screening/background; not pristine held-out data',
                'requested/returned model IDs do not prove immutable vendor weights']}
        output=prepare_private_output(output)
        _write(output/'manifest.json',manifest)
        _write(output/'manifest-integrity.json',{'sha256':file_hash(output/'manifest.json')})
        with PilotLedger(output/'ledger.jsonl',calls,prices,approval=True):pass
        _write(claim_path(parent),{'directory':str(output),'manifest_sha256':file_hash(output/'manifest.json')})
    return manifest


def load_study(directory,*,check_runtime=True):
    directory=Path(directory).resolve()
    if (not (directory/'ledger.jsonl').is_file()
        or read(directory/'manifest-integrity.json')!={'sha256':file_hash(directory/'manifest.json')}):
        raise ValueError('missing ledger or changed manifest')
    manifest=read(directory/'manifest.json')
    if manifest.get('schema_version')!='scoped-judge-study/v1':raise ValueError('unknown study')
    snapshot,_=parent_snapshot(manifest['parent']['directory'])
    if snapshot!=manifest['parent']:raise ValueError('parent custody changed')
    if read(claim_path(snapshot['directory']))!={'directory':str(directory),
            'manifest_sha256':file_hash(directory/'manifest.json')}:
        raise ValueError('auxiliary claim mismatch')
    if check_runtime and (source_hashes()!=manifest['source_sha256']
        or json.loads(json.dumps(environment()))!=manifest['environment']):
        raise ValueError('runtime source or environment changed')
    return manifest


def _phase_scores(manifest,completed,phase):
    cases={c['id']:c for c in manifest['cases']}
    counts={}
    for call in (c for c in manifest['calls'] if c['phase']==phase):
        case_id,arm,slot=call['id'].split(':',2)
        case=cases[case_id]; operation=case['oracle']['operation']
        key=f'{slot}:{arm}'
        by_operation=counts.setdefault(key,{op:dict(planned=0,completed=0,valid=0,
            invalid=0,correct=0,missing=0,exact_obligations=0) for op in OPERATIONS})
        count=by_operation[operation]; count['planned']+=1
        if call['id'] not in completed:
            count['missing']+=1;continue
        count['completed']+=1
        try:result=parse_response(completed[call['id']]['response'],case['item'],arm)
        except (ValueError,TypeError):count['invalid']+=1;continue
        count['valid']+=1
        count['correct']+=int(result['status']==case['oracle']['status'])
        count['exact_obligations']+=int(result['checks']==case['oracle']['checks'])
    passed=True
    for key,ops in counts.items():
        if not key.endswith(':v3'):continue
        planned=sum(c['planned'] for c in ops.values())
        passed &= (sum(c['valid'] for c in ops.values())==planned
                   and sum(c['correct'] for c in ops.values())*6>=planned*5
                   and all(ops[op]['correct']==ops[op]['planned'] for op in
                           ('long_omission','partial_missing','partial_complete','partial_contradiction')))
    return {'decision':'pass_auxiliary_only' if passed else 'pause','counts':counts}


def report(directory):
    manifest=load_study(directory,check_runtime=False)
    prices={s['id']:parse_provider_slot(s).pricing for s in manifest['providers']}
    ledger,completed=inspect_ledger(Path(directory)/'ledger.jsonl',manifest['calls'],prices)
    return {'schema_version':'scoped-judge-study-report/v1','main_pilot_released':False,
        'ledger':ledger,'budget':manifest['budget'],
        'phases':{phase:_phase_scores(manifest,completed,phase) for phase in ('development','evaluation')},
        'limitations':manifest['limitations']}


def run_phase(directory,phase,*,provider_factory=None,environ=None,progress=None):
    if phase not in {'development','evaluation'}:raise ValueError('unknown auxiliary phase')
    directory=Path(directory).resolve()
    if read(directory/'manifest-integrity.json')!={'sha256':file_hash(directory/'manifest.json')}:
        raise ValueError('changed manifest')
    initial=read(directory/'manifest.json')
    with parent_lock(initial['parent']['directory']):
        manifest=load_study(directory)
        slots={s['id']:parse_provider_slot(s) for s in manifest['providers']}
        prices={k:s.pricing for k,s in slots.items()}
        with PilotLedger(directory/'ledger.jsonl',manifest['calls'],prices,approval=True) as ledger:
            if phase=='evaluation' and _phase_scores(manifest,ledger.completed,'development')['decision']!='pass_auxiliary_only':
                raise ValueError('development gate has not passed')
            cases={c['id']:c for c in manifest['cases']}
            providers={}
            for call in (c for c in manifest['calls'] if c['phase']==phase):
                if call['id'] in ledger.completed:continue
                case_id,arm,slot_id=call['id'].split(':',2)
                if slot_id not in providers:
                    providers[slot_id]=(provider_factory or _provider)(slots[slot_id],
                        dict(os.environ if environ is None else environ))
                prompt=build_prompt(cases[case_id]['item'],arm)
                ledger.complete(call['id'],providers[slot_id],
                                ProviderRequest(prompt,{},'opaque','test_gen',OUTPUT_LIMIT))
                if progress:progress({'phase':phase,'completed':len(ledger.completed),
                                      'spent_microusd':ledger.spent})
        result=report(directory)
        if not (directory/f'{phase}-report.json').exists():
            _write(directory/f'{phase}-report.json',result)
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=('prepare','development','evaluation','report'))
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--parent',type=Path)
    parser.add_argument('--seeds',type=Path)
    parser.add_argument('--env-file',type=Path)
    parser.add_argument('--approve',action='store_true')
    args=parser.parse_args()
    if args.phase=='prepare':
        result=create_study(args.parent,read(args.seeds),args.directory,approval=args.approve)
        print(json.dumps({'prepared':True,'calls':len(result['calls']),'budget':result['budget']}))
    elif args.phase=='report':print(json.dumps(report(args.directory),indent=2))
    else:
        if args.env_file:load_private_env(args.env_file)
        result=run_phase(args.directory,args.phase,progress=lambda p:print(json.dumps(p),flush=True))
        print(json.dumps(result,indent=2))


if __name__=='__main__':main()
