# Discovery experiment artifacts

This directory is the tracked home for compact, reviewable artifacts from the
requirements-smell discovery process.

Run the offline discovery from the repository root:

```bash
python -m eval.discovery --mode offline --replications 1
python -m eval.discovery --verify-artifacts
```

Each promoted run contains:

- `run.json`: mode, source revision, case/task counts and configuration;
- `corpus-manifest.json`: source provenance and hashes for every case;
- `episodes.jsonl`: one record per case, variant and task family;
- `generated-code/`: the clean and smelly implementations;
- `test-reports/`: hidden-test outcomes and execution states;
- `comparisons/`: a readable clean-versus-smelly code diff; and
- `metrics.json`: aggregate results.

The default offline run is deterministic and uses the smell-blind stub. It
demonstrates the pipeline; it is not a live-provider or confirmatory result.
On macOS hosts that cannot expose the required address-space limit, the
offline adapter may use a hash-exact trusted reference fixture; reports mark
that execution mode and it must not be presented as isolated execution.
The live mode requires `AGENT_EXPERIMENT=1` and provider credentials and must be
reported separately with its cost and qualification metadata.

Do not commit API keys, private prompts, or unreviewed large provider traces.
