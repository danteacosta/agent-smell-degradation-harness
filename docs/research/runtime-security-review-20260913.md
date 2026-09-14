# Runtime recovery and local security review — 2026-09-13

Scope: white-box inspection and isolated adversarial tests of exploratory
collection ownership, recovery, provider transport construction and Python
sandbox input validation. No production endpoint, private corpus, paid provider,
external target or live sandbox escape was exercised. This is a bounded local
pentest, not a security certification.

## Findings and changes

| Finding | Impact | Change and evidence |
| --- | --- | --- |
| Resume re-enters generation with fresh counters and run identity | Duplicate requests or mixed evidence | Preserve run identity for untouched preflight only; compare source, corpus, configuration, rubric and reference hashes before replacing files. Rejected recovery preserves prior files byte-for-byte. |
| No process-wide run ownership | Concurrent writers can interleave evidence | Atomic directory creation plus nonblocking POSIX directory-inode flock held for the whole runner. A second process fails; process death releases the lock. |
| Existing run paths can be reused | Prior evidence can be overwritten | New launch refuses existing run/output paths. Resumed directories require ownership, mode 0700, regular entries and no symlinks. |
| Live SDK clients do not explicitly disable transport retries | One ledger attempt may hide multiple network attempts | Construct OpenAI-compatible and Anthropic clients with max_retries=0 and timeout=60 seconds. Injected clients remain the caller's responsibility. This timeout is a transport setting, not a total collection deadline. |
| Source normalization precedes size checks | Avoidable allocation and malformed Unicode exception | Reject excessive raw character/UTF-8 byte sizes and invalid Unicode before normalization or worker creation. |
| Repeated linear corpus lookup per artifact | Avoidable repeated scans | Build one intent index; replace each scan with a dictionary lookup. No elapsed-time speedup claimed. |

Run ownership is a single-host POSIX guarantee on a trusted local filesystem.
It does not defend against a malicious same-UID process, administrator, directory
rename by a trusted parent owner, or distributed/NFS lock semantics. Existing
directories with broader permissions are rejected; permissions are not silently
rewritten. No controls were removed to execute as root.

## Honest recovery boundary

Automatic recovery now covers preflight, generation, validated judging and the
final report commit. Before provider dispatch, the runner creates a durable call
intent. After receipt, it persists response and
usage before reconciling cost. A complete artifact then receives an immutable
execution receipt containing the original T1--T3 trace. Resume validates all
bindings and restores only those complete executions.

No claim of provider-side exactly-once execution is made. A crash after remote
acceptance but before durable response receipt remains ambiguous and blocks. A
durable response without a complete execution receipt also blocks because its
original runtime timestamps cannot be reconstructed. Existing raw evidence,
ledger and checkpoint must be preserved; do not remove markers to force retry.
Each successful judge response receives an immutable receipt bound to its request,
provider/model identity, generator relation, ledger boundary and frozen scope.
Two validated call receipts are then bound into one deterministic consolidated
result receipt. Resume reconstructs counters from these receipts and does not
dispatch completed judge calls again. Terminal status is written only after the
private and redacted public reports are durably committed. Failure between those
writes leaves `finalizing`, which is resumable from the validated receipts. Real
storage/power-loss qualification remains future work.

Changing transport behavior requires a new reviewed runtime configuration and
qualification; no frozen experimental hash or historical evidence was rewritten.

## Initial dependencies and resource findings (before the follow-up below)

This paragraph records the initial inspection, not the current implementation.
The hashed bundle, completed advisory scan and resource launcher below address
these gaps; host qualification and the stated coverage exclusions remain open.

The project pins ARP to a Git commit and already provides `constraints.txt`,
which pins PyYAML, pytest and several development dependencies. README installation
commands consume it, but the evaluation CI's editable development install does not.
Build tools and optional provider SDKs are not covered by that partial inventory;
it is not a complete transitive, artifact-hash-locked environment. Existing
qualification inventory checks help detect drift but do not substitute for a
reviewed reproducible lock. No CVE database scan was completed; no claim that
dependencies are vulnerability-free is made. Freeze the actual qualified
environment in an isolated build, rather than copying this mixed workspace's
packages into the experiment.

Sandbox inspection found existing source/test/literal bounds, CPU and address
space limits, process/file-descriptor limits, worker output bounds and process
termination. Local execution tests that cannot enforce all required controls
remain skipped. This review does not establish resistance to interpreter/kernel
vulnerabilities or aggregate memory exhaustion across many independent workers.
A global concurrency/resource cap and a total collection deadline remain open.

## Verification and source status

