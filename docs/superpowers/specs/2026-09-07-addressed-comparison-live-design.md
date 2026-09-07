# Execute the frozen v3/v4 auxiliary comparison

The investigator has authorized merging PR #46 and running its comparison.
PR #46 is now on `main` at `207f545`. It supplies an offline plan and response
audit; a separate coordinator must own real dispatch and the shared budget.
This specification defines that coordinator. Written-spec review is pending.

The comparison retains the [approved study design](2026-09-07-addressed-comparison-design.md):
48 development calls, followed by 96 evaluation calls only if development
passes. No main-pilot collection is authorized by either phase. Work proceeds
sequentially without subagents, with sampled application memory reported
separately from any claim of a system-wide memory limit.

## Scope and alternatives

Use a separate live coordinator around the existing plan, auditor, provider
adapter and durable ledger. Keeping the offline interface without credentials
preserves its read-only contract. Reusing the old v2/v3 runner would require
changing a frozen study; a new generic experiment engine would add unnecessary
surface area. Neither is needed for this bounded comparison.

The coordinator changes execution and budget ownership only. It must not change
the source bank, construction answers, source split, v3/v4 prompts, parsers,
512-token output allowance, input bounds or alternating call order. Both arms
use the same providers and frozen prices. It must not import old responses as
new observations, select cases after responses, repair model output or retry
failed judgments to obtain a passing gate.

## Acceptance contract

1. Given complete failed predecessor development, zero predecessor evaluation
   receipts and no pending accounting, preparation records one exclusive
   successor and a budget-closure receipt. Parent and predecessor files remain
   byte-identical, including their original claim and all measured spending.
2. Given changed custody, a second successor, missing or corrupt evidence,
   uncertain cost, unavailable locks or an exceeded cap, the coordinator refuses
   dispatch. A missing new ledger is an error, never a reason to recreate it.
3. Given an authorized frozen run, each planned call has a durable reservation
   before provider contact and a persisted observation before reconciliation.
   Resume skips verified completions. An ambiguous attempt blocks subsequent
   calls and is never automatically retried.
4. Given all 48 development receipts, evaluation is allowed only when the
   prospective v4 rule passes for both providers. An authored response audit or
   edited report cannot authorize evaluation. Failure leaves 96 calls unattempted.
5. Given partial or complete collection, reporting includes every planned call,
   invalid response and missing observation, alongside verified costs and pending
   reservations. Citation integrity, construction agreement and semantic validity
   remain separate. Main collection stays blocked even if all 144 calls pass.

## Budget closure and exclusive ownership

The existing offline proposal remains a proposal and is never overwritten.
Recompute it under the final runtime and compare its experimental contract with
the approved offline plan: predecessor custody, cases, calls, providers and
budget must match. New coordinator source files require a new runtime identity,
not a new study population or allowance. Preserve both plan versions.

Preparation requires an explicit live-approval option and records the user's
authorization scope in the new private manifest. Under the parent lock and
then the predecessor lock, verify the failed predecessor from its journal,
not its report. Create a new directory outside every Git checkout with mode
0700. Write the manifest, integrity record, closure receipt and empty durable
ledger before publishing an exclusive successor claim alongside the old claim.
Use exclusive file creation and synchronize files and their parent directories.

The closure receipt binds predecessor custody, the new manifest, the retained
actual spending, cancelled unused direct reservations and released unused
contingency. Preserve the original claim. The successor claim binds the new
directory, manifest and closure receipt. A partially prepared directory or claim
cannot dispatch and is preserved for inspection, not automatically repaired.
Another directory does not establish another spending allowance.

The closed predecessor cannot legally execute its evaluation because its
unchanged development gate failed; its completed development has no unpaid
occurrences. The coordinator also holds the original parent and predecessor
locks throughout each live phase. Altered predecessor state invalidates custody
and stops the successor.

All accounting uses integer microdollars. Retain parent spending, every remaining
parent direct reservation, the parent's full contingency, predecessor actual
spending and the earlier unresolved reservation. Add the complete new envelope,
including its contingency. Require the shared total to fit US$7 and predecessor
auxiliary spending plus the new envelope to fit US$1. Before each dispatch,
check new actual spending plus remaining direct reservations and full new
contingency against both caps. Do not release the parent's contingency or infer
credit balances from protocol reservations.

## Runtime freeze and phase gate

Freeze committed source, installed-package identity, exact request digests,
provider endpoints, requested/accepted model identities and pricing before the
first call. Check key presence without printing credentials. If provider pricing
or configuration needs revision, stop before collection and create a reviewed
freeze rather than silently changing the approved contract.

