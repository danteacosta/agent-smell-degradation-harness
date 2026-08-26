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
- `observable-traces/`: portable T0--T3 projections consumed by the verifier;
- `generated-code/`: the clean and smelly implementations;
- `test-reports/`: hidden-test outcomes and execution states;
- `comparisons/`: a readable clean-versus-smelly code diff; and
- `metrics.json`: phase-1 aggregate results; and
- `verification/`: phase-2 decisions, independent behavior labels, efficacy
  metrics and a short interpretation guide.

The default offline run is deterministic and uses the smell-blind stub. It
demonstrates the pipeline; it is not a live-provider or confirmatory result.
On macOS hosts that cannot expose the required address-space limit, the
offline adapter may use a hash-exact trusted reference fixture; reports mark
that execution mode and it must not be presented as isolated execution.
The live mode requires `AGENT_EXPERIMENT=1` and provider credentials and must be
reported separately with its cost and qualification metadata.

Run the verifier against the newest promoted bundle, or choose one explicitly:

```bash
make discovery-efficacy
python -m eval.discovery_verifier --bundle-dir artifacts/experiments/runs/<run-id>
```

`verification/decisions.jsonl` contains only oracle-free decisions and stable
decision hashes. `verification/labels.jsonl` is written after those decisions
and contains the independent behavior labels used to calculate recall,
false-alert rate, F1, paired discrimination, lead time and cost/latency
summaries. Timing fields are run-specific; the score/action/hash are the
reproducible decision core.

Do not commit API keys, private prompts, or unreviewed large provider traces.
