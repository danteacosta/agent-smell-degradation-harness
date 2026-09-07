# Pilot review hardening

The PR review found two gaps in the stated frozen, valid-response gate. Fix
them without changing historical prompts, private inputs or recorded outcomes.

Acceptance contract:

1. Given a newly frozen run, changing the temporal analyzer must prevent any
   further provider dispatch. Include that analyzer in the source inventory.
2. Given a syntactically valid diagnostic response whose severity contradicts
   its coverage status, count it as invalid and keep the main cohort blocked.
3. Apply the same response contract to final exploratory judging, retaining raw
   responses rather than repairing them. Historical comparison scoring stays
   unchanged and can still report inconsistent pairs explicitly.
4. Existing failed diagnostics and their cost receipts remain byte-identical.

Implementation: regression tests in `tests/test_pilot_runtime.py`, one small
pilot-local response validator and the source inventory in `eval/pilot_runtime.py`.
No new dependency or design pattern is needed. Tests use the existing adapter
fixture to exercise public phase/preflight behavior without network calls.

- [ ] Add failing source-drift and inconsistent-response tests.
- [ ] Run focused tests and confirm the intended failures.
- [ ] Implement the minimal safeguards; rerun focused and full tests.
- [ ] Publish the negative diagnostic result and supersede stale pending text.
- [ ] Review privacy, accounting, SOLID and clean-code boundaries before merge.

Historical private launches continue to require their exact archived source.
This change does not migrate or authorize a new collection.
