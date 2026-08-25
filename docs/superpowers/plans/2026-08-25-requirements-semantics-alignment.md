# Requirements-semantics alignment implementation plan

> **Execution:** implement directly in the current checkout, using the
> repository's existing pytest suite as the regression harness.

## 1. Add the shared conditional-semantics contract

**Files:** `protocol/conditional_semantics.py`, `tests/test_conditional_semantics.py`

- Write tests for a valid item, empty list, invalid enum, invalid negative case,
  unknown/terminal key, and empty text before finalizing the implementation.
- Run the focused tests and use the failures to drive the validator contract.
- Implement the validator and schema-version constant with deterministic
  normalization and useful error paths.
- Run the focused tests again.

## 2. Thread the contract through T1/runtime/replay

**Files:** `agents/checkpoints.py`, `agents/staged_runtime.py`, `agents/live.py`,
`agents/runtime.py`, `replay/schema.py`, `replay/integrations.py`, related tests

- Add the additive field to T1 allowlists and normalize legacy payloads.
- Add an explicit `require_conditional_semantics` option for the confirmatory
  staged-provider path without breaking generic legacy fixtures.
- Update provider prompts and diagnostics; preserve the terminal-data rejection.
- Reuse the shared validator in replay and vendor adapters.
- Add/adjust BDD-style tests for legacy normalization, valid provider output,
  malformed output, and prompt/diagnostic observables.

## 3. Extend confirmatory metadata without feature leakage

**Files:** `data/confirmatory/schema.json`, `data/confirmatory/manifest.json`,
`label_plane/datasets.py`, `eval/prepilot.py`, dataset tests

- Add required project-domain, lifecycle, and source conditional-semantics
  fields to the source-record schema.
- Update the development seed and test builders with explicit metadata.
- Validate the fields at the dataset boundary and retain them only as metadata.
- Add a regression test showing metadata is not admitted as deployable feature
  content.

## 4. Align thesis and ARP documentation

**Files:** `docs/thesis/masters-scope.md`, `docs/thesis/preregistration.md`,
`docs/thesis/data_dictionary.md`, `agent-reliability-protocol/docs/profiles/agent-smell-degradation-v1.md`

- Explain context dependence and the non-causal, perception-based role of
  smell evidence.
- Add the conditional-semantic fields, domain/lifecycle heterogeneity, and the
  no-leakage boundary to the data contract and preregistration.
- Add the two related-work references already inserted in the proposal.
- Keep ARP core event definitions unchanged and update only the thesis profile.

## 5. Verify, review, and publish

- Run focused tests, then the full pytest suite.
- Review the diff for SOLID/clean-code issues and confirm no generic repository
  was changed.
- Check repository status, commit the two repositories separately, push the
  commits, and verify the remote branch and changed-file list.
