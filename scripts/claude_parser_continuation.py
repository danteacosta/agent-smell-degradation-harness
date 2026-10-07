"""Versioned continuation after telemetry parser failure; never retry an attempted slot."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts import claude_shared_omission as original
from agents.claude_cli_v2 import ClaudeCLIProvider, validate_stream
from scripts import claude_quota_amendment as previous
from agents.providers import ProviderRequest
ma=original.ma


from scripts.claude_quota_amendment import require_amended_capacity, remaining_schedule


def prepare(out:Path,parent:Path,baseline:Path):
    manifest,_=previous.verify(parent)
    stop=json.loads((parent/'continuation-stopped.json').read_text())
    if stop['reason']!='Claude stream rejected: unexpected system activity':raise RuntimeError('wrong prior stop')
    if out.exists():raise FileExistsError('fresh continuation required')
    if time.time()-baseline.stat().st_mtime>900:raise RuntimeError('quota observation stale')
    quota=original.quota_snapshot(baseline.read_text());require_amended_capacity(quota)
    attempted=set();failed=[]
    for path in parent.glob('*/calls/*/attempt.json'):
        result=json.loads((path.parent/'result.json').read_text())
        if result['status']=='generation_failed':
            if result.get('error_type')!='RuntimeError':raise RuntimeError('other failure not authorized')
            validate_stream((path.parent/'capture/stdout.jsonl').read_text(),path.parents[2].name)
            failed.append((path.parents[2].name,path.parent.name))
        elif result['status'] not in {'suite_ready','suite_invalid'}:raise RuntimeError('unrecognized prior outcome')
        if result['status']=='suite_ready' and ma.ta.sha256_file(path.parent/'suite.cjs')!=result['suite_sha256']:raise RuntimeError('prior suite drift')
        attempted.add((path.parents[2].name,path.parent.name))
    if len(failed)!=1:raise RuntimeError('expected exactly one preserved parser refusal')
    remaining=remaining_schedule(manifest['schedule'],attempted)
    parent_inventory=ma.ta.inventory(parent)
    shutil.copytree(parent,out);out.chmod(0o700)
    ma.ta.put(out/'parser-continuation-manifest.json',{'schema':'claude-parser-continuation/v1','remaining_schedule':remaining,
        'parent_inventory':parent_inventory,'parent_attempted':len(attempted),'preserved_failures':failed,
        'quota':quota,'quota_observed_at':baseline.stat().st_mtime,'five_hour_reserve':0,'other_windows_reserve':30,
        'script_sha256':ma.ta.sha256_file(Path(__file__)),
        'adapter_sha256':ma.ta.sha256_file(ROOT/'agents/claude_cli_v2.py'),
        'user_authorization':'06/10/2026: certo, ajuste e continue','confirmatory_eligible':False})
    ma.ta.put(out/'parser-continuation-receipt.json',{'manifest_sha256':ma.ta.sha256_file(out/'parser-continuation-manifest.json')})
    return {'imported_attempts':len(attempted),'preserved_failed_attempts':len(failed),'remaining':len(remaining),'quota':quota}


def verify(out:Path):
    manifest,_=previous.verify(out)
    amendment=json.loads((out/'parser-continuation-manifest.json').read_text())
    if ma.ta.sha256_file(out/'parser-continuation-manifest.json')!=json.loads((out/'parser-continuation-receipt.json').read_text())['manifest_sha256'] or amendment['script_sha256']!=ma.ta.sha256_file(Path(__file__)) or amendment['adapter_sha256']!=ma.ta.sha256_file(ROOT/'agents/claude_cli_v2.py'):
        raise RuntimeError('amendment drift')
    for name,digest in amendment['parent_inventory'].items():
        path=out/name
        if ma.ta.sha256_file(path)!=digest:raise RuntimeError('imported evidence drift')
    return manifest,amendment


def generate(out:Path):
    manifest,amendment=verify(out)
    if time.time()-amendment['quota_observed_at']>900:raise RuntimeError('quota observation stale')
    ma.ta.put(out/'parser-continuation-started.json',{'at':time.time()})
    quota=amendment['quota']
    completed=amendment['parent_attempted']
    try:
        for model,cid in amendment['remaining_schedule']:
            require_amended_capacity(quota)
            if ma.ta.sha256_file(Path(manifest['executable']))!=manifest['executable_sha256']:raise RuntimeError('CLI drift')
            directory=out/model/'calls'/cid
            ma.ta.put(directory/'attempt.json',{'call_id':cid,'model':model,'at':time.time(),'policy':'five_hour_zero_weekly_thirty_parser_v2'})
            provider=ClaudeCLIProvider(executable=manifest['executable'],model=model,timeout_seconds=300,evidence_directory=directory/'capture')
            try:raw=provider.complete(ProviderRequest((out/model/'frozen/prompts'/f'{cid}.txt').read_text(),{},'opaque','code'))
            except Exception as error:
                ma.ta.put(directory/'result.json',{'status':'generation_failed','error_type':type(error).__name__})
                raise
            ma.ta.put(directory/'response.txt',raw)
            try:suite=ma.ta.extract_suite(raw)
            except ValueError as error:ma.ta.put(directory/'result.json',{'status':'suite_invalid','reason':str(error)})
            else:
                ma.ta.put(directory/'suite.cjs',suite)
                ma.ta.put(directory/'result.json',{'status':'suite_ready','suite_sha256':ma.ta.sha256_bytes(suite.encode())})
            completed+=1
            quota=original.quota_snapshot((directory/'capture/stdout.jsonl').read_text())
            ma.ta.put(out/'parser-continuation-progress'/f'{completed:03}.json',{'completed':completed,'planned':300,'quota':quota})
            print(json.dumps({'completed':completed,'planned':300,'quota':quota}),flush=True)
        for model in original.MODELS:
            results=[json.loads(p.read_text())['status'] for p in (out/model/'calls').glob('*/result.json')]
            ma.ta.put(out/model/'generation.json',dict(Counter(results)))
        ma.ta.put(out/'generation-completed.json',{'attempted':completed})
    except Exception as error:
        ma.ta.put(out/'parser-continuation-stopped.json',{'reason':str(error)[:250],'attempted':len(list(out.glob('*/calls/*/attempt.json'))),'completed':completed,'planned':300,'quota':quota})
        raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('prepare','generate','execute'))
    p.add_argument('--out',type=Path,required=True);p.add_argument('--parent',type=Path);p.add_argument('--baseline',type=Path)
    args=p.parse_args()
    if args.mode=='prepare':print(json.dumps(prepare(args.out,args.parent,args.baseline)))
    elif args.mode=='generate':generate(args.out)
    else:
        verify(args.out)
        original.execute(args.out)


if __name__=='__main__':main()
