# Artifact-addressed evidence implementation plan

> For agentic workers: use superpowers:executing-plans inline. Do not dispatch
> subagents; the user requested constrained memory use.

Goal: resolve experimental judge citations to exact artifact spans and report
software integrity without claiming semantic validity or releasing collection.

Architecture: three modules isolate snapshot identity, judge-response validation,
and aggregate offline reporting; a small shared JSON reader avoids duplicate
parsing policy. Existing frozen v2/v3 code, ledgers,
features, budget gates, and provider adapters remain unchanged.

Tech stack: Python standard library, pytest, the existing pinned runtime.
No new dependency, network client, browser, or background worker.

Approved [specification](../specs/2026-09-07-evidence-addressing-design.md).
Inline review found no unresolved design issue; it does not count as independent
review. Execute the batches below with fresh verification at each checkpoint.

## 1. Version-bound artifact spans

Files: create `label_plane/artifact_segments.py` and
`tests/test_artifact_segments.py`.

- [x] Write behavior tests for deterministic Unicode/CRLF round trips,
  repeated spans, long lines, stale IDs, snapshot tampering, field types, input
  bounds, and exact byte ranges.
- [x] Run `python -m pytest -q tests/test_artifact_segments.py`; confirm missing
  functionality fails before implementation.
- [x] Implement `build_snapshot(text)`, `validate_snapshot(snapshot)`, and
  `resolve_segments(snapshot, ids)`. Preserve source bytes; recompute the
  canonical snapshot before accepting serialized input. Use bounded inputs and
  fixed error codes, never private text in errors.
- [x] Re-run the focused tests and inspect the public API for unnecessary
  abstraction. No filesystem or network dependency belongs in this module.

## 2. Experimental addressed judge

Files: create `label_plane/addressed_judge.py` and
`tests/test_addressed_judge.py`.

- [x] Write failing tests for artifact-only prompt fields, multi-span evidence,
  every obligation, strict JSON and citation validation, empty covered evidence,
  and an irrelevant real citation that remains semantically unvalidated.
- [x] Run `python -m pytest -q tests/test_addressed_judge.py` and observe failure.
- [x] Implement `build_prompt(item)` and `parse_response(raw, item)`. Reuse the
  existing item/aggregation semantics without editing the frozen module. Check
  all bounded field types before membership operations. Output resolved spans
  privately and explicit `locator_integrity` / `semantic_validity` fields.
- [x] Run new and historical scoped-judge tests. Ensure no quote repair or
  retroactive v3 score changes occur.

## 3. Redacted offline audit

Files: create `eval/evidence_addressing.py` and
`tests/test_evidence_addressing.py`.

- [x] Write failing integration tests for mixed valid/invalid/unlabeled inputs,
  construction-label denominators, missing responses, invalid envelopes, exact
  redaction, bounded CLI inputs, and the toy command's exit behavior.
- [x] Implement `summarize(records)` and `python -m eval.evidence_addressing`.
  Input records contain only `item`, `raw_response`, and optional
  `expected_checks`. Never dispatch providers. Malformed cases remain in the
  attempted denominator; unavailable semantic validity is not zero accuracy.
- [x] Support mutually exclusive `--demo` or `--input PRIVATE_JSON`; read
  bounded JSON input and print aggregate JSON only. There is no file writer,
  provider mode, launch override, or implicit repair.
- [x] Re-run integration and full tests, checking privacy and cost boundaries.

## 4. Documentation and delivery

- [x] Add `docs/research/artifact-addressed-evidence.md` with exact contracts,
  commands, bounds, interpretation, and a natural-language-validity caveat.
- [x] Reconcile README, annotation-free guidance, results links, literature
  catalog, product boundary, roadmap, and `tasks/todo.md` without changing
  historical result counts or raw evidence.
- [x] Run full pytest, compileall, eval and gates, wedge and replay fixtures;
  review the full diff for ATDD, SOLID, clean code, privacy, and leakage.
- [x] Update the research report in Drive through a revision-guarded native
  edit, preserving structure and verifying changed text/styles.
- [ ] Commit verified changes and publish a reviewable PR. Do not merge this
  new experiment interface or run paid calls as an automatic side effect.

Verification commands use the existing runtime interpreter. The acceptance
contract is observable behavior; test totals are engineering evidence only.

## Local verification record

The initial snapshot, judge, and report batches failed before implementation
(35, 32, and 26 tests). All 93 passed after implementation. Two supplementary
boundary tests cover unavailable networking and the distinction between a valid
software response and construction disagreement. The focused total is 95.
The final full suite passed 1,053 tests, with 7 skipped and 9 subtests passed.
Compilation, eval, gates, wedge fixtures, and replay exit codes 0/20 passed.
No project linter/typechecker is configured.

The frozen scientific runtime lacks `setuptools`; it was not modified. A wheel
was built offline with the already available auxiliary Python 3.12 toolchain,
without dependency installation. The report's four targeted native text edits
were read back with unchanged paragraph roles and 12-point text. This narrow
text edit did not include a new PDF visual review.

Inline implementation review: no blocking finding in the approved contract,
use-case coverage, test isolation, privacy/cost boundary, or SOLID/clean-code
structure. Shared strict JSON parsing removed duplicated policy. Advisory limits:
real irrelevant citations can pass; no provider validity or study-completion
claim follows from this audit; the evidence presentation needs a separate
experimental freeze. No independent review or human calibration is claimed.
