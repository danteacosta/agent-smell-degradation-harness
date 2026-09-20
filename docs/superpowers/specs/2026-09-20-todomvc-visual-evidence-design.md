# TodoMVC visual evidence

The user requested visual proof of the existing manual-fault E2E rehearsal and
the next requirement-to-generated-code comparison. This first change preserves
native browser media for the already-qualified reference/manual-mutant pair.
Provider generation is a separate scientific decision; this change does not
alter repository admission or create human approvals.

## Observable contract

- Given the frozen TodoMVC reference and identical Cypress command, when the
  existing qualification runs, both arms retain their own browser video.
- The Escape test produces a viewport screenshot after its interaction in both
  arms. The normal Cypress failure screenshot is retained as additional evidence.
- Before the second run can clear Cypress output directories, the first arm's
  media is copied into its immutable evidence subdirectory and hashed.
- The receipt records relative media paths, sizes and SHA-256 hashes. A missing
  or unsafe media artifact cannot be presented as successful visual capture.
- Gold-pass and targeted-mutant-failure criteria are unchanged. Missing visual
  evidence is separate from behavioral qualification; the CI additionally
  requires visual completeness. Old callers without capture remain compatible.
- The exact original oracle bytes remain unchanged; an additional support hook
  takes the Escape screenshot without replacing assertions or swallowing errors.

## Design

`eval/todomvc_escape_qualification.py` gains an opt-in media capture flag. Its
runner copies only fresh, regular PNG/MP4 files from the configured fixed Cypress
directories, rejects symlinks, and records each arm's media before the next run.
Fresh output directories are required before execution; no unrelated files are
deleted. The receipt includes visual status and per-arm media manifests.

A small Cypress support wrapper imports the original support module, adds an
afterEach hook scoped to the exact Escape test, and captures the viewport. It is
copied into the frozen checkout by CI and its bytes are bound in the receipt.
Cypress video is explicitly enabled. Neither the oracle nor application logic
is edited for visual capture. Native CI is the acceptance test for PNG/video
creation and unchanged 28-pass/one-targeted-failure behavior.

No new design pattern is needed: file collection belongs to the existing runner,
and the support hook isolates capture from the behavioral oracle.

## Failure and verification

Use real subprocess fixtures for distinct per-arm files and same-path overwrite,
missing media, stale directories and symlink rejection. Run focused regression
tests, Python compilation, diff review, full CI and the native Cypress workflow.
Inspect the actual PNGs and video metadata after download, verify hashes, and
link them from the report/slide without claiming they came from the earlier run.

## Source

Cypress official screenshot/video documentation, read 2026-09-20:
https://docs.cypress.io/app/guides/screenshots-and-videos
https://docs.cypress.io/app/references/configuration
https://docs.cypress.io/api/commands/screenshot

Video must be explicitly enabled. Cypress clears media directories before a run,
which requires per-arm preservation. These sources describe capture mechanics,
not the validity of a scientific treatment.
