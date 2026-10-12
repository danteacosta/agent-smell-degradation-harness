"""Separate, journaled Claude 5.5 replication; immutable earlier collectors."""
from __future__ import annotations
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from agents.claude_cli_v2 import ClaudeCLIProvider
from agents.providers import ProviderRequest
from scripts import shared_omission_e2e as so
from scripts import claude_shared_omission as original
from scripts.claude_quota_amendment import require_amended_capacity,remaining_schedule
from scripts.claude_quota_v3 import read_quota
ma=so.ma
MODELS=('claude-sonnet-5-5','claude-opus-5-5')


def bindings():
    paths=[Path(__file__),ROOT/'agents/claude_cli_v2.py',ROOT/'scripts/claude_quota_v3.py',
           ROOT/'scripts/claude_quota_amendment.py',Path(original.__file__),Path(so.__file__),Path(ma.__file__),Path(ma.ta.__file__),ROOT/'agents/providers.py',ROOT/'docs/preregistration/2026-10-06-claude55-shared-omission.md']
    return {str(p.relative_to(ROOT)):ma.ta.sha256_file(p) for p in paths}


def attempts(out:Path):
    return {(p.parents[2].name,p.parent.name) for p in out.glob('*/calls/*/attempt.json')}


def baseline_quota(path:Path):
    if not 0<=time.time()-path.stat().st_mtime<=900:raise RuntimeError('stale quota qualification')
    quota=read_quota(path.read_text());require_amended_capacity(quota)
    return quota


def prepare(out:Path,parent:Path,baseline:Path,executable:Path):
    source=so.verify(parent)
    if out.exists():raise FileExistsError('fresh packet required')
    quota=baseline_quota(baseline)
    controls=json.loads((out.parent/'controls/controls.json').read_text());so.validate_controls(controls)
    out.mkdir(mode=0o700,parents=True)
    schedules={}
    for model in MODELS:
        dest=out/model
        shutil.copytree(parent/'frozen',dest/'frozen',ignore=shutil.ignore_patterns('receipt.json','manifest.json','controls.json'))
        manifest={**source,'model':model,'provider':'claude_cli','executable':str(executable.resolve()),
                  'replication_role':'exploratory_claude55','parent_receipt_sha256':ma.ta.sha256_file(parent/'frozen/receipt.json')}
        ma.ta.put(dest/'frozen/manifest.json',manifest);ma.ta.put(dest/'frozen/controls.json',controls)
        ma.ta.put(dest/'frozen/receipt.json',{'files':ma.ta.inventory(dest/'frozen')})
        schedules[model]=manifest['schedule']
    manifest={'schema':'claude55-shared-omission/v1','models':MODELS,'code_sha256':bindings(),
              'executable':str(executable.resolve()),'executable_sha256':ma.ta.sha256_file(executable.resolve()),
              'schedule':original.interleaved_schedule(schedules),'baseline_quota':quota,
              'five_hour_reserve':0,'other_windows_reserve':30,'retry':'none','confirmatory_eligible':False}
    ma.ta.put(out/'replication-manifest.json',manifest)
    ma.ta.put(out/'replication-receipt.json',{'manifest_sha256':ma.ta.sha256_file(out/'replication-manifest.json')})
    return {'models':list(MODELS),'planned':len(manifest['schedule'])}


def verify(out:Path):
    if (out/'quota-active.lock').exists():raise RuntimeError('generation is active or lock needs investigation')
    manifest=json.loads((out/'replication-manifest.json').read_text())
    if (manifest['code_sha256']!=bindings() or tuple(manifest['models'])!=MODELS or
        ma.ta.sha256_file(out/'replication-manifest.json')!=json.loads((out/'replication-receipt.json').read_text())['manifest_sha256'] or
        ma.ta.sha256_file(Path(manifest['executable']))!=manifest['executable_sha256']):raise RuntimeError('replication drift')
    for model in MODELS:so.verify(out/model)
    remaining_schedule(manifest['schedule'],attempts(out))
    covered=set()
    for segment in sorted((out/'quota-segments').glob('*')):
        receipt=segment/'receipt.json'
        if not receipt.is_file():raise RuntimeError('missing segment receipt')
        files=json.loads(receipt.read_text())['files']
        for name,digest in files.items():
            if ma.ta.sha256_file(out/name)!=digest:raise RuntimeError('prior attempt or segment drift')
        expected={str(p.relative_to(out)) for p in segment.rglob('*') if p.is_file() and p!=receipt}
        if not expected<=set(files):raise RuntimeError('incomplete segment receipt')
        covered.update(files)
    call_files={str(p.relative_to(out)) for model in MODELS for p in (out/model/'calls').rglob('*') if p.is_file()}
    if not call_files<=covered:raise RuntimeError('attempt not covered by segment receipt')
    return manifest


def require_other_capacity(quota):
    for name,window in quota.items():
        reserve=0 if name=='five_hour' else 30
        if window['resets_at']<=time.time() or (name!='five_hour' and window['remaining_percent']<=reserve+1e-9):
            raise RuntimeError('non-five-hour reserve reached or quota expired')


def remote_quota_rejection(error,raw):
    if type(error) is not RuntimeError or str(error)!='Claude exited 1; no retry':return False
    events=[json.loads(line) for line in raw.splitlines() if line.strip()]
    info=[e['rate_limit_info'] for e in events if e.get('type')=='rate_limit_event'][-1]
    return info.get('status')=='rejected' and read_quota(raw,allow_blocked=True)['five_hour']['remaining_percent']<=1e-9