151 tests passed and 5 sandbox-execution tests were skipped locally. Fourteen
new cases cover concurrent process exclusion and crash release, three ambiguous
live markers, duplicate launch, three filesystem attacks, preflight identity and
reference mutation, two SDK constructors, and three hostile source inputs.
Existing ledger durability/budget tests were included. No provider was contacted.

Literature search: Birrell and Nelson, *Implementing Remote Procedure Calls*,
ACM TOCS 2(1), 1984, DOI https://doi.org/10.1145/2080.357392.
Peer-reviewed; provisional credibility 8/10 for foundational failure semantics.
Bibliographic identity was located, but attempted full-text access failed; no
paper-specific result is used to justify a scientific claim. The recovery
counterexample and changes above are supported by inspected code and tests.

## Follow-up: transport regressions and directory persistence

The remote evaluation at `7873152` exposed two integration-test SDK doubles that
did not accept the new retry and timeout arguments. Both now assert zero SDK
retries and a 60-second transport timeout; production safeguards are unchanged.

New runs and permitted preflight resumes flush the run directory and its ancestor
chain before entering the runner. Existing paths are not durability receipts;
resume must not bypass a previously failed barrier. Flush errors abort
entry and release descriptors/locks without deleting evidence. This addresses
a missing persistence barrier, not automatic recovery of remote operations.
Ordering and injected-failure tests do not simulate power loss or qualify a
particular filesystem, mount configuration, storage device or operating system.

