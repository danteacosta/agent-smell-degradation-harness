#!/usr/bin/env python3
"""Verify a public memorization projection without private files or model calls."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re


def load(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inventory(root):
    files = {}
    for path in root.rglob('*'):
        require(not path.is_symlink(), 'symlink in public packet')
        if path.is_file() and path != root / 'receipt.json':
            files[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            require(path.is_dir() or path == root / 'receipt.json', 'nonregular evidence')
    return files


def judgment(raw):
    try:
        match = re.search(r'\{.*\}', raw, re.S)
        value = json.loads(match.group(0)).get('states_rule') if match else None
        return value if value in ('yes', 'no') else None
    except (ValueError, TypeError):
        return None


def verify(root):
    root = root.resolve(strict=True)
    require(not (root/'receipt.json').is_symlink(), 'receipt symlink')
    require(load(root/'receipt.json')['files'] == inventory(root), 'public receipt mismatch')
    manifest, results = load(root/'manifest.json'), load(root/'results.json')
    calls, audit = load(root/'calls.json'), load(root/'audit.json')
    accounting, custody = load(root/'accounting.json'), load(root/'custody.json')
    templates = load(root/'templates.json')
    require(manifest['schema_version']=='memorization-probe/v1' and results['schema_version']=='memorization-probe/v1-results' and results['status']=='complete', 'wrong schema/status')
    coders, judges = manifest['coders'], manifest['judges']
    require(coders and len(set(coders))==len(coders) and len(judges)==len(set(judges))==2 and not set(coders)&set(judges) and manifest['repetitions']==3 and manifest['retry_policy']=='no_retry_no_repair', 'invalid model/repetition design')
    require('executable' not in manifest, 'private executable published')
    rules = {r['candidate_id']:r for r in manifest['rules']}
    require(len(rules)==len(manifest['rules']), 'duplicate rules')
    controls = {c['id']:c for c in manifest['judge_controls']}
    require(len(controls)==len(manifest['judge_controls'])==4, 'four distinct controls required')
    ids=[*coders,*judges,*rules,*controls]
    require(all(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', s) for s in ids), 'unsafe identity')
    for rule in rules.values():
        require((root/f"frozen/probes/{rule['candidate_id']}.txt").read_text()==templates['PROBE_TEMPLATE'].format(project=rule['project'], question=rule['question']), 'probe prompt differs from template')
    for c in controls.values():
        require((root/f"frozen/judge-controls/{c['id']}.txt").read_text()==templates['JUDGE_TEMPLATE'].format(rule=c['rule'],answer=c['answer']), 'control prompt differs from template')
    by_slot={c['slot']:c for c in calls};require(len(by_slot)==len(calls), 'duplicate calls')
    seen_calls=set()

    def call(slot, model, kind, status, verdict=None):
        require(slot in by_slot and slot not in seen_calls, 'missing/repeated call slot')
        seen_calls.add(slot);c=by_slot[slot]
        require(c['model']==model and c['kind']==kind and c['status']==status, 'call identity/status mismatch')
        if status=='call_failed':
            require(c['raw_result']['status']=='call_failed' and set(c['raw_result'])=={'status','error_type'} and 'raw_response' not in c and 'answer_as_judged' not in c, 'failed call contains response')
        else:
            require(re.fullmatch(r'[0-9a-f]{64}',c['original_response_sha256']) and type(c['original_response_bytes']) is int and c['original_response_bytes']>=0 and type(c['original_response_characters']) is int and c['original_response_characters']>=0, 'invalid response custody')
            if kind=='probe':
                text=c['answer_as_judged']
                require(isinstance(text,str) and len(text)<=4000 and len(text)<=c['original_response_characters'], 'invalid judged projection')
            else:
                raw=c['raw_response']
                require(len(raw)==c['original_response_characters'] and len(raw.encode())==c['original_response_bytes'] and hashlib.sha256(raw.encode()).hexdigest()==c['original_response_sha256'], 'raw judge response custody mismatch')
                require(c['verdict']==verdict and c['raw_result']=={'verdict':verdict} and judgment(raw)==verdict, 'judge raw verdict mismatch')
        return c

    require(len(results['controls'])==4 and len({c['id'] for c in results['controls']})==4, 'control results incomplete')
    for control in results['controls']:
        require(control['id'] in controls and control['expected']==controls[control['id']]['expected'] and set(control['verdicts'])==set(judges), 'control identity mismatch')
        for judge in judges:
            v=control['verdicts'][judge];require(v==control['expected'], 'judge not qualified')
            call(f"judge-controls/{judge}/{control['id']}",judge,'judge_control','ok',v)
    expected={(r,c) for r in rules for c in coders};seen=set();computed=[];totals=defaultdict(Counter);source_counts=defaultdict(Counter)
    first, second=judges
    for row in results['rows']:
        key=(row['candidate_id'],row['coder']);require(key in expected and key not in seen, 'duplicate/unscheduled pair');seen.add(key)
        require(row['project']==rules[key[0]]['project'] and sorted(a['rep'] for a in row['answers'])==[1,2,3], 'pair identity or repetitions mismatch')
        counts=Counter()
        for answer in row['answers']:
            slot=f"probes/{key[0]}/{key[1]}/rep{answer['rep']}"
            require(answer['status'] in ('ok','call_failed'), 'unknown answer status')
            call(slot,key[1],'probe',answer['status'])
            if answer['status']=='call_failed':
                require(answer.get('states_rule') is None and answer.get('verdicts') in (None,{}), 'failed probe has labels/judgments');counts['probe_failed']+=1;continue
            verdicts=answer.get('verdicts');require(isinstance(verdicts,dict) and first in verdicts, 'first judge missing')
            required={first,second} if verdicts[first]=='yes' else {first}
            require(set(verdicts)==required and all(v in ('yes','no',None) for v in verdicts.values()), 'incorrect conditional judge schedule')
            # Exact executor routing, including the unresolved (None) case.
            derived='no' if verdicts[first]=='no' else verdicts.get(second) if verdicts[first]=='yes' and verdicts.get(second) in ('yes','no') else None
            require(answer.get('states_rule')==derived, 'answer state differs from judge routing')
            for judge in required:
                jslot=f'{slot}/judges/{judge}';require(jslot in by_slot, 'judge slot missing')
                jstatus=by_slot[jslot]['status'];require(jstatus in ('ok','call_failed') and (jstatus=='ok' or verdicts[judge] is None), 'failed judge has a verdict')
                call(jslot,judge,'judge',jstatus,verdicts[judge])
            counts['judge_unresolved' if derived is None else derived]+=1
        yes=counts['yes'];unknown=counts['probe_failed']+counts['judge_unresolved'];label=int(yes>=2)
        require(row['yes']==yes and row['memorized']==label, 'aggregate differs from answers')
        diagnostic='recovered' if yes>=2 else 'not_recovered' if yes+unknown<2 else 'inconclusive'
        computed.append({'candidate_id':key[0],'project':row['project'],'coder':key[1], 'target_rule':rules[key[0]]['rule'],'frozen_memorized':label,'yes':yes,'no':counts['no'],'probe_failed':counts['probe_failed'],'judge_unresolved':counts['judge_unresolved'],'diagnostic':diagnostic})
        totals[key[1]].update({diagnostic:1,'evaluated_pairs':1,'frozen_memorized_1':label,'answer_slots':3,**dict(counts)})
        source_counts[key[1]][str(label)]+=1
    require(seen==expected and seen_calls==set(by_slot), 'missing pair or extra call')
    summary={'rules':len(rules),'memorized_by_coder':{c:dict(t) for c,t in source_counts.items()},'unjudged_answers':sum(r['judge_unresolved'] for r in computed)}
    require(results['summary']==summary, 'source summary mismatch')
    require(hashlib.sha256((root/'results.json').read_bytes()).hexdigest()==custody['source_results_sha256'], 'public results bytes differ from source custody hash')
    require(audit['rows']==computed and audit['by_coder']=={c:dict(totals[c]) for c in coders} and audit['source_status']=='complete' and audit['judges_qualified'] is True and audit['missing_pairs']==[] and audit['planned_pairs']==len(expected) and audit['observed_pairs']==len(expected) and audit['planned_answer_slots']==len(expected)*3 and audit['rules']==len(rules), 'audit does not reproduce public rows')
    require(audit['results_sha256']==custody['source_results_sha256'] and audit['panel_results_sha256']==manifest['panel_results_sha256']==custody['panel_results_sha256'] and audit['executor_sha256']==manifest['script_sha256']==custody['executor_sha256'] and audit['source_bindings_verified'] is True and audit['labels_unchanged'] is True and custody['labels_unchanged'] is True, 'custody/audit bindings mismatch')
    probes=len(expected)*3
    expected_accounting={'planned_probe_calls':probes,'planned_control_calls':8,'planned_judge_calls_maximum':probes*2,'scheduled_calls_conditional':len(calls),'observed_attempts':len(calls),'missing_scheduled_calls':0,'missing_pairs':[],'failed_calls':sum(c['status']=='call_failed' for c in calls),'second_judge_not_scheduled':probes-sum(c['kind']=='judge' and c['model']==second for c in calls)}
    require(accounting==expected_accounting, 'call accounting mismatch')
    return {'status':'verified','rules':len(rules),'pairs':len(expected),'answer_slots':probes,'calls':len(calls),'by_coder':audit['by_coder'], 'limits':'Checks public projection consistency and exact original results bytes. Truncated original probe bytes and private captures are unavailable; source hashes are custody references, not independently reconstructed originals.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--public',type=Path,required=True);args=p.parse_args()
    print(json.dumps(verify(args.public),ensure_ascii=False))


if __name__=='__main__':main()
