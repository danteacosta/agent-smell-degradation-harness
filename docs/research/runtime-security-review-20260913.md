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

Automatic recovery supports only a preflight with no live-start marker, ledger
or raw evidence. Before live initialization, a durable marker records that
reconciliation is required. A crash before the first provider call may therefore
produce a conservative false block. A crash after dispatch cannot be safely
treated as proof that the provider did not execute.

Post-call automatic resume is **not implemented**. No claim of exactly-once
provider execution is made. Existing raw evidence, ledger and checkpoint must
be preserved. Do not remove markers to force a retry. Required next work:

1. Reconcile each ledger reservation with durable response and provider billing
   evidence, retaining ambiguous outcomes as unresolved.
2. Persist and hash validated stage outputs before advancing the scheduler;
   replay completed stages locally and skip only fully verified operations.
3. Bind the recovery inventory to provider/model, input/configuration hashes,
   corpus, rubric, source revision and price snapshot.
4. Qualify crashes before dispatch, after remote acceptance, after response
   receipt, after evidence fsync and before checkpoint commit. Provider-side
   idempotency must be verified for the actual API before claiming deduplication.

Changing transport behavior requires a new reviewed runtime configuration and
qualification; no frozen experimental hash or historical evidence was rewritten.

## Dependencies and resource review

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
