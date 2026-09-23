# Bounded persistence collection

Goal: execute the 18 previously frozen requests once, preserving every absence,
raw response (transport capture limited to 2 MB per stream with truncation metadata), browser report and screenshot. This is a single-intent exploratory
second-page visible-edit endpoint, not cross-project H1/H2 confirmation.

## Accepted design

Reuse CodexCLIProvider, bounded raw HTML admission, persistence_executor and the
fixed-denominator behavioral analyzer. A small separate collector owns custody
and dispatch; the provider owns subscription auth and fresh empty contexts; the
qualified offline browser owns endpoint observations. No generalized framework.
Use the frozen PR72 packet as immutable parent; never replace its receipts.
Freeze executable, provider/collector/runtime bytes and qualification before any
experimental call. Use a fresh execution packet, immutable run-start marker,
sequential randomized 18-slot order, two unchanged model labels, low effort,
180-second timeout, no resume/retry/repair/API-key fallback. Internal transport
retries and model snapshots are not observable. Do not call the model to diagnose
an experimental response. Capacity check is preflight evidence, not a quota guarantee.
All generation ends before any generated HTML is executed or outcomes reviewed.

Alternatives: adapting the old Escape collector would mix its scaffold and
endpoint semantics; a generic multi-endpoint collector is premature while only
persistence is admitted. A narrow collector with existing adapters is preferred.

## ATDD / BDD contracts

1. Given a hash-verified admitted packet and runtime, when prepared, the successor
   preserves all 18 exact prompts/order and freezes executable/config/code before
   dispatch. Drift, unsafe links, existing destinations or failed preflight reject.
2. Given 18 slots, when collected, each gets at most one call and a fresh empty
   context; only its exact prompt enters the generator. Shared user config,
   project instructions, tools, paired alternatives and oracle are excluded.
3. Given invalid HTML output, preserve it as unknown and continue; given provider failure,
   stop dispatch and preserve remaining slots as unattempted. Interruption leaves
   a durable attempted marker and forbids resume. Never replace evidence.
4. Given complete generation, execute valid HTML offline with the exact qualified
   image, preserving reports/screenshots. Unknown and missing remain unknown;
   target-only, non-target, mixed and null outcomes all remain in analysis.
5. Given rerun or drift, reject before provider invocation. No key fallback or
   quota reset. Source/prompt and oracle admission remain unchanged.

## Implementation and verification

- [x] Baseline provider, persistence and analysis tests.
- [x] Add tests/test_persistence_collection.py: exact prompt/ordering, no execution
      until generation ends, invalid/provider-error missingness, duplicate run,
      frozen/executable drift, durable interruption evidence.
- [x] Run new tests red, implement scripts/persistence_collection.py, run green.
- [x] Use fake CLI integration to prove separate empty cwd, sanitized environment,
      required isolation flags, prompt-only stdin and no resume command.
- [x] Review implementation for security, SOLID, clean code and evidence custody.
- [x] Freeze a successor private packet; verify CLI help/auth, capacity and image.
- [x] Execute one bounded collection; classify and visually inspect evidence.
- [ ] Publish precise methods/results, update Drive/slides and merge after CI.

Verification: pytest tests/test_codex_cli.py tests/test_persistence_collection.py
 tests/test_persistence_executor.py tests/test_behavioral_expansion_analysis.py;
 git diff --check; full CI. Browser qualification remains the 9-control frozen
 PR72 packet; actual generated HTML must go through the same offline executor.

Frozen output rule: UTF-8 response <=200000 bytes; after outer whitespace only, starts with <!doctype html or <html (case-insensitive) and ends with </html>. No Markdown unwrapping, JSON extraction, repair or normalization of the stored artifact. This is an artifact-interface admission rule, not a functional correctness test. Immutable fsynced run-start and per-slot attempt records precede calls.

Preflight evidence: Python 3.14 environment selected because baseline imports require >=3.11; 55 focused tests passed. CLI 0.155.0-alpha.9.2 explicitly selected (system CLI 0.3.0 excluded). Two separate nonexperimental availability calls returned READY for the frozen model labels with distinct thread IDs. No tools occurred. Review required durable directory links; regression test fails on unavailable fsync before any provider call.

Execution checkpoint: all 18 scheduled calls completed with valid raw HTML and no provider stop; E2E execution follows only after the immutable collection boundary. CI for collector commit 74d1599 passed all six checks, including 1,774 tests, 12 skips and nine subtests.

Final execution: 18 valid HTML, 13 target passes, zero target failures, five unknowns. Visual/source audit identified four span-labelled visible rows unrecognized by the frozen selector; preserve their unknown labels, not a persistence-defect claim. 52 PNGs total, including one partial set.
