# Claude 5.5 replication implementation plan

Goal: repeat the authorized 25-requirement shared-omission experiment with explicit Sonnet 5.5 and Opus 5.5 IDs, preserving all 4.6 evidence.

Architecture: one new versioned orchestration module copies the original frozen prompts and targets, uses the existing tool-free V2 adapter and quota parser, and journals reset continuations. Analysis and browser runner remain unchanged. No mutation of globals or of older collector files.

Acceptance: fresh output only; identical prompt and page hashes; 300 unique model/slot attempts; no retry of failures; zero extra/API use; five-hour consumption allowed, >30% required in every other window; valid new quota qualification and reset+60 seconds before continuation. Invalid/missing quota, model switch, CLI drift or unexplained failure stops. Evaluate saved suites once only after generation completion, with Docker controls qualified.

- [x] Write regression tests for 5.5 identity, fresh packet, quota stop, failure preservation, reset guard and no duplicated slots.
- [x] Implement scripts/claude55_shared_omission.py, reusing immutable analysis, adapter, schedule and quota functions.
- [x] Run focused regressions, syntax, security/clean-code review, and hash checks against earlier collector files.
- [ ] Publish the exploratory protocol and runtime before research generation; qualify Docker controls, freeze packet, launch detached.
- [ ] Monitor through quota resets; report results separately, never relabel 4.6 or approve human audit.

Verification: 38 focused tests passed, including eight audit-workbook tests with spreadsheet dependencies present. Three Docker controls qualified. Independent read-only review identified four quota/journal boundaries; regression tests reproduced them before fixes, then passed, and second review found no remaining launch blocker. Older collector and analysis files remain unchanged.
