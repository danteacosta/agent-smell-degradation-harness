# Lessons learned

## 2026-09-03: pre-final evidence

- A schema-valid checkpoint can still be substantively empty. Shape validation and evidence completeness must be separate gates, and the latter must run before T4.
- A passing LLM judge count is not a correctness rate without independent labels. Agreement is a calibration observation, not ground truth.
- Provider retries consume budget and can hide prompt-contract failures. Keep the prompt hash, stage bounds, response hash, and measured cost together in every rerun.
