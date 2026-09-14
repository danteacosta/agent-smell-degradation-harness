# Language controls pilot implementation plan

**Goal:** Add and qualify a bounded original-policy profile that distinguishes
ambiguous interpretation from meaning-preserving rewriting.

**Architecture:** A pure case inventory feeds the existing subscription-only
runner. Intended and alternative behavioral reports stay in private evidence;
the provider receives only one prompt. No new execution or provider adapter.

**Tech stack:** Python, pytest, existing native Linux Docker executor, Codex CLI.

## Tasks

- [ ] Add public-contract tests in `tests/test_language_controls.py`: truth-table
  coverage and twin prompt identity, safe profile rejection before side effects,
  preparation freeze, hidden metadata, both intended/alternative reporting,
  provider failure stops dispatch while retaining the planned denominator.
  Run `/private/tmp/masters-review-venv/bin/python -m pytest tests/test_language_controls.py -q`
  and confirm the new behavior is absent.
- [ ] Add `eval/language_controls.py` for six reviewed original policies and
  exhaustive Boolean/small-integer test domains. Extend `prepare` and `run` in
  `eval/codex_demo.py` with keyword `profile`, default `omission_v1`, and CLI
  choices. Preserve omission behavior and schema; the new profile gets its own
  scope/schema, family/role/cluster metadata and explicit rewritten-arm label.
- [ ] Store alternative execution reports and interpretation classification
  without changing intended outcomes or exposing alternative metadata to the
  provider. Keep controls separate in descriptive output. On a provider error
  preserve the attempted episode and all remaining not-executed planned rows.
- [ ] Run the new tests plus `tests/test_codex_demo.py`, `tests/test_codex_cli.py`
  and behavior-pair analyzer tests. Review code for narrow responsibilities,
  hidden input leakage, error accounting, and regression of the existing lane.
- [ ] Qualify the real isolated executor and run exactly two repetitions of
  each variant (24 episodes) using the approved local Codex model. No API-key
  fallback or replacement of failed episodes. Stop dispatching by 21:08 UTC.
- [ ] Verify file hashes and rederive family/variant/interpretation counts;
  record a separate exploratory result and update the proposal/report/slides.
  Open a reviewable PR with exact validation and limitations. Do not merge a
  failing or unreviewed head merely to fit the time window.
