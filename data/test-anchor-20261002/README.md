# Test-anchor experiment, 2 October 2026

81 new Astra tester calls produced 81 valid suites. Those suites were applied to 36 existing A/C interfaces (three requirements/projects), giving 180 browser evaluations. The original result includes a known runner defect: only root navigation was served, so RealWorld profile navigation failed. A separately identified browser-only diagnostic corrects the origin boundary and replays the same suites and interfaces, with zero further LLM calls.

- [Frozen original results](frozen-original/results.json) and [all original reports](frozen-original/reports/).
- [Post hoc diagnostic results](origin-diagnostic/results.json) and [all diagnostic reports](origin-diagnostic/reports/).
- [81 generated suites](suites/), [schedule](schedule.json), [frozen prompt hashes](frozen-hashes.json), [control outcomes](controls/), [custody](custody.json), and [public file receipt](receipt.json).
- [Interpretation and limitations](../../docs/research/2026-10-02-test-anchor-results.md).

Diagnostic target detection: implementation + received request 0/11; implementation + complete reference 11/11; complete reference + scaffold 33/33 (three evaluations of each of the same 11 failures). The last strategy's Paperless alarms are timeouts, separately identified from assertions. Remaining RealWorld alarms test Bob while the qualified scaffold is fixed to Alice, so they are out of scope relative to the target oracle. The original and diagnostic totals must stay separate. This is exploratory and does not confirm H1 or H2.
