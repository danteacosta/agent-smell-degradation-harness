# Source-based exploratory pilot preparation

The approved design moves evaluation to real sources. This task prepares an
offline package for the week of 7–13 September; it does not collect paid data.
The 12-intent pre-pilot and its private results remain immutable.

## Acceptance contract

1. Given source-pinned candidates, preparation accepts exactly 24 distinct intent
   IDs in at least six projects, rejects duplicate source locators/text, verifies
   text hashes and records outstanding reviews without inventing approval.
2. Given historical judge evidence, sampling uses project, text length and
   reference-obligation count, never previous labels. Old responses remain in a
   private sidecar; changing them cannot change selected inputs.
3. Given a source-derived control specification, materialization preserves all
   non-target obligations, records the exact deletion and source context, and
   separates expected responses from provider requests. Ambiguity is auxiliary.
4. Given the frozen prices, call counts distinguish intents, base episodes,
   provider trajectories and judgments. Costs include both providers, duplicates,
   controls, natural re-evaluation and contingency. Over-budget plans stay blocked.
5. Given missing admission, approval or runtime support, the readiness report
   remains no-go. Producing a package must not imply permission to launch.

## Implementation sequence

- Add behavior tests first for data validation, label-blind selection, control
  transformations, budget arithmetic and fail-closed readiness.
- Implement a small offline preparation module. Reuse judge request validation,
  v2 rendering and private-output creation; do not relax pre-pilot schemas.
- Curate 12 additional source intents, retaining source context and exact edits.
  Store private material outside Git; publish only protocol and redacted status.
- Materialize a natural sample and controls before collecting any new responses.
- Write the pilot protocol, admission/authorization checklist and operator guide.
- Run focused and full tests, compile checks, privacy review and diff review.

## Design boundaries

Preparation owns deterministic data transformations and budget planning, not
provider execution or authorization. No new design pattern is needed. Existing
provider adapters and fail-closed accounting stay unchanged. A separate pilot
runtime is required because the existing ledger and runner encode 12 intents and
1,296 calls; a document or changed count cannot safely authorize 24 intents.

Natural re-evaluation measures label changes, not correctness. Repeated identical
texts are clustered and their historical occurrence labels retained. This sample
is not suitable for estimating episode-weighted prevalence. Source controls use
constructed oracles, not human ground truth. CASS records disclose the source's
own AI-assisted authorship. No data from these six projects becomes a previously
unseen confirmatory test set.

## Verification

Run `python -m pytest -q tests/test_pilot_preparation.py`, the complete pytest
suite, `python -m compileall -q eval label_plane`, and `git diff --check`.
An offline generated report must record zero provider calls. Review public files
for private texts, provider keys, private hashes and experiment identities.
