# Quote-based versus addressed evidence: offline comparison preparation

The investigator needs a bounded next comparison, not another unrecorded retry
of a failed study. PR #45 supplied the offline v4 evidence interface. This
increment prepares its comparison with the unchanged v3 interface and audits
supplied responses. It does not dispatch providers or release main collection.

Date: 2026-09-07. The user approved this offline direction in the research task.
The user approved this written specification before implementation. Review is
inline, not independent; no subagents are used under the user's memory constraint.

## Alternatives and decision

Prepare the complete 48-call development and conditional 96-call evaluation
plan, with an explicit proposal to close the failed predecessor. This preserves
the planned source split and makes the budget disposition reviewable. Reducing
the study would change its coverage; raising the cap is unnecessary if the
predecessor can be closed safely. Neither alternative is applied silently.

The closure is a proposal only in this increment. The original claim, ledger,
manifest, reports, contingency and authorization remain untouched. A later live
coordinator must record and enforce the approved succession before dispatch.
An offline manifest is not a spending token.

## Study contract

Use the predecessor's frozen case bank without selecting on new responses:
two development source locators and four evaluation locators, with two projects
in each split. Six operations per locator, two prompt arms, two providers and
one repetition yield 48 + 96 planned calls. The evaluation locators are not
displayed for tuning; prior screening/background exposure remains a limitation.
Do not describe them as contamination-free or count dependent variants as
independent requirements.

Both arms receive identical artifact text, reference, scope and obligations.
V3 retains its original prompt, parser and 120-character quote limit. V4 uses
the PR #45 prompt, segmentation policy and strict artifact-ID parser unchanged.
The different presentation, instructions and response formats are a bundled
intervention. This is not an isolated causal test of quote transcription.

Freeze one 512-output-token allowance for both arms and the existing conservative
input bound of UTF-8 prompt bytes plus 64. Alternate arm and provider order by
case index. Freeze order, exact prompts, provider configuration, prices, source
files, environment, inputs and construction answers before any later collection.
Provider names and private source identifiers do not enter public summaries.

The six operations remain concise complete, distributed complete, long omission,
partial missing, partial complete and partial contradiction. Construction answers
are AI-assisted expectations, not independently established natural-language
truth. No expected answer, split or source join enters either provider prompt.

## Decision rule, defined before responses

A later live development decision requires all 48 planned calls to have verified
receipts. V3 failures remain baseline observations, not repaired successes. For
each provider, v4 must have all 12 responses valid, at least 10/12 exact
obligation-vector matches, and 2/2 exact matches for each of long omission,
partial missing, partial complete and partial contradiction. Evaluation uses
the corresponding 24 valid, at least 20/24 exact and 4/4 named-operation counts.

Exact obligation vectors are stricter than the predecessor's aggregate-match
criterion. This change is prospective: an aggregate omission can conceal a
wrong judgment on another obligation. Report aggregate matches separately for
continuity; never apply the new criterion retrospectively to the old gate.

The offline auditor reports whether supplied records meet the candidate response
rule. It cannot establish verified dispatch, usage or cost and therefore never
reports evaluation or main collection as authorized. Failure retains missing
and invalid denominators. A failed new version ends that comparison; changing
the prompt or criteria is a separate development decision.

## Budget and predecessor custody

Preparation must verify the original manifest integrity, exclusive claim,
parent custody, journal chain, complete failed development and zero evaluation
receipts. Require no pending reservation and no stopped/ambiguous journal.
Regenerate and compare the predecessor's case bank and call plan. Verify that
the baseline prompt/parser and predecessor gate source match their frozen
identities. Reject changed evidence rather than interpreting a handwritten
report as closure permission.

The private proposal itemizes measured predecessor spending, unexecuted direct
reservations and unused contingency. Only a future audited closure may release
the last two, after confirming all measured outcomes are reconciled. Preserve
the parent's spent amount, every remaining parent reservation and its full
contingency, plus the earlier unresolved reservation. Preserve the old claim
and receipts; do not delete, reset, migrate or rewrite them.

