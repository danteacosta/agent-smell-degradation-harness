"""Quota-warning compatible, journaled continuation; never repeat attempted slots."""
from __future__ import annotations
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts import claude_parser_continuation as previous
from scripts import claude_shared_omission as original
from scripts.claude_quota_amendment import require_amended_capacity,remaining_schedule
from agents.claude_cli_v2 import ClaudeCLIProvider
from agents.providers import ProviderRequest
ma=original.ma


def read_quota(raw:str,*,allow_blocked:bool=False):
    """Accept warnings; blocked status is readable only to record a future reset."""
    try:
        events=[json.loads(line) for line in raw.splitlines() if line.strip()]
        info=[e['rate_limit_info'] for e in events if e.get('type')=='rate_limit_event'][-1]
        allowed={'allowed','allowed_warning'}|({'rejected'} if allow_blocked else set())
        if info.get('status') not in allowed:raise ValueError('unrecognized status')
        info={**info,'status':'allowed'}
        return original.quota_snapshot(json.dumps({'type':'rate_limit_event','rate_limit_info':info}))
    except (ValueError,KeyError,IndexError,TypeError):raise RuntimeError('unavailable subscription quota') from None


def pending_slots(schedule:list,attempted:set):
    return remaining_schedule(schedule,attempted)


def attempts(out:Path):
    return {(p.parents[2].name,p.parent.name) for p in out.glob('*/calls/*/attempt.json')}


def bindings():
    paths=[Path(__file__),ROOT/'agents/claude_cli_v2.py',Path(previous.__file__),ROOT/'scripts/claude_quota_amendment.py']
    return {str(p.relative_to(ROOT)):ma.ta.sha256_file(p) for p in paths}


def prepare(out:Path,parent:Path):
    manifest,_=previous.verify(parent)
    stop=json.loads((parent/'parser-continuation-stopped.json').read_text())
    if stop['reason']!='missing or invalid Claude subscription quota':raise RuntimeError('wrong prior stop')
    if out.exists():raise FileExistsError('fresh packet required')
    # All prior outcomes, including the known parser refusal, are imported unchanged.
    for model,cid in attempts(parent):
        directory=parent/model/'calls'/cid
        result=json.loads((directory/'result.json').read_text())
        if result['status']=='suite_ready' and ma.ta.sha256_file(directory/'suite.cjs')!=result['suite_sha256']:raise RuntimeError('prior suite drift')
    inventory=ma.ta.inventory(parent)
    shutil.copytree(parent,out);out.chmod(0o700)
    ma.ta.put(out/'quota-v3-manifest.json',{'schema':'claude-quota-warning/v3','code_sha256':bindings(),'parent_inventory':inventory,
        'imported_attempts':len(attempts(parent)),'schedule':manifest['schedule'],
        'authorization':'06/10/2026: continuar até limite de cinco horas e agendar retorno após reset',
        'five_hour_reserve':0,'other_windows_reserve':30,'confirmatory_eligible':False})
    ma.ta.put(out/'quota-v3-receipt.json',{'manifest_sha256':ma.ta.sha256_file(out/'quota-v3-manifest.json')})
    return {'imported_attempts':len(attempts(out)),'pending':len(pending_slots(manifest['schedule'],attempts(out)))}


def verify(out:Path):
    manifest,_=previous.verify(out)
    amendment=json.loads((out/'quota-v3-manifest.json').read_text())
    if amendment['code_sha256']!=bindings() or ma.ta.sha256_file(out/'quota-v3-manifest.json')!=json.loads((out/'quota-v3-receipt.json').read_text())['manifest_sha256']:raise RuntimeError('code or manifest drift')
    for name,digest in amendment['parent_inventory'].items():
        if ma.ta.sha256_file(out/name)!=digest:raise RuntimeError('imported evidence drift')
    for folder in sorted((out/'quota-segments').glob('*')):
        receipt=folder/'receipt.json'
        if receipt.exists():
            for name,digest in json.loads(receipt.read_text())['files'].items():
                if ma.ta.sha256_file(out/name)!=digest:raise RuntimeError('segment evidence drift')
    return manifest,amendment


