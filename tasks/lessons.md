# Lessons learned

## 2026-09-07: frozen runtimes and verification

- Build packages in a separate source staging directory. Creating local
  distribution metadata while custody tests run can change their environment
  inventory and invalidate already prepared fixtures.
- A sanitized subprocess must still reproduce the verified runtime's import
  path. Bind `PYTHONPATH` to that runtime explicitly; never inherit arbitrary
  paths or provider credentials. Editable-install metadata exposed this issue.
- Network test doubles must preserve planned call order when distinct source
  IDs produce identical prompts. A dictionary keyed only by prompt can silently
  assign an evaluation response to a development call.

## 2026-09-03: pre-final evidence

- A schema-valid checkpoint can still be substantively empty. Shape validation and evidence completeness must be separate gates, and the latter must run before T4.
- A passing LLM judge count is not a correctness rate without independent labels. Agreement is a calibration observation, not ground truth.
- Provider retries consume budget and can hide prompt-contract failures. Keep the prompt hash, stage bounds, response hash, and measured cost together in every rerun.
