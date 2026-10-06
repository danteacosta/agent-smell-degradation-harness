"""User-authorized continuation of unattempted slots under amended quota policy."""
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
from agents.claude_cli import ClaudeCLIProvider
from agents.providers import ProviderRequest
ma=original.ma


def require_amended_capacity(quota:dict,*,now:float|None=None):
    """Allow five-hour consumption; preserve reserve for every other window."""
    now=time.time() if now is None else now
    for key,window in quota.items():
        reserve=0 if key=='five_hour' else 30
        if window['resets_at']<=now or window['remaining_percent']<=reserve+1e-9:
            raise RuntimeError('amended quota limit reached or window expired')


def remaining_schedule(schedule:list,attempted:set):
    """Exclude every attempted slot, never classify a failed attempt as pending."""
    if not attempted<={tuple(slot) for slot in schedule}:raise ValueError('unexpected attempted slot')
    return [slot for slot in schedule if tuple(slot) not in attempted]


def prepare(out:Path,parent:Path):
    manifest=original.verify(parent)
    stop=json.loads((parent/'stopped.json').read_text())
    if stop['reason']!='quota reserve reached or window expired':raise RuntimeError('only quota stop permits continuation')
    if (parent/'generation-completed.json').exists():raise RuntimeError('original already complete')
    if out.exists():raise FileExistsError('fresh continuation required')
    progress=sorted((parent/'progress').glob('*.json'))
    if not progress or time.time()-progress[-1].stat().st_mtime>900:raise RuntimeError('quota observation stale')
    quota=json.loads(progress[-1].read_text())['quota']
    require_amended_capacity(quota)
    attempted=set()
    for path in parent.glob('*/calls/*/attempt.json'):
        result=json.loads((path.parent/'result.json').read_text())
        if result['status'] not in {'suite_ready','suite_invalid'}:raise RuntimeError('ambiguous/failed prior call: no continuation')
        if result['status']=='suite_ready' and ma.ta.sha256_file(path.parent/'suite.cjs')!=result['suite_sha256']:raise RuntimeError('prior suite drift')
        attempted.add((path.parents[2].name,path.parent.name))
    remaining=remaining_schedule(manifest['schedule'],attempted)
    parent_inventory=ma.ta.inventory(parent)
    shutil.copytree(parent,out)
    out.chmod(0o700)
    (out/'stopped.json').rename(out/'parent-stopped.json')
    ma.ta.put(out/'continuation-manifest.json',{'schema':'claude-quota-amendment/v1','remaining_schedule':remaining,
        'parent_inventory':parent_inventory,'parent_attempted':len(attempted),'quota':quota,'quota_observed_at':progress[-1].stat().st_mtime,
        'five_hour_reserve':0,'other_windows_reserve':30,'script_sha256':ma.ta.sha256_file(Path(__file__)),
        'user_authorization':'06/10/2026: pode zerar a de 5 horas','confirmatory_eligible':False})
    ma.ta.put(out/'continuation-receipt.json',{'manifest_sha256':ma.ta.sha256_file(out/'continuation-manifest.json')})
    return {'imported_attempts':len(attempted),'remaining':len(remaining),'quota':quota}


def verify(out:Path):
    manifest=original.verify(out)
    amendment=json.loads((out/'continuation-manifest.json').read_text())
    if ma.ta.sha256_file(out/'continuation-manifest.json')!=json.loads((out/'continuation-receipt.json').read_text())['manifest_sha256'] or amendment['script_sha256']!=ma.ta.sha256_file(Path(__file__)):
        raise RuntimeError('amendment drift')
    for name,digest in amendment['parent_inventory'].items():
        path=out/('parent-stopped.json' if name=='stopped.json' else name)
        if ma.ta.sha256_file(path)!=digest:raise RuntimeError('imported evidence drift')
    return manifest,amendment


def generate(out:Path):
    manifest,amendment=verify(out)
    if time.time()-amendment['quota_observed_at']>900:raise RuntimeError('quota observation stale')
    ma.ta.put(out/'continuation-started.json',{'at':time.time()})
    quota=amendment['quota']
    completed=amendment['parent_attempted']
    try:
        for model,cid in amendment['remaining_schedule']:
            require_amended_capacity(quota)
            if ma.ta.sha256_file(Path(manifest['executable']))!=manifest['executable_sha256']:raise RuntimeError('CLI drift')
            directory=out/model/'calls'/cid
            ma.ta.put(directory/'attempt.json',{'call_id':cid,'model':model,'at':time.time(),'policy':'five_hour_zero_weekly_thirty'})
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
            ma.ta.put(out/'continuation-progress'/f'{completed:03}.json',{'completed':completed,'planned':300,'quota':quota})
            print(json.dumps({'completed':completed,'planned':300,'quota':quota}),flush=True)
        for model in original.MODELS:
            results=[json.loads(p.read_text())['status'] for p in (out/model/'calls').glob('*/result.json')]
            ma.ta.put(out/model/'generation.json',dict(Counter(results)))
        ma.ta.put(out/'generation-completed.json',{'attempted':completed})
    except Exception as error:
        ma.ta.put(out/'continuation-stopped.json',{'reason':str(error)[:250],'attempted':len(list(out.glob('*/calls/*/attempt.json'))),'completed':completed,'planned':300,'quota':quota})
        raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('prepare','generate','execute'))
    p.add_argument('--out',type=Path,required=True);p.add_argument('--parent',type=Path)
    args=p.parse_args()
    if args.mode=='prepare':print(json.dumps(prepare(args.out,args.parent)))
    elif args.mode=='generate':generate(args.out)
    else:
        verify(args.out)
        original.execute(args.out)


if __name__=='__main__':main()
