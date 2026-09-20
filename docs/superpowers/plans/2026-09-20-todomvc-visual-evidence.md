# TodoMVC Visual Evidence Implementation Plan

**Goal:** Preserve auditable screenshots and video for both arms of the manual
TodoMVC Escape rehearsal without changing its oracle or admission gate.

**Architecture:** Extend the existing runner with optional per-arm media capture;
use a separate Cypress support hook and explicit video configuration. Keep the
native test suite and targeted-failure classification unchanged.

**Tech Stack:** Python, pytest, Cypress/Electron, GitHub Actions.

## Tasks

- [ ] Review the design and plan against actual runner and upstream support files.
- [ ] Add failing subprocess regression tests in
  `tests/test_todomvc_escape_qualification.py`: preserve different gold/mutant
  bytes from repeated paths; reject stale/symlink inputs; distinguish missing
  visual evidence from a valid behavioral result.
- [ ] Run `/private/tmp/pr58-fix-venv/bin/python -m pytest
  tests/test_todomvc_escape_qualification.py -q` and verify expected failures.
- [ ] Implement the minimum optional capture in
  `eval/todomvc_escape_qualification.py`, with hashes and safe relative paths.
- [ ] Add `eval/fixtures/todomvc-visual-support.js`, importing the actual upstream
  support entrypoint and taking a viewport screenshot after the Escape test.
- [ ] Update `.github/workflows/todomvc-oracle-qualification.yml` to copy the
  wrapper, enable video, request capture and upload the complete evidence tree.
- [ ] Re-run focused tests, compilation and diff checks. Review correctness,
  path safety, per-arm isolation, error reporting, SOLID and clean code.
- [ ] Open a PR; run native Cypress and full CI. Preserve all arm media, inspect
  the screenshots, verify video metadata and hashes. Merge only the reviewed
  green head, under the user's continuing merge authorization.
- [ ] Record the fresh run in the research dossier, Drive report and slide notes;
  export current deliverables. Keep older qualification receipts historical.

The three-requirement provider pilot remains separate from this plan. It must
either satisfy existing independent-review admission or receive explicit user
direction for a separately labelled exploratory study; no gate is bypassed by
this media change.
