# Local trace integrity before evaluation

The runner now checks trace files against the count and SHA-256 accumulated by
`ProvenanceRecorder` while it emits events. A receipt reconstructed from an
altered file cannot replace that emission record. This extends the strict
receipt validation in PR #205 into the evaluation path.

## Acceptance contract

- Given an intact newly emitted trace, evaluation and metric publication proceed;
  each episode includes its `trace_receipt` as audit metadata.
- Given a rewritten, truncated, or missing trace during generation, the runner
  raises an integrity error before task evaluation and writes no metric output.
- Given a completed trace altered by a later episode or validator, the runner
  raises an integrity error before aggregating and publishing metrics.
- Given preexisting content at the trace path, the recorder's fresh emission
  receipt does not adopt that content. Verification rejects the combined file.
- Given a file changed after its read, the trace evaluator consumes the same
  byte snapshot that passed verification, rather than reading the path again.

The recorder owns emission accounting. The integrity module owns byte validation
and verified parsing. The runner owns the placement of checks before evaluation
and publication. The event wire schemas, task labels, and scientific feature
definitions remain unchanged. Receipts are operational evidence, not predictors
or support for H1/H2.

The candidate freeze manifest records the new runner hash. Its status remains
`candidate`; this maintenance update neither confirms a freeze nor authorizes
provider execution.

## Trust boundary and remaining work

These receipts live in runner memory and episode metadata on the same host.
They establish local consistency, not authenticated authorship or independent
custody. A party able to alter runner memory or execution is outside this
barrier. The checks cover snapshots at specific points, not permanent file
immutability after publication. Interrupted writes fail verification rather
than being accepted as complete evidence. Existing files are preserved.

Independent custody still needs a separately controlled collector: receive
emission commitments before evaluation, bind them to run and episode identity,
and issue a receipt that the agent cannot replace. Retention, access controls,
failure handling, and the authority operating that collector require an
infrastructure decision and verification before any authenticity claim.

For product work, this is preparation for reproducible audit evidence. It does
not establish that customer evals miss critical rules, or that customers will
pay. The suggested pilots, a paid engagement, and repetition after an update
remain commercial validation milestones. No new collection or outreach is
part of this change.

## Verification

Behavior tests exercise the public recorder and runner with real local
collaborators, synthetic requirements, and no model calls. They cover intact
traces, payload replacement, deletion, truncation, later-episode and validator
tampering, preexisting prefixes, receipt isolation, and verified-snapshot reads.

Run the focused checks with the project's pinned ARP dependency available:

```sh
python -m pytest -q tests/test_runner_trace_gate.py tests/test_trace_integrity.py tests/test_provenance.py tests/test_eval_runner.py tests/test_provider_checkpoints.py tests/test_runtime_checkpoint_agent.py tests/test_test_omission_audit.py
```