Use the existing provider factory with SDK retries disabled and a 45-second
timeout. The ledger reserves before dispatch, retains raw responses and usage,
and reconciles verified costs, model identity and latency. Verify receipt/request
identity when loading completed calls. A response with a bad judgment schema but
valid accounting remains a completed, invalid judgment. An unverifiable provider
outcome retains its pending reservation and stops the run.

The live gate requires verified receipts for every planned development call.
For each provider, v4 needs 12/12 valid responses, at least 10/12 exact obligation
vectors, and 2/2 exact vectors for long omission, partial missing, partial complete
and partial contradiction. Evaluation uses 24/24, at least 20/24 and 4/4,
respectively. V3 schema failures remain baseline outcomes. Aggregate-status
agreement is reported but cannot substitute for exact-vector agreement.

Evaluation recomputes the development decision from verified ledger responses
through the frozen auditor. It then rechecks the ledger head and custody under
the dispatch locks. The previously saved report is never an authorization token.
Passing evaluation completes this auxiliary comparison only. Failure ends this
version; a later prompt change requires another development decision.

## Modules, locking and failure behavior

`eval/addressed_comparison_custody.py` owns private manifest creation, closure,
exclusive successor claims, bounded reads, custody verification and shared-budget
checks. It reuses the existing plan arithmetic and journal inspection. It does
not instantiate providers or score judgments.

`eval/addressed_comparison_live.py` exposes `prepare`, `development`, `evaluation`
and `report`. It owns sequential dispatch, receipt-derived phase decisions and
redacted reporting. Tests inject providers at the existing adapter boundary;
real callers use the existing factory. No new dependency or generic workflow
abstraction is needed.

Preserve the existing offline modules and frozen predecessor code. Their plan
validation and auditing functions acquire parent/predecessor locks internally.
Do not call them while those same locks are held. Instead, validate outside the
dispatch critical section, then recheck byte custody and runtime identity inside
it. Whenever all locks are needed, acquire parent, predecessor, then successor
ledger. Use nonblocking acquisition and release on every exit path.

For reporting, take a verified journal snapshot under the locks, release them
before invoking the offline auditor, then recheck custody and the journal head.
Reject a changed snapshot. Evaluation follows the same process and rechecks
the report's privately bound head after acquiring dispatch ownership. This
avoids nested locks and prevents a stale report from releasing calls.

Private paths must be canonical and regular; reject symlink components, duplicate
JSON keys, oversized files, nonstandard numeric constants and malformed plans.
Public errors use fixed categories without paths, raw exceptions or key values.
Missing, truncated or changed durable files are failures, not reset requests.

## Reporting and scientific limits

Keep raw responses, request hashes, source joins, configuration identities,
closure records, ledger heads and detailed receipts in private storage. Public
reports use opaque provider/source groups and aggregate counts. Distinguish
dispatched attempts, reconciled completions, pending attempts, invalid judgments
and unattempted calls; do not describe all missing observations as unattempted.

Reuse the auditor's planned denominators, arm/operation strata, aggregate and
exact-vector agreement, and paired outcomes. Add receipt-derived phase decisions,
costs, usage and pending-reservation counts in a separate live report. Preserve
the nested auditor's offline authority flags rather than rewriting it as proof
of dispatch. Missing-cost outcomes keep verified cost as a lower bound with the
pending commitment separately visible.

The cases use AI-assisted construction answers and dependent variants. Evaluation
locators may have appeared in screening/background material; they are not a
pristine held-out sample. Matching the construction vector does not show that a
cited segment semantically supports the decision. Requested and returned model
IDs do not establish immutable vendor weights. Report `semantic_validity` as
`not_measured`; H1/H2 and main collection remain unreleased.

## Verification and delivery

Before implementation, review this written specification. Use test-first
integration scenarios with real temporary journals and authored adapter responses.
Cover exclusive succession, partial preparation, missing ledgers, lock contention,
source/price drift, unchanged predecessor bytes, cap boundaries, resume without
repurchase, a crash after reservation, missing usage, invalid judgments, failed
development, stale reports and both passing phases. Test CLI privacy and network
prohibition for preparation/reporting.

Run focused and full suites, compilation and the three repository gates. Review
cost and secret boundaries, responsibility separation and error handling directly;
review is not independent when performed inline. Commit the verified runtime
before a fresh private preflight. Execute development sequentially and evaluation
only if the gate passes. Preserve negative results and incomplete episodes, then
update research prose with measured findings rather than software-test outcomes.