def generate(out:Path,baseline:Path):
    manifest=verify(out)
    if (out/'generation-completed.json').exists():raise FileExistsError('generation already complete')
    segments=sorted((out/'quota-segments').glob('*'))
    if segments:
        stop=json.loads((segments[-1]/'stopped.json').read_text())
        if stop.get('resume_after_reset') is not True or time.time()<stop['reset_at']+60:
            raise RuntimeError('no continuation before authorized reset+60')
    quota=baseline_quota(baseline)
    lock=out/'quota-active.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
    segment=out/'quota-segments'/f'{len(segments):03}';segment.mkdir(mode=0o700,parents=True)
    ma.ta.put(segment/'started.json',{'at':time.time(),'prior_attempted':len(attempts(out)),
        'baseline_sha256':ma.ta.sha256_file(baseline),'quota':quota})
    touched=[];observed_exhaustion=False;remote_exhaustion=False
    try:
        for model,cid in remaining_schedule(manifest['schedule'],attempts(out)):
            require_amended_capacity(quota)
            if ma.ta.sha256_file(Path(manifest['executable']))!=manifest['executable_sha256']:raise RuntimeError('CLI drift')
            directory=out/model/'calls'/cid
            if directory.exists():raise RuntimeError('existing call directory without matching attempt')
            ma.ta.put(directory/'attempt.json',{'model':model,'call_id':cid,'at':time.time(),'segment':segment.name})
            touched.append(directory)
            provider=ClaudeCLIProvider(executable=manifest['executable'],model=model,timeout_seconds=300,evidence_directory=directory/'capture')
            try:raw=provider.complete(ProviderRequest((out/model/'frozen/prompts'/f'{cid}.txt').read_text(),{},'opaque','code'))
            except Exception as error:
                ma.ta.put(directory/'result.json',{'status':'generation_failed','error_type':type(error).__name__})
                capture=directory/'capture/stdout.jsonl'
                if capture.exists():
                    try:
                        raw_capture=capture.read_text()
                        quota=read_quota(raw_capture,allow_blocked=True)
                        remote_exhaustion=remote_quota_rejection(error,raw_capture)
                    except (RuntimeError,ValueError,KeyError,IndexError):pass
                raise
            ma.ta.put(directory/'response.txt',raw)
            try:suite=ma.ta.extract_suite(raw)
            except ValueError as error:ma.ta.put(directory/'result.json',{'status':'suite_invalid','reason':str(error)})
            else:
                ma.ta.put(directory/'suite.cjs',suite)
                ma.ta.put(directory/'result.json',{'status':'suite_ready','suite_sha256':ma.ta.sha256_bytes(suite.encode())})
            quota=read_quota((directory/'capture/stdout.jsonl').read_text())
            observed_exhaustion=quota['five_hour']['remaining_percent']<=1e-9
            require_other_capacity(quota)
            progress={'attempted':len(attempts(out)),'planned':len(manifest['schedule']),'quota':quota}
            ma.ta.put(segment/'progress'/f'{progress["attempted"]:03}.json',progress)
            print(json.dumps(progress),flush=True)
        for model in MODELS:
            statuses=[json.loads(p.read_text())['status'] for p in (out/model/'calls').glob('*/result.json')]
            ma.ta.put(out/model/'generation.json',dict(Counter(statuses)))
        ma.ta.put(out/'generation-completed.json',{'at':time.time(),'attempted':len(attempts(out))})
        ma.ta.put(segment/'completed.json',{'at':time.time()})
    except Exception as error:
        other_capacity=all(w['remaining_percent']>30 and w['resets_at']>time.time() for k,w in quota.items() if k!='five_hour')
        ma.ta.put(segment/'stopped.json',{'at':time.time(),'reason':str(error)[:250],
            'attempted':len(attempts(out)),'planned':len(manifest['schedule']),'quota':quota,
            'resume_after_reset':other_capacity and (remote_exhaustion or (observed_exhaustion and type(error) is RuntimeError and str(error)=='amended quota limit reached or window expired')),'reset_at':quota['five_hour']['resets_at']})
        raise
    finally:
        files={str(p.relative_to(out)):ma.ta.sha256_file(p) for d in touched for p in d.rglob('*') if p.is_file()}
        files.update({str(p.relative_to(out)):ma.ta.sha256_file(p) for p in segment.rglob('*') if p.is_file()})
        ma.ta.put(segment/'receipt.json',{'files':files});lock.unlink()


def execute(out:Path):
    verify(out)
    if not (out/'generation-completed.json').exists():raise RuntimeError('generation incomplete')
    fd=os.open(out/'evaluation-started.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as f:json.dump({'at':time.time()},f)
    try:
        for model in MODELS:
            ma.execute(out/model)
            manifest=so.verify(out/model);results=json.loads((out/model/'results.json').read_text())
            ma.ta.put(out/model/'selected-mutant-analysis.json',so.analyse_selected(results['rows'],manifest))
        ma.ta.put(out/'completed.json',{'at':time.time(),'models':MODELS})
    except Exception as error:
        ma.ta.put(out/'evaluation-stopped.json',{'at':time.time(),'reason':str(error)[:250]});raise


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('prepare','generate','execute'))
    p.add_argument('--out',type=Path,required=True);p.add_argument('--parent',type=Path);p.add_argument('--baseline',type=Path)
    p.add_argument('--executable',type=Path,default=Path.home()/'.local/bin/claude');args=p.parse_args()
    if args.mode=='prepare':print(json.dumps(prepare(args.out,args.parent,args.baseline,args.executable)))
    elif args.mode=='generate':generate(args.out,args.baseline)
    else:execute(args.out)


if __name__=='__main__':main()