The proposed shared amount is parent retained commitments + predecessor measured
spending + earlier unresolved amount + the complete new reserved envelope.
Require it to fit US$7; also require predecessor measured spending plus the new
envelope to fit the existing US$1 auxiliary allowance. Show the all-reservations-
retained alternative, which may exceed the cap. No authority follows from a
passing arithmetic check. Recompute from frozen prices, never rounded display
amounts. A future coordinator must prevent concurrent/repeated successor claims.

## Modules and data flow

`eval/addressed_comparison_plan.py` owns read-only predecessor verification,
matched-call preparation, budget-proposal arithmetic and private plan validation.
Reuse existing provider configuration parsing, pure envelope calculations and
journal inspection. Never instantiate a provider or `PilotLedger` here.

`eval/addressed_comparison_audit.py` owns offline response parsing, denominator
accounting, pairing and safe summaries. Reuse the separate v3/v4 parsers. Input
records bind a call ID and prompt digest to one raw response or explicit missing
response. Reject duplicate, unknown or mismatched observations; do not let them
replace a prior record. Every planned call absent from the input remains missing.

Report planned, observed, valid, invalid, missing, aggregate matches and exact
obligation matches by phase, opaque provider slot, arm, operation and opaque
source group. Paired counts distinguish both matching, only v3, only v4 and
neither; invalid or missing responses cannot disappear through complete-case
filtering. These are descriptive counts, not an independence-based significance
test. Return fixed error categories, never raw exceptions or private identifiers.

`eval/addressed_comparison.py` exposes bounded offline `prepare` and `audit`
commands, with optional private output outside all Git checkouts. There are no
API-key, live, env-file or dispatch options. Read bounded regular JSON files,
reject symlinks and duplicate keys, and create outputs exclusively. Public
stdout contains aggregates only. Private plans contain the necessary custody
and prompt identities. Audit outputs always state `semantic_validity:
not_measured`, `provider_calls_dispatched: 0`, `execution_authorized: false` and
`main_collection_released: false`.

Pure functions and a small CLI are enough. Separate planning and scoring so a
future dispatch coordinator can consume a verified contract without giving
the offline auditor provider credentials or mutable budget ownership. No new
framework, provider abstraction or generic workflow engine is needed.

## Acceptance scenarios

1. Given a preserved failed predecessor, preparation reproduces 144 matched
   planned calls and a budget proposal without changing any predecessor file,
   claim or journal, without displaying evaluation payloads or contacting APIs.
2. Given missing approval, changed custody, an incomplete/ambiguous predecessor,
   a changed baseline, symlink input, malformed bank or over-budget proposal,
   preparation fails before creating an accepted private output.
3. Given supplied valid, invalid and missing responses, the auditor retains all
   planned denominators and separates locator/schema validity, aggregate and
   exact construction agreement, paired outcomes and semantic validity.
4. Given duplicate IDs, wrong prompt identities or unknown observations, reject
   the audit rather than overwriting evidence. Partial-scope blanket abstention
   and aggregate-only agreement cannot establish the required exact-vector
   matches. A real but irrelevant citation remains locator-valid; even matching
   the construction vector does not validate that citation's semantic support.
5. Given a complete toy audit satisfying the prospective response rule, both
   execution flags remain false. CLI tests run with network unavailable and
   verify that raw text, hashes, credentials and paths never reach public output.

## Verification and delivery

Use test-first contract and integration tests with authored fixtures. Run the
focused suite, full repository suite, compilation and existing gates; review
privacy, custody, integer cost arithmetic, SOLID and clean-code boundaries.
Re-run private preparation only as an offline estimate after implementation.
Preserve all historical results and distinguish software verification from
empirical findings. A later paid-run decision requires the final frozen plan,
an enforced succession receipt and explicit collection authorization.
