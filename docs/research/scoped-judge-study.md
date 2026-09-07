# Scope-aware evaluator study

This auxiliary study investigates the failed [source diagnostic](source-diagnostic-results.md).
It does not revise that run, supply independent human labels or release the main
pilot. The [frozen design](../plans/2026-09-07-scoped-judge-study.md) specifies the
comparison and decision rules before collection.

The [completed development result](scoped-judge-results.md) failed the frozen
gate after 48 calls. Evaluation remains uncollected; the study is not a passing
qualification of either provider.

## What changes

The v2 comparator retains its prompt and receives explicit observation-scope
metadata. V3 adds scope semantics and an obligation inventory, then asks for a
short evidence excerpt per obligation. Both arms use the same 512-token response
allowance. This is a **bundled intervention**, not an isolated test of one prompt
sentence. Agreement with construction oracles does not demonstrate entailment
or human-label validity.

The six operations include complete and incomplete observations. A partial
observation can support coverage, reveal a contradiction, or leave an obligation
unresolved. This prevents a rule that always abstains on partial context from
passing the gate.

## Execution contract

The private bank freezes two development sources and four evaluation sources,
with two projects represented in each split. Six operations, two arms and two
providers yield 48 development and 96 evaluation calls. There is one repetition;
dependent cases are not counted as independent requirements. Evaluation source
locators were not target controls in the failed diagnostic, but may have appeared
in screening or background context. They are not pristine held-out data.

Run `python -m eval.scoped_judge_study --help` for the private operator interface.
Preparation requires explicit approval, the preserved failed parent launch and
private source seeds. It freezes source hashes, installed-package versions,
prices, requests, oracles and the complete call plan before creating a ledger.

The auxiliary envelope is capped at US$1 **within** the existing US$7 pilot cap.
Accounting retains the parent's measured spending, remaining reservations and
full contingency, plus the earlier US$0.000218 unresolved reservation. A separate
exclusive claim prevents accidentally starting another auxiliary budget against
the same parent. Collection holds the parent's existing lock without rewriting
its journal. Missing or changed custody, an unresolved reservation or unverified
usage stops dispatch. There are no hidden SDK retries.

The evaluation phase recomputes the development gate from preserved responses.
A handwritten report cannot unlock it. Even a passing evaluation reports
`main_pilot_released: false`; a later main launch needs its own explicit decision
and frozen configuration. Invalid outputs remain invalid and count against the
gate rather than being repaired after collection.

## Review before collection

The implementation separates pure label-plane behavior from provider/ledger
orchestration and reuses the existing provider Adapter and journal. Focused tests
cover schema identity, literal evidence, scope controls, parent custody, shared
budget, phase locking and no-repurchase resume. The review also caught a parent
hash-format mismatch: parent launch integrity uses canonical JSON, while private
file custody uses byte hashes. A regression now preserves that distinction.

The technical review is AI-assisted, not an independent human methodological
approval. The source-to-obligation mapping and the construction oracles remain
AI-assisted limitations. Results must report valid/planned and correct/planned
denominators by operation and provider, with source-unit dependence disclosed.
