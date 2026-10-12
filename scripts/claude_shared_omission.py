"""Separate Claude replication of frozen shared-omission prompts, with quota stop."""
from __future__ import annotations
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import shutil
import sys
import time
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from agents.claude_cli import ClaudeCLIProvider
from agents.providers import ProviderRequest
from scripts import shared_omission_e2e as so
from scripts import mutation_adequacy as ma
MODELS = ('claude-sonnet-4-6','claude-opus-4-6')
STOP_REMAINING = 30


def quota_snapshot(raw: str) -> dict:
    """Read the latest observed subscription windows, never infer from tokens."""
    try:
        events=[json.loads(line) for line in raw.splitlines() if line.strip()]
        info=[e['rate_limit_info'] for e in events if e.get('type')=='rate_limit_event'][-1]
        if info.get('status')!='allowed' or info.get('isUsingOverage') is not False:
            raise ValueError('unavailable or extra usage')
        windows=info['unifiedWindows']
        if not isinstance(windows,dict) or not {'five_hour','seven_day'}<=set(windows):
            raise ValueError('required windows missing')
        result={}
        for key in windows:
            used,reset=windows[key]['utilization'],windows[key]['resetsAt']
            if type(used) not in (int,float) or not math.isfinite(used) or not 0<=used<=1 or type(reset) not in (int,float) or not math.isfinite(reset):
                raise ValueError('invalid window')
            result[key]={'remaining_percent':100*(1-used),'resets_at':reset}
        return result
    except (ValueError,KeyError,IndexError,TypeError,AttributeError):
        raise RuntimeError('missing or invalid Claude subscription quota') from None


def require_capacity(quota: dict, *, now: float | None = None) -> dict:
    """Refuse a new attempt at or below the reserve, or after window expiry."""
    now=time.time() if now is None else now
    if any(w['resets_at']<=now or w['remaining_percent']<=STOP_REMAINING+1e-9 for w in quota.values()):
        raise RuntimeError('quota reserve reached or window expired')
    return quota


def interleaved_schedule(schedules: dict) -> list[tuple[str,str]]:
    """Alternate model cohorts while preserving the original seeded slot order."""
    lengths={len(v) for v in schedules.values()}
    if len(lengths)!=1:raise ValueError('cohorts must have equal schedules')
    return [(model,call['call_id']) for i in range(next(iter(lengths))) for model,calls in schedules.items() for call in [calls[i]]]


def bindings():
    return {str(p.relative_to(ROOT)):ma.ta.sha256_file(p) for p in (Path(__file__),ROOT/'agents/claude_cli.py',Path(so.__file__),Path(ma.__file__),Path(ma.ta.__file__))}


