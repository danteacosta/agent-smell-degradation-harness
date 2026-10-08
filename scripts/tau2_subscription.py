"""Single-task exploratory τ² wrapper; defaults to offline preflight only."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

from agents.tau2_subscription import PINNED_TAU2, PROTOCOL, SubscriptionBridge, install, quota_gate


def refresh_claude_quota(path, capture, aliases):
    """Refresh only Claude routes from the latest official captured CLI event."""
    capture, path = Path(capture), Path(path)
    try:
        sampled = capture.stat().st_mtime
        if not 0 <= time.time() - sampled <= 60:
            raise ValueError("stale capture")
        events = [json.loads(line) for line in capture.read_text().splitlines() if line.strip()]
        info = [e['rate_limit_info'] for e in events if e.get('type') == 'rate_limit_event'][-1]
        if info['status'] not in ('allowed', 'allowed_warning') or info['isUsingOverage'] is not False:
            raise ValueError("subscription quota unavailable")
        windows = []
        for name, window in info['unifiedWindows'].items():
            utilization, reset = window['utilization'], window['resetsAt']
            if (type(utilization) not in (int, float) or not math.isfinite(utilization)
                or not 0 <= utilization <= 1 or type(reset) not in (int, float)
                or not math.isfinite(reset) or reset <= time.time()):
                raise ValueError("invalid public quota window")
            windows.append({'name': 'weekly' if name == 'seven_day' else name,
                            'remaining_percent': (1-utilization)*100, 'reset_at': reset})
        if not windows or 'weekly' not in {w['name'] for w in windows}:
            raise ValueError("weekly quota missing")
        snapshot = json.loads(path.read_text())
        for alias in aliases:
            if alias not in snapshot['routes']:
                raise ValueError("missing quota route")
            snapshot['routes'][alias] = {'sampled_at':sampled, 'status':info['status'],
                                        'extra_usage':False, 'windows':windows}
        temporary = path.with_name(path.name + '.' + uuid.uuid4().hex)
        try:
            write_private(temporary, snapshot)
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
    except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError) as exc:
        raise RuntimeError("public Claude quota unavailable; no next call") from exc


def preflight(checkout):
    checkout = Path(checkout).resolve(strict=True)
    commit = subprocess.check_output(["git","-C",str(checkout),"rev-parse","HEAD"],text=True).strip()
    dirty = subprocess.check_output(
        ["git","-C",str(checkout),"status","--porcelain","--untracked-files=no"],text=True).strip()
    if commit != PINNED_TAU2 or dirty or not (checkout/"src/tau2").is_dir():
        raise ValueError("clean pinned tau2 checkout required")


class TurnTransport:
    """Fresh official provider and private evidence directory for every turn."""
    def __init__(self, provider_class, *, executable, model, out, timeout,
                 quota_path=None, quota_aliases=()):
        self.provider_class, self.executable, self.model = provider_class, executable, model
        self.out, self.timeout = Path(out), timeout
        self.last_call_metadata = {}
        self.quota_path, self.quota_aliases = quota_path, quota_aliases

    def complete(self, request):
        evidence = self.out/uuid.uuid4().hex
        provider = self.provider_class(executable=self.executable,model=self.model,
            timeout_seconds=self.timeout,evidence_directory=evidence)
        answer = provider.complete(request)
        self.last_call_metadata = provider.last_call_metadata
        if self.quota_path is not None:
            refresh_claude_quota(self.quota_path, evidence/'stdout.jsonl', self.quota_aliases)
            write_private(evidence/'quota-after.json', json.loads(Path(self.quota_path).read_text()))
        return answer


def write_private(path, data):
    fd = os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,"w") as f:
        json.dump(data,f,indent=2,allow_nan=False); f.write("\n")


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tau2",type=Path,required=True)
    ap.add_argument("--data",type=Path,required=True,help="one build-generated variant root")
    ap.add_argument("--execute",action="store_true",help="explicit single task, never a batch")
    ap.add_argument("--task-id")
    ap.add_argument("--agent-provider",choices=["claude","codex"])
    ap.add_argument("--user-provider",choices=["claude","codex"])
    ap.add_argument("--agent-model"); ap.add_argument("--user-model")
    ap.add_argument("--claude-executable"); ap.add_argument("--codex-executable")
    ap.add_argument("--quota",type=Path); ap.add_argument("--out",type=Path)
    ap.add_argument("--refresh-claude-quota",action="store_true",
                    help="refresh Claude routes after each call from official CLI events")
    ap.add_argument("--max-calls",type=int); ap.add_argument("--timeout",type=float,default=120)
    ap.add_argument("--agent-windows",help="all public quota window names, comma separated")
    ap.add_argument("--user-windows",help="all public quota window names, comma separated")
    ap.add_argument("--seed",type=int,default=2026100701)
    args=ap.parse_args(argv)
    preflight(args.tau2)
    data=args.data.resolve(strict=True)
    if not (data/"tau2/domains/airline/policy.md").is_file():
        ap.error("build-generated variant data root required")
    if not args.execute:
        print(json.dumps({"status":"offline_preflight_ok","tau2_commit":PINNED_TAU2,
                          "protocol":PROTOCOL,"model_calls":0}))
        return
    for name in ("task_id","agent_provider","user_provider","agent_model","user_model",
                 "quota","out","max_calls","agent_windows","user_windows"):
        if getattr(args,name) is None: ap.error("--execute requires --"+name.replace("_","-"))
    if args.max_calls <= 0: ap.error("positive max-calls required")
    # Set before importing tau2: its data directory is resolved at import time.
    os.environ["TAU2_DATA_DIR"]=str(data)
    sys.path.insert(0,str(args.tau2.resolve()/"src"))
    from tau2.data_model.simulation import TextRunConfig
    from tau2.run import get_tasks, run_single_task
    from agents.claude_cli_v2 import ClaudeCLIProvider
    from agents.codex_cli import CodexCLIProvider
    out=args.out.resolve()
    if out.is_relative_to(Path(__file__).resolve().parents[1]):
        ap.error("raw evidence must be outside the repository checkout")
    out.mkdir(mode=0o700,parents=True,exist_ok=False)
    routes={}
    claude_aliases=[f'subscription-{role}' for role in ('agent','user')
                   if getattr(args,role+'_provider') == 'claude']
    for role in ("agent","user"):
        backend=getattr(args,role+"_provider")
        executable=getattr(args,backend+"_executable")
        if not executable: ap.error("explicit official CLI executable required")
        routes["subscription-"+role]=TurnTransport(
            ClaudeCLIProvider if backend=="claude" else CodexCLIProvider,
            executable=executable,model=getattr(args,role+"_model"),out=out,timeout=args.timeout,
            quota_path=args.quota if args.refresh_claude_quota and backend=='claude' else None,
            quota_aliases=claude_aliases)
    expected={f"subscription-{role}":getattr(args,role+"_windows").split(",")
              for role in ("agent","user")}
    bridge=SubscriptionBridge(routes,before_call=quota_gate(args.quota,
        expected_windows=expected),max_calls=args.max_calls)
    config=TextRunConfig(domain="airline",agent="llm_agent",user="user_simulator",
        llm_agent="subscription-agent",llm_user="subscription-user",
        llm_args_agent={"num_retries":0},llm_args_user={"num_retries":0},
        num_trials=1,max_concurrency=1,max_retries=0,auto_resume=False,
        auto_review=False,hallucination_retries=0,seed=args.seed)
    write_private(out/"started.json",{"protocol":PROTOCOL,"tau2_commit":PINNED_TAU2,
        "task_id":args.task_id,"config":config.model_dump(mode="json"),
        "requested_models":{"agent":args.agent_model,"user":args.user_model},
        "refresh_claude_quota":args.refresh_claude_quota,
        "confirmatory_eligible":False})
    try:
        tasks=get_tasks("airline",task_ids=[args.task_id])
        if len(tasks)!=1: raise ValueError("exactly one matching task required")
        # ALL remains the upstream evaluation default. Unregistered LLM judges
        # stop rather than secretly using an API or silently skipping a check.
        with install(bridge):
            result=run_single_task(config,tasks[0],seed=args.seed)
        if bridge.stopped: raise RuntimeError("transport failed during simulation")
        write_private(out/"result.json",{"simulations":[result.model_dump(mode="json")]})
    except BaseException as exc:
        write_private(out/"stopped.json",{"reason":type(exc).__name__,"retry":False})
        raise
    finally:
        write_private(out/"receipts.json",bridge.receipts)


if __name__=="__main__": main()
