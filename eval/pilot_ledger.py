"""Single-writer explicit-call journal for the separately authorized US$7 pilot.

No change to the fixed pre-pilot's US$1 policy. A response and its accounting
are persisted together. A pending reservation is never automatically retried.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import time

from eval.exploratory_cost import CostLedger, ProviderPricing, TokenBounds
from eval.pilot_preparation import digest
from label_plane.judge_prompt_comparison import _unique_keys

CAP = 7_000_000


class PilotStop(RuntimeError):
    """The frozen experiment cannot safely dispatch another call."""


def inspect_ledger(path, plan, pricing):
    """Validate the same journal state without creating a lock or writing bytes."""
    ledger = object.__new__(PilotLedger)
    ledger.plan = {c['id']:c for c in plan}
    ledger.pricing = pricing
    ledger.budget = envelope(plan, pricing)
    ledger.config = {'schema_version':'pilot-ledger/v1','calls':plan,
                     'prices':{s:p.to_dict() for s,p in sorted(pricing.items())},'budget':ledger.budget}
    ledger.pending, ledger.completed = {}, {}
    ledger.spent, ledger.index, ledger.head = 0, 0, '0'*64
    ledger.stopped = False
    path = Path(path)
    if path.is_symlink(): raise PilotStop('symlink journal rejected')
    raw = path.read_text()
    if not raw or not raw.endswith('\n'): raise PilotStop('empty or truncated journal')
    for line in raw.splitlines():
        event=json.loads(line,object_pairs_hook=_unique_keys)
        check={k:v for k,v in event.items() if k!='hash'}
        if (set(event)!={'event','data','index','prev','hash'} or event['index']!=ledger.index
            or event['prev']!=ledger.head or event['hash']!=digest(check)):
            raise PilotStop('journal integrity mismatch')
        ledger._apply(event['event'],event['data'])
        ledger.index+=1; ledger.head=event['hash']
    report=ledger.report()
    if ledger.pending: report['state']='stopped'
    return report, ledger.completed


def envelope(plan, pricing):
    if not plan or len(plan) > 5000 or len(pricing) != 2:
        raise ValueError('pilot requires an explicit bounded plan and two providers')
    ids = set()
    direct = 0
    for call in plan:
        if set(call) - {'id','slot','phase','input_bound','output_bound','prompt_sha256'}:
            raise ValueError('unknown planned call field')
        if not all(isinstance(call.get(k),str) and call[k] for k in ('id','slot','phase')):
            raise ValueError('missing call identity')
        if call['id'] in ids or call['slot'] not in pricing:
            raise ValueError('duplicate call or unknown provider')
        ids.add(call['id'])
        if not isinstance(pricing[call['slot']], ProviderPricing):
            raise ValueError('invalid frozen pricing')
        if any(type(call.get(k)) is not int or call[k] <= 0 for k in ('input_bound','output_bound')):
            raise ValueError('invalid call bound')
        direct += pricing[call['slot']].reservation_microusd(TokenBounds(call['input_bound'],call['output_bound']))
    return {'planned_calls':len(plan), 'direct_microusd':direct,
            'contingency_microusd':(direct+3)//4, 'reserved_microusd':direct+(direct+3)//4,
            'approved_cap_microusd':CAP, 'within_cap':direct+(direct+3)//4 <= CAP}


class PilotLedger:
    def __init__(self,path,plan,pricing,*,approval=False):
        if approval is not True:
            raise ValueError('explicit expanded pilot authorization required')
        self.plan = {c['id']:c for c in json.loads(json.dumps(plan))}
        self.pricing = dict(pricing)
        self.budget = envelope(plan, pricing)
        if not self.budget['within_cap']:
            raise ValueError('complete pilot envelope exceeds US$7')
        self.config = {'schema_version':'pilot-ledger/v1', 'calls':list(self.plan.values()),
                       'prices':{s:p.to_dict() for s,p in sorted(pricing.items())}, 'budget':self.budget}
        self.path = Path(path)
        self.pending, self.completed = {}, {}
        self.spent, self.index, self.head = 0, 0, '0'*64
        self.stopped = False
        self._lock = None
        self._file = None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.is_symlink() or Path(str(self.path)+'.lock').is_symlink():
            raise PilotStop('symlink journal or lock rejected')
        try:
            self._lock = open(str(self.path)+'.lock','a+')
            fcntl.flock(self._lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            existed = self.path.exists()
            self._file = self.path.open('a+',encoding='utf-8')
            self._file.seek(0)
            raw = self._file.read()
            if existed:
                if not raw or not raw.endswith('\n'):
                    raise PilotStop('empty or truncated journal; cannot reset budget')
                for line in raw.splitlines():
                    event=json.loads(line,object_pairs_hook=_unique_keys)
                    check={k:v for k,v in event.items() if k!='hash'}
                    if (set(event)!={'event','data','index','prev','hash'} or event['index']!=self.index
                        or event['prev']!=self.head or event['hash']!=digest(check)):
                        raise PilotStop('journal integrity mismatch')
                    self._apply(event['event'],event['data'])
                    self.index+=1; self.head=event['hash']
            else:
                self._append('plan',self.config)
                directory_fd=os.open(self.path.parent,os.O_RDONLY)
                try: os.fsync(directory_fd)
                finally: os.close(directory_fd)
            if self.pending or self.stopped:
                raise PilotStop('stopped or ambiguous prior call; no automatic retry')
        except Exception as exc:
            self.close()
            if isinstance(exc,PilotStop): raise
            raise PilotStop('journal unavailable or already owned') from exc

    def _apply(self,kind,data):
        if kind=='plan':
            if self.index!=0 or data!=self.config: raise PilotStop('frozen plan mismatch')
        elif kind=='reserve':
            identifier=data['id']
            call=self.plan.get(identifier)
            if not call or identifier in self.pending or identifier in self.completed:
                raise PilotStop('invalid reservation')
            expected=self.pricing[call['slot']].reservation_microusd(TokenBounds(call['input_bound'],call['output_bound']))
            if data['reserved_microusd']!=expected: raise PilotStop('reservation mismatch')
            self.pending[identifier]=data
        elif kind=='reconcile':
            identifier=data['id']
            if identifier not in self.pending: raise PilotStop('reconciliation without reservation')
            call=self.plan[identifier]; price=self.pricing[call['slot']]
            usage=CostLedger._normalized_usage(data['usage'])
            actual=price._cost_microusd(usage['input_tokens'],usage['output_tokens'],usage['cached_tokens'])
            if (data['actual_cost_microusd']!=actual or actual>self.pending[identifier]['reserved_microusd']
                or usage['input_tokens']>call['input_bound'] or usage['output_tokens']>call['output_bound']):
                raise PilotStop('usage/cost mismatch')
            self.spent+=actual
            self.completed[identifier]={**data,'prompt_sha256':self.pending[identifier]['prompt_sha256']}
            del self.pending[identifier]
        elif kind=='observation':
            if data['id'] not in self.pending: raise PilotStop('observation without reservation')
        elif kind=='stop': self.stopped=True
        else: raise PilotStop('unknown journal event')

    def _append(self,kind,data):
        event={'event':kind,'data':data,'index':self.index,'prev':self.head}
        event['hash']=digest(event)
        try:
            self._file.write(json.dumps(event,sort_keys=True,allow_nan=False)+'\n')
            self._file.flush(); os.fsync(self._file.fileno())
            self._apply(kind,data)
            self.index+=1; self.head=event['hash']
        except Exception as exc:
            self.stopped=True
            raise PilotStop('journal durability failure') from exc

    def stop(self,reason):
        self.stopped=True
        self._append('stop',{'reason':reason})
        raise PilotStop(reason)

    def complete(self,identifier,provider,request):
        if self.stopped or self.pending: raise PilotStop('pilot is stopped')
        call=self.plan.get(identifier)
        if call is None: self.stop('unplanned_call')
        prompt_hash=hashlib.sha256(request.prompt.encode()).hexdigest()
        if identifier in self.completed:
            row=self.completed[identifier]
            if row['prompt_sha256']!=prompt_hash: self.stop('changed_prompt_for_paid_call')
            provider.last_call_metadata={k:row[k] for k in ('usage','response_model','response_id')}
            return row['response']
        if (len(request.prompt.encode())+64 > call['input_bound']
            or request.max_output_tokens!=call['output_bound']
            or ('prompt_sha256' in call and call['prompt_sha256']!=prompt_hash)):
            self.stop('request_outside_frozen_plan')
        price=self.pricing[call['slot']]
        reserved=price.reservation_microusd(TokenBounds(call['input_bound'],call['output_bound']))
        if self.spent+reserved+self.budget['contingency_microusd']>CAP:
            self.stop('budget_exhausted')
        provider.last_call_metadata={}
        self._append('reserve',{'id':identifier,'reserved_microusd':reserved,'prompt_sha256':prompt_hash})
        started=time.monotonic()
        try:
            response=provider.complete(request)
            metadata=provider.last_call_metadata
            self._append('observation',{'id':identifier,'response':response,
                         'usage':metadata.get('usage'),'response_model':metadata.get('response_model'),
                         'response_id':metadata.get('response_id')})
            usage=CostLedger._normalized_usage(metadata.get('usage'))
            if metadata.get('response_model') not in {price.model,price.model_version}:
                raise ValueError('unexpected model identity')
            if usage['input_tokens']>call['input_bound'] or usage['output_tokens']>call['output_bound']:
                raise ValueError('usage exceeds frozen bounds')
            actual=price._cost_microusd(usage['input_tokens'],usage['output_tokens'],usage['cached_tokens'])
            if not isinstance(response,str): raise ValueError('response is not text')
            self._append('reconcile',{'id':identifier,'response':response,'usage':usage,
                         'response_model':metadata['response_model'],'response_id':metadata.get('response_id'),
                         'actual_cost_microusd':actual,'latency_ms':round((time.monotonic()-started)*1000,3)})
            return response
        except Exception as exc:
            if not self.stopped: self.stop('unverified_provider_outcome')
            raise PilotStop('unverified_provider_outcome') from exc

    def report(self):
        return {**self.budget,'spent_microusd':self.spent,'completed_calls':len(self.completed),
                'pending_count':len(self.pending), 'active_reserved_microusd':sum(x['reserved_microusd'] for x in self.pending.values()),
                'state':'stopped' if self.stopped else 'ready','ledger_head':self.head}

    def close(self):
        if self._file is not None: self._file.close(); self._file=None
        if self._lock is not None: self._lock.close(); self._lock=None

    def __enter__(self): return self
    def __exit__(self,*args): self.close()