def prepare(out:Path,parent:Path,baseline:Path,executable:Path):
    original=so.verify(parent)
    if out.exists():raise FileExistsError('new packet only')
    if time.time()-baseline.stat().st_mtime>900:raise RuntimeError('quota baseline stale')
    quota=require_capacity(quota_snapshot(baseline.read_text()))
    controls=json.loads((out.parent/'controls/controls.json').read_text())
    so.validate_controls(controls)
    out.mkdir(mode=0o700,parents=True)
    schedules={}
    for model in MODELS:
        target=out/model
        shutil.copytree(parent/'frozen',target/'frozen',ignore=shutil.ignore_patterns('receipt.json'))
        manifest={**original,'model':model,'executable':str(executable.resolve()),'provider':'claude_cli',
                  'replication_role':'exploratory_second_provider','parent_receipt_sha256':ma.ta.sha256_file(parent/'frozen/receipt.json')}
        (target/'frozen/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        (target/'frozen/controls.json').write_text(json.dumps(controls,indent=2)+'\n')
        ma.ta.put(target/'frozen/receipt.json',{'files':ma.ta.inventory(target/'frozen')})
        schedules[model]=manifest['schedule']
    ma.ta.put(out/'replication-manifest.json',{'schema':'claude-shared-omission/v1','code_sha256':bindings(),
        'executable':str(executable.resolve()),'executable_sha256':ma.ta.sha256_file(executable.resolve()),
        'schedule':interleaved_schedule(schedules),'baseline_quota':quota,'baseline_observed_at':baseline.stat().st_mtime,
        'quota_stop_remaining_percent':STOP_REMAINING,'confirmatory_eligible':False,'retry':'none'})
    ma.ta.put(out/'replication-receipt.json',{'manifest_sha256':ma.ta.sha256_file(out/'replication-manifest.json')})
    return {'models':len(MODELS),'calls':sum(map(len,schedules.values())),'quota':quota}


def verify(out:Path):
    manifest=json.loads((out/'replication-manifest.json').read_text())
    if ma.ta.sha256_file(out/'replication-manifest.json')!=json.loads((out/'replication-receipt.json').read_text())['manifest_sha256'] or manifest['code_sha256']!=bindings() or ma.ta.sha256_file(Path(manifest['executable']))!=manifest['executable_sha256']:
        raise RuntimeError('replication drift')
    for model in MODELS:so.verify(out/model)
    return manifest


def generate(out:Path):
    manifest=verify(out)
    if (out/'started.json').exists():raise FileExistsError('no restart or retry')
    if time.time()-manifest['baseline_observed_at']>900:raise RuntimeError('quota baseline stale')
    quota=manifest['baseline_quota']
    ma.ta.put(out/'started.json',{'at':time.time()})
    counts=Counter()
    try:
        for index,(model,cid) in enumerate(manifest['schedule']):
            require_capacity(quota)
            if ma.ta.sha256_file(Path(manifest['executable']))!=manifest['executable_sha256']:raise RuntimeError('CLI drift')
            directory=out/model/'calls'/cid
            ma.ta.put(directory/'attempt.json',{'call_id':cid,'model':model,'at':time.time()})
            p=ClaudeCLIProvider(executable=manifest['executable'],model=model,timeout_seconds=300,evidence_directory=directory/'capture')
            try: raw=p.complete(ProviderRequest((out/model/'frozen/prompts'/f'{cid}.txt').read_text(),{},'opaque','code'))
            except Exception as error:
                ma.ta.put(directory/'result.json',{'status':'generation_failed','error_type':type(error).__name__})
                counts['generation_failed']+=1
                raise
            ma.ta.put(directory/'response.txt',raw)
            try:suite=ma.ta.extract_suite(raw)
            except ValueError as error:
                ma.ta.put(directory/'result.json',{'status':'suite_invalid','reason':str(error)})
                counts['suite_invalid']+=1
            else:
                ma.ta.put(directory/'suite.cjs',suite)
                ma.ta.put(directory/'result.json',{'status':'suite_ready','suite_sha256':ma.ta.sha256_bytes(suite.encode())})
                counts['suite_ready']+=1
            quota=quota_snapshot((directory/'capture/stdout.jsonl').read_text())
            ma.ta.put(out/'progress'/f'{index:03}.json',{'attempted':sum(counts.values()),'planned':len(manifest['schedule']),'quota':quota,'counts':dict(counts)})
            print(json.dumps({'attempted':sum(counts.values()),'planned':len(manifest['schedule']),'quota':quota}),flush=True)
        for model in MODELS:
            results=[json.loads(p.read_text())['status'] for p in (out/model/'calls').glob('*/result.json')]
            ma.ta.put(out/model/'generation.json',dict(Counter(results)))
        ma.ta.put(out/'generation-completed.json',{'attempted':sum(counts.values())})
    except Exception as error:
        attempted=sum(1 for _ in out.glob('*/calls/*/attempt.json'))
        ma.ta.put(out/'stopped.json',{'reason':str(error)[:250],'error_type':type(error).__name__,'attempted':attempted,'planned':len(manifest['schedule']),'quota':quota})
        raise


def execute(out:Path):
    verify(out)
    if not (out/'generation-completed.json').is_file():raise RuntimeError('generation incomplete; inspect stopped.json')
    for model in MODELS:
        analysis=ma.execute(out/model)
        ma.ta.put(out/f'{model}-summary.json',{k:v for k,v in analysis.items() if k!='suites'})
    ma.ta.put(out/'completed.json',{'models':list(MODELS),'at':time.time()})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('prepare','generate','execute'))
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--parent',type=Path)
    parser.add_argument('--baseline',type=Path)
    parser.add_argument('--executable',type=Path,default=Path.home()/'.local/bin/claude')
    args=parser.parse_args()
    if args.mode=='prepare': print(json.dumps(prepare(args.out,args.parent,args.baseline,args.executable)))
    elif args.mode=='generate':generate(args.out)
    else:execute(args.out)


if __name__=='__main__':main()
