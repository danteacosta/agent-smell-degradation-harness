# Provider-agnostic LLM panel runtime

## Goal

Make the natural-requirement panel executable with whichever model providers
are selected later, while preserving blinded annotation, private source text,
reproducible operational evidence and the historical task contract.

## Tasks

- [x] Define arbitrary judge IDs and configurable consensus in the panel
  contract.
- [x] Add test-first coverage for routing, smoke limits, retries, missing
  credentials, and adapter response normalization.
- [x] Implement environment-backed judge configuration and HTTP adapters for
  common wire formats behind a provider-neutral adapter seam.
- [x] Add a smoke-by-default CLI, explicit full-run confirmation, private raw
  output guards, and a secret-free configuration example.
- [x] Add explicit `prepilot`/`pilot`/`full_panel` stage metadata, strict
  expected-task and same-item-set validation, and model snapshot recording.
- [x] Add an idempotent atomic checkpoint/resume path and a measured-cost
  budget stop that fails closed when billing cannot be measured.
- [x] Add panel agreement/disagreement summaries, optional private project and
  intent joins, and a separate human/model disagreement field.
- [x] Add a private four-stratum control-matrix contract without expected or
  gold labels, while keeping the historical two-variant contracts unchanged.
- [x] Run the complete CI suite, review the diff, and publish the branch only
  after the generated artifacts and remote status are verified.

## Verification commands

```text
python3.13 -m unittest discover -s tests -p 'test_panel_runtime.py'
python3.13 -m py_compile label_plane/llm_panel.py label_plane/panel_runtime.py scripts/run_llm_panel.py
python3.13 scripts/run_llm_panel.py --help
git diff --check
```

The complete CI suite is authoritative because this workstation does not have
the repository's pytest dependency installed.

The implementation branch was published at commit `548272f`. CI run
`33170680479` passed the evaluation gate, `33170680441` passed the
constraint-replay gate, and `33170680439` passed the wedge check. The branch
is synchronized with its remote; the main worktree and branch were not changed.
