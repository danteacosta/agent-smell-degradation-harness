# Scoped evaluator development study

## Decision and scope

The user approved continuing the separately versioned v3 design after the failed
96-call diagnostic. This is auxiliary instrument development, not a restart of
that frozen launch or authorization to generate the main cohort. No H1/H2
estimate, human-validity claim or automatic semantic approval follows.

The observed v2 failure combines partial-context overcalling with format errors.
The proposed intervention bundles explicit observation scope, an obligation
inventory and per-obligation evidence. A comparison cannot attribute a gain to
one of those changes alone. Both arms receive the same artifact/reference and
scope information, and the same 512-token output allowance. The historical v2
prompt and all historical responses remain unchanged.

## Acceptance contract (BDD)

1. Given a complete artifact, the evaluator distinguishes a missing obligation
   from supported coverage. Given a partial artifact, missing support permits
   uncertainty; explicit contradiction remains an omission and fully visible
   support remains coverage. Scope must not determine the answer by itself.
2. Given a response, every frozen obligation ID occurs exactly once. Unknown,
   missing, duplicate, ungrounded or malformed entries are invalid, not repaired.
   Aggregation is deterministic: any omitted obligation dominates, then uncertain,
   otherwise covered. This validates the response contract, not entailment.
3. Given a private source case, the provider receives only the reference,
   artifact, scope and required obligation inventory. Expected statuses, source
   identities, development/evaluation membership and transformation joins remain
   in the private label plane.
4. Given an explicit paid-call plan, dispatch is sequential, one attempt only,
   with durable reservation and raw observation before cost reconciliation. A
   changed source/input/environment or ambiguous cost stops before another call.
   Completed calls can be replayed locally without purchase.
5. Given a failed or incomplete development gate, evaluation stays locked. A
   completed evaluation never unlocks the original pilot. Both validity and
   correct/planned counts retain all failed and missing denominators.

## Frozen study design

- Development: two previously used source controls, one per source project.
- Evaluation: four source locators not previously used as target controls in the
  failed diagnostic, two per project. They may have appeared in screening or
  background text. This is not pristine held-out data or pretraining isolation.
- Six operations per locator: concise complete; distributed complete with source
  context; long omission; partial missing; partial complete; partial contradiction.
- Two arms, two providers, one repetition: 48 development + 96 evaluation calls.
- Cases and construction oracles are frozen together before either phase.
  No tuning between development and evaluation. Failure ends this study version.
- Development gate per provider for v3: all 12 calls valid, at least 10/12 exact
  aggregate matches, both omissions detected, both partial-missing cases uncertain,
  both partial-complete cases covered, and both partial contradictions detected.
  Evaluation uses the analogous threshold
  of at least 20/24 exact matches, all 24 valid, and 4/4 for each named operation.
- Report per operation, provider and source unit; do not pool dependent cases as
  independent requirements. Report per-obligation v3 matches separately.
- Natural-language source transformations and construction oracles are AI-assisted
  and lack independent human validation. Formal response checks do not cure this.

## Implementation and boundaries

`label_plane/scoped_judge.py` owns pure prompt construction and response scoring.
`eval/scoped_judge_study.py` owns frozen preparation, custody, budget, phase gates
and collection. Reuse the existing provider Adapter and durable PilotLedger;
do not add a new provider abstraction or change the legacy pilot runtime.

The auxiliary reserved envelope is at most US$1 and must fit **inside** the
existing US$7 pilot envelope, including already measured spending, the remaining
main plan and its contingency. The failed parent ledger is held read-only under
its existing lock during collection; its bytes/hash must remain unchanged. No
reset, migration, hidden retry, top-up or new spending authority is implied.

## Verification and delivery

Test pure schema/aggregation and boundary contracts first, then fake-provider
integration for freeze, budget, incomplete responses, resume and phase gates.
Run focused tests, full repository checks where feasible, compile, diff review,
security/cost review and clean-code/SOLID review. Freeze source hashes and the
environment before paid calls. Publish only redacted aggregate findings and
limitations; update the proposal/report/slides and retain private evidence.