Implementation motivation: Pillai et al., *All File Systems Are Not Created
Equal*, OSDI 2014 ([paper](https://www.usenix.org/system/files/conference/osdi14/osdi14-paper-pillai.pdf)).
The study distinguishes application atomicity from persistence; our application
of that distinction is an engineering inference, not evidence for H1/H2.

## Recoverable calls v1: response/cost boundary

`eval.recoverable_calls.call_session` provides a separate private session for
new, explicitly bound provider operations. It writes an immutable request intent,
reserves cost, receives the response, durably records response/usage, and only then
reconciles cost. On reopening, the existing ledger validates its hash chain and
arithmetic. A durable response may finish a missing reconciliation locally.
An already reconciled response is reused without a provider call or budget reset.

Bindings include run, source, corpus, rubric, oracle, runtime configuration and
pricing scope, plus provider/model, request digest, logical call ID and explicit
attempt. Changed bindings, conflicting usage, partial receipts and unknown remote
outcomes block reuse. Per-session thread serialization and directory-inode locks
exclude competing writers. Same-UID tampering remains outside the threat model;
checksums detect inconsistencies, not provenance authenticity.

An ambiguous reservation without a durable response is never retried or erased.
Reconcile provider response/billing evidence independently; absence of a bill
alone does not prove that an operation was not executed. No manual override or
deletion of an intent is supplied. Old evidence has no new receipts and is not
silently migrated. The exploratory runner now resumes the generation phase only
when complete `execution-receipt/v1` records restore the original runtime-native
T1--T3 payloads, timestamps, context events, artifact and provider metadata.
Each receipt is bound to the run/configuration/corpus/rubric/oracle/pricing/source
scope, pair, variant, episode, artifact, provider/model/version and an existing
cost-ledger boundary. Completed artifacts are skipped without provider calls;
unexpected receipts fail closed.

A cached stage response without a complete execution receipt still blocks:
re-running that stage would invent new timestamps and turn reconstruction into
false online warning evidence. The runner writes a `generation_complete` barrier
before judging and can resume from that barrier or a `judging` checkpoint.
Successful calls are restored only from validated `judge-call-receipt/v1`
records; completed occurrences are checked against `judge-result-receipt/v1`.
A synthetic interruption after two judged occurrences resumes the complete
1,296-operation fixture plan with 1,296 provider-fixture calls in total, not
1,300. This is full exploratory pipeline recovery for durable local receipts,
not provider-side exactly-once execution or power-loss qualification.

Finalization has its own resumable barrier. An injected failure on the first
public-report write, after all 1,296 fixture operations completed, leaves the
checkpoint in `finalizing`. A second process reconstructs and commits both
reports, advances the checkpoint to `completed`, and observes no additional
provider-fixture call. This tests process-level write interruption and ordering;
it does not emulate loss of power, volatile device caches or filesystem damage.

Implementation motivation is bounded by Zhang et al., *Fault-tolerant and
Transactional Stateful Serverless Workflows*, OSDI 2020
([paper](https://www.usenix.org/system/files/osdi20-zhang_haoran.pdf)). Beldi
combines durable operation logs with re-execution; this single-process design
borrows only that separation of durable completion from retry. It does not
inherit Beldi's distributed guarantees, strongly consistent storage assumptions
or AWS evaluation.

For an existing v1 session, this command reconciles durable response usage only;
it constructs no provider and prints a bounded accounting report:

```sh
python -m eval.recoverable_calls --directory /private/run.calls \
  --runtime-config /private/runtime.json --scope /private/frozen-scope.json
```

The scope must contain run_id, configuration_sha256, corpus_sha256,
rubric_sha256, oracle_sha256, source_revision and pricing_sha256. API callers use
`with call_session(path, cost_configuration, scope) as calls:` followed by
`calls.complete(provider, request, call_id=stable_id, phase=phase, attempt=1)`.
The caller remains responsible for source admission and provider authorization.

Recovery tests also terminate a spawned process with os._exit after fixture
remote acceptance, after durable response but before cost reconciliation, and
after cost reconciliation. A new process/session either refuses ambiguous
evidence byte-for-byte or reuses the response, reconciles exactly one cost event
and permits the next distinct operation. These are abrupt process-death tests,
not real provider calls, power-loss simulation or storage qualification.

## Global admission and resource supervision

```sh
python -m eval.collection_limits --root /private/shared-collection-slots \
  --max-runs 1 --wall-seconds 3600 --memory-bytes 2147483648 \
  --file-bytes 268435456 --open-files 128 -- COMMAND ARGUMENTS
```

All cooperating launchers must share the same root and fixed capacity. Separate
processes acquire bounded slots; crashes release them. The supervisor enforces a
wall deadline and kills the process group, including residual children after the
leader exits. Child address space, CPU time, file size and descriptor counts are
bounded before exec. Session receipts additionally cap call inventory, response
bytes, evidence quota and further dispatch after the session deadline. These are
not sandbox controls against a malicious child that escapes its process group.

Address-space limits apply per process, not to the aggregate descendant tree.
For aggregate memory, task count and CPU quota, supply `--cgroup` referencing a
delegated cgroup v2 with the exact configured memory.max, memory.swap.max=0,
pids.max and cpu.max. The launcher verifies policy and joins before exec; it
never changes existing cgroup limits. Host delegation and real OOM/fork/CPU
qualification remain required. Without a cgroup, no aggregate-RAM guarantee is
claimed. This is a launcher for a single-threaded supervisor, not a server API.

## Hashed dependency bundle and advisory gate

`scripts/dependency_bundle.py` resolves the runtime, dev, live and build-tool
closure in a clean Linux x86_64 CPython 3.12 environment. Registry wheels are
pinned with SHA-256; ARP is built from its pinned Git revision without isolated
unlocked build dependencies, then separately hash-bound. Once lock files exist,
the workflow consumes them rather than resolving new versions. No historical
qualification inventory is overwritten. Wheel artifacts must be archived beyond
the CI retention window before experiment freeze.

The dedicated dependency-audit workflow verifies offline hash-enforced install
and pip check, then runs pip-audit against exact registry versions. The evaluation
workflow runs the full test suite using the same frozen locks. The scanner has an
isolated, recorded tool inventory. VCS-only ARP and
the application are explicitly outside registry advisory coverage and require
source review. A failed scanner/network call is not a clean result; findings
fail the gate and are retained in audit.json. No automatic fix/ignore rule is
used. OS/kernel, native system packages, action supply chain and undisclosed
vulnerabilities are outside this package scan.

Implementation references: [pip repeatable installs](https://pip.pypa.io/en/stable/topics/repeatable-installs/)
and [PyPA pip-audit](https://github.com/pypa/pip-audit). These are implementation
documentation, not scientific evidence for H1/H2.

Executed dependency evidence: workflow run 34758454971 generated the two lock
files, passed pip check and 1360 tests plus nine subtests in the isolated bundle,
and scanned 25 registry packages with pip-audit 2.10.1 against PyPI advisories.
No known vulnerabilities were returned on 2026-09-13. The exact inventory,
exclusions and artifact SHA-256 are recorded in dependency-audit-20260913.json.
The evaluation workflow now consumes the frozen locks; the audit workflow no
longer duplicates its full-suite run. ARP's deterministic wheel hash must match
on every rebuild. This is a new dependency candidate, not a silent replacement
of previously qualified provider SDK/runtime snapshots.
The lock targets direct HTTPS, not optional SOCKS proxy transport. Local
constructor tests exposed an ambient SOCKS setting without socksio; no production
proxy configuration was changed. Constructor-only tests prohibit socket connects
and isolate ambient proxy settings. A SOCKS deployment needs its own reviewed
extra dependency lock and transport qualification.
