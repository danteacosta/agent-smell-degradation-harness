# Expanded evidence-v2 comparison plan

**Goal:** execute the user-authorized larger comparison on previously unqueried
constructed controls, preserving both earlier studies unchanged.

**Architecture:** add one named study to the existing auxiliary runner and
scorer. Keep the historical and evidence-v2 prompts byte-identical. Reuse
provider adapters, parser, private storage policy and fail-closed cost ledger.
No new dependency, primary-protocol change or automatic prompt promotion.

**Execution:** sequential inline implementation and review, without subagents.

## Frozen design

Twelve newly authored templates cover pagination bounds, inactivity expiry,
inventory limits, uniqueness, tenant isolation, consent, ordering, redaction,
transaction rollback, version preconditions, checksums and channel independence.
Each has literal coverage, meaning-preserving paraphrase, one deliberately
deleted condition, and opposite behavior. That is 48 cases, two prompts, two
providers and two repetitions: 384 calls. No old controls are included.
These are new examples of familiar constraint families, not unseen domains.

Keep 96 output tokens, ledger input bound 512, original frozen model/pricing
configuration, seed 20260906, one attempt per occurrence and SDK retries zero.
Freeze code, controls, prompt, order and configuration hashes before calling.
The existing direct envelope plus 25% contingency and conservative ledger
envelope must both fit US$1. No resumption after ambiguous usage.

Primary diagnostic is correct deletion detection out of 24 planned occurrences
per configuration (12 templates, two repetitions). Report false alarms on 48
complete/paraphrased occurrences, contradiction detection, schema failures,
abstention, inconsistent labels, missingness and literal evidence grounding.
Counts are descriptive; repetitions are not independent samples. Compare arms
on the same templates and do not pool the old comparison or small smoke.
No human calibration, natural-artifact validity or H1/H2 claim follows.

## ATDD / BDD and verification

- [x] Given the new study, preflight produces 384 calls without network I/O,
      uses only historical/evidence-v2 arms, and freezes budgets below US$1.
- [x] Given the new pack, all 48 identifiers and reference texts are disjoint
      from previous packs; each template has two positive and two negative cases.
- [x] Given constant clean predictions, omissions fail; given constant omitted
      predictions, complete cases produce false alarms. Missing denominators
      remain 96 per arm/provider and 24 per operation.
- [x] Given an injected provider, all 384 occurrences persist privately; given
      missing usage, stop without retry and preserve the remaining denominator.
- [x] Run new tests red, implement named-study selection, run targeted and full
      offline verification, review privacy/cost/SOLID and commit before live use.
- [x] Execute one live run; preserve all failures and report planned denominators.
- [x] Prepare aggregate results for PR #41; keep account balances and raw data private.

## Earlier-call reconciliation and account checks

The old ledger remains terminal and unchanged. Its ambiguous attempt has no
persisted provider request/response identifier or usage. The available OpenAI
key receives HTTP 403 from the official organization-cost endpoint; no admin
key is present and the available browser session requires login. Thus exact
reconciliation cannot currently be established. Keep its US$0.000218 reserved;
do not substitute an estimate for observed usage or replay the occurrence.
The new study is independent and does not release that reservation.

DeepSeek's official balance endpoint can report available account credit.
The OpenAI costs endpoint reports expenditure rather than prepaid credit.
Account balances stay private and are not a study outcome. Sources and limits
are recorded in [the account-check note](2026-09-06-provider-account-checks.md).

## Pre-collection verification

Four new behavioral tests failed before implementation. After implementation,
23 focused tests and the full local suite passed: 872 passed, seven skipped,
nine subtests passed. Eval, gates, compile and diff checks passed. Offline
rescoring still exactly reproduces both prior reports. The direct envelope is
US$0.466610; the conservative ledger envelope is US$0.832032. Neither amount
is an observed charge. Private records retain any unresolved earlier liability.

Review: the change adds constructed data and explicit study selection only.
Provider, cost, secret-loading and historical prompt contracts are unchanged.
No new framework, duplicate cost policy or external side effect is introduced
outside the existing live path. Constant-answer and missing-usage regressions
cover the key diagnostic and stopping boundaries. Remaining limitations are
authored construction oracles, known constraint families and no human calibration.

## Collection checkpoint

The [expanded result](judge-v2-expanded-results.md) records 384/384 completed
calls at US$0.052009, with no invalid/missing response or unresolved cost in
this run. The earlier ambiguous attempt remains an external-evidence dependency.