def generate(out:Path,baseline:Path):
    manifest,amendment=verify(out)
    segments=sorted((out/'quota-segments').glob('*'))
    if segments:
        stopped=json.loads((segments[-1]/'stopped.json').read_text())
        if stopped.get('resume_after_reset') is not True or time.time()<stopped['reset_at']+60:raise RuntimeError('not authorized to continue before reset')
    if time.time()-baseline.stat().st_mtime>900:raise RuntimeError('stale quota baseline')
    quota=read_quota(baseline.read_text());require_amended_capacity(quota)
    lock=out/'quota-active.lock'
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
    segment=out/'quota-segments'/f'{len(segments):03}'
    segment.mkdir(mode=0o700,parents=True,exist_ok=False)
    ma.ta.put(segment/'started.json',{'at':time.time(),'baseline_sha256':ma.ta.sha256_file(baseline),'quota':quota})
    touched=[];exhausted=False
    try:
        for model,cid in pending_slots(amendment['schedule'],attempts(out)):
            require_amended_capacity(quota)
            if ma.ta.sha256_file(Path(manifest['executable']))!=manifest['executable_sha256']:raise RuntimeError('CLI drift')
            directory=out/model/'calls'/cid
            ma.ta.put(directory/'attempt.json',{'call_id':cid,'model':model,'at':time.time(),'segment':segment.name})
            touched.append(directory)
            provider=ClaudeCLIProvider(executable=manifest['executable'],model=model,timeout_seconds=300,evidence_directory=directory/'capture')
            try:raw=provider.complete(ProviderRequest((out/model/'frozen/prompts'/f'{cid}.txt').read_text(),{},'opaque','code'))
            except Exception as error:
                ma.ta.put(directory/'result.json',{'status':'generation_failed','error_type':type(error).__name__})
                capture=directory/'capture/stdout.jsonl'
                if capture.exists():
                    try:
                        quota=read_quota(capture.read_text(),allow_blocked=True)
                        exhausted=quota['five_hour']['remaining_percent']<=1e-9
                    except RuntimeError:pass
                raise
            ma.ta.put(directory/'response.txt',raw)
            try:suite=ma.ta.extract_suite(raw)
            except ValueError as error:ma.ta.put(directory/'result.json',{'status':'suite_invalid','reason':str(error)})
            else:
                ma.ta.put(directory/'suite.cjs',suite)
                ma.ta.put(directory/'result.json',{'status':'suite_ready','suite_sha256':ma.ta.sha256_bytes(suite.encode())})
            quota=read_quota((directory/'capture/stdout.jsonl').read_text())
            ma.ta.put(segment/'progress'/f'{len(attempts(out)):03}.json',{'attempted':len(attempts(out)),'planned':300,'quota':quota})
            print(json.dumps({'attempted':len(attempts(out)),'planned':300,'quota':quota}),flush=True)
        for model in original.MODELS:
            statuses=[json.loads(p.read_text())['status'] for p in (out/model/'calls').glob('*/result.json')]
            ma.ta.put(out/model/'generation.json',dict(Counter(statuses)))
        ma.ta.put(out/'generation-completed.json',{'attempted':len(attempts(out))})
        ma.ta.put(segment/'completed.json',{'at':time.time()})
    except Exception as error:
        exhausted=exhausted or quota['five_hour']['remaining_percent']<=1e-9
        other_capacity=all(w['remaining_percent']>30 for k,w in quota.items() if k!='five_hour')
        ma.ta.put(segment/'stopped.json',{'reason':str(error)[:250],'attempted':len(attempts(out)),'planned':300,'quota':quota,
            'resume_after_reset':exhausted and other_capacity,'reset_at':quota['five_hour']['resets_at'],'at':time.time()})
        raise
    finally:
        files={str(p.relative_to(out)):ma.ta.sha256_file(p) for directory in touched for p in directory.rglob('*') if p.is_file()}
        files.update({str(p.relative_to(out)):ma.ta.sha256_file(p) for p in segment.rglob('*') if p.is_file()})
        ma.ta.put(segment/'receipt.json',{'files':files})
        lock.unlink()


def execute(out:Path):
    verify(out);original.execute(out)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('prepare','generate','execute'))
    p.add_argument('--out',type=Path,required=True);p.add_argument('--parent',type=Path);p.add_argument('--baseline',type=Path)
    args=p.parse_args()
    if args.mode=='prepare':print(json.dumps(prepare(args.out,args.parent)))
    elif args.mode=='generate':generate(args.out,args.baseline)
    else:execute(args.out)


if __name__=='__main__':main()
