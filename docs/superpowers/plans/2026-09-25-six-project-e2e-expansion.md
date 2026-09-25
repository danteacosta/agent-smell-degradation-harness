# Six-project E2E expansion implementation plan

**Goal:** Produce prospective browser evidence for four new projects without
changing the omission family or inspecting outcomes before the cohort is frozen.

1. Freeze source custody, A/B/C text, neutral interfaces, and the 72-slot
   schedule in `scripts/six_project_e2e_freeze.py`; verify exact deletion and
   deterministic materialization in `tests/test_six_project_e2e_freeze.py`.
2. Implement and qualify the Paperless-ngx, Kanboard, Nextcloud, and OpenProject
   browser oracles with valid alternatives, target mutants, non-target mutants,
   ambiguity controls, screenshots, and fail-closed observation schemas.
3. Bind the qualified oracle hashes, collector/runtime identity, models, and
   execution policy in a new immutable execution packet. Do not repair or retry
   individual generated artifacts.
4. Dispatch all 72 isolated requests through the ChatGPT-authenticated Codex
   adapter. Preserve every planned slot and stop cleanly if account capacity
   cannot complete the packet.
5. Execute every artifact offline in the frozen browser runtime. Publish raw
   labels, screenshots, receipts, per-project/model contrasts, missingness
   bounds, and the equal-project-weighted descriptive result.
6. Update the thesis report and presentation with the final evidence and its
   limits; submit code changes through CI and merge only when green.

Verification: focused Python tests, browser-oracle qualification, materialized
packet revalidation, main test suite, syntax/static checks, and `git diff --check`.
