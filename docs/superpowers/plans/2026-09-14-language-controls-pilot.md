# Language controls pilot implementation plan

**Goal:** Add and qualify a bounded original-policy profile that distinguishes
ambiguous interpretation from meaning-preserving rewriting.

**Architecture:** A pure case inventory feeds the existing subscription-only
runner. Intended and alternative behavioral reports stay in private evidence;
the provider receives only one prompt. No new execution or provider adapter.

**Tech stack:** Python, pytest, existing native Linux Docker executor, Codex CLI.

## Tasks

- [x] Add public-contract tests in `tests/test_language_controls.py`: truth-table
  coverage and twin prompt identity, safe profile rejection before side effects,
  preparation freeze, hidden metadata, both intended/alternative reporting,
  provider failure stops dispatch while retaining the planned denominator.
  Run `/private/tmp/masters-review-venv/bin/python -m pytest tests/test_language_controls.py -q`
  and confirm the new behavior is absent.
- [x] Add `eval/language_controls.py` for six reviewed original policies and
  exhaustive Boolean/small-integer test domains. Extend `prepare` and `run` in
  `eval/codex_demo.py` with keyword `profile`, default `omission_v1`, and CLI
  choices. Preserve omission behavior and schema; the new profile gets its own
  scope/schema, family/role/cluster metadata and explicit rewritten-arm label.
- [x] Store alternative execution reports and interpretation classification
  without changing intended outcomes or exposing alternative metadata to the
  provider. Keep controls separate in descriptive output. On a provider error
  preserve the attempted episode and all remaining not-executed planned rows.
- [x] Run the new tests plus `tests/test_codex_demo.py`, `tests/test_codex_cli.py`
  and behavior-pair analyzer tests. Review code for narrow responsibilities,
  hidden input leakage, error accounting, and regression of the existing lane.
- [x] Qualify the real isolated executor and run exactly two repetitions of
  each variant (24 episodes) using the approved local Codex model. No API-key
  fallback or replacement of failed episodes. Stop dispatching by 21:08 UTC.
- [x] Verify file hashes and rederive family/variant/interpretation counts;
  record a separate exploratory result and update the proposal/report/slides.
  Open a reviewable PR with exact validation and limitations. Do not merge a
  failing or unreviewed head merely to fit the time window.

## Verified execution record

Completed 24/24 episodes; the real executor qualified before dispatch. All
142 receipt files, four source hashes and 24 prompts passed independent
recomputation. A second assistant checked the raw evidence and interpretation.
The [result report](../../research/codex-language-controls-results-20260914.md)
preserves null controls and twin dependence. Proposal and operational report
were updated in place, with prior text preserved; both native slide decks
received three editable slides each, including the pronoun comparison.
Structural checks reported no errors and only two unchanged decorative-arrow
warnings per deck. New slides were visually inspected. Native PDF export
succeeded through the raw-file fetch path; the final visual and meeting decks
contain 13 and 14 slides respectively, with matching PowerPoint exports.
PR55 merged as `e2b578d05ff358a3f13a41c14906080b2a903f9a` after CI passed
(1,436 tests plus nine subtests); the post-merge main evaluation also passed.
