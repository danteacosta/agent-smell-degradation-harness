# Language review export implementation plan

**Goal:** Reproduce the corrected first-reading packet from versioned source.
**Architecture:** One offline module selects original texts into cluster-isolated
forms and writes reviewer/custodian artifacts with a completion receipt.
**Tech stack:** Python standard library, pytest, existing policy inventory.

- [x] Add `tests/test_language_review.py` acceptance tests for one text per
  cluster, balanced coverage, exact prompts, hidden custody fields, empty human
  fields, matching Markdown/JSON, deterministic output and receipt integrity.
  Add overwrite/symlink and command-line behavior tests. Run the file and observe
  the missing exporter fail before implementing.
- [x] Implement `eval/language_review.py` with `export_review(output, seed=...)`
  and `main()`. Build supported six-form assignments in memory; validate the
  fixed profile shape before creating a new directory. Write `forms/`,
  `custodian/`, root instructions and a last-written receipt. Never read results.
- [x] Run the new tests plus language_controls and annotation_charter tests,
  compile the module and run diff checks. Export one real private bundle and
  independently verify its hashes, form membership and exact original texts.
- [x] Document the command and distribution rule in README; update the current
  master’s status and old completion checkpoint with the final exports and
  remaining scientific gates. Keep historic evidence clearly labeled.
- [ ] Review implementation and docs, open a PR, await native CI, and merge only
  the reviewed green head. Record the new packet location and remaining human
  prerequisites in the operational Drive report.

Verification command:
`/private/tmp/masters-review-venv/bin/python -m pytest tests/test_language_review.py tests/test_language_controls.py tests/test_annotation_charter.py -q`

## Local verification record

The new acceptance tests first failed because the exporter did not exist.
The implemented exporter passed 42 focused tests covering review forms,
language controls, annotation charter and existing draft packets; compilation
and diff checks passed. Independent implementation review found no blockers.
A real private export contained six four-item forms and ten unique prompts;
all 15 receipt hashes, cluster isolation and exact source texts were rederived.
Receipt SHA-256: `c7e3a93c93ac85fba81e38e401533012ddc039b6ec08f0250a3f776eb7019c9b`.
No participants, human labels, distribution or model calls resulted from export.
