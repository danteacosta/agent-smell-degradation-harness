# Pre-pilot launch pack

## Decision requested from the advisor

Authorize preparation and execution of the non-confirmatory 120-episode
pre-pilot only after the executable readiness report returns `go`. This is not
authorization for confirmatory collection and does not freeze the current
220-intent/36-project design candidate.

## Fixed pre-pilot design

- 12 independent software intents;
- one clean and one controlled missing-condition variant per intent;
- five replications per variant;
- acceptance-criteria generation as the only primary task;
- 120 episodes in total;
- two distinct real provider/model configurations qualified before collection;
- runtime-native T1–T3 evidence emitted before T4;
- final artifacts labeled independently under the blinded rubric.

The pre-pilot estimates feasibility, provider/checkpoint failure rates,
annotation time and reliability, failure prevalence, intraproject dependence,
latency, and cost. It cannot support H1 or H2.

## Gates before the first episode

| Gate | Required evidence | Current state |
| --- | --- | --- |
| Advisor | Explicit authorization for the pre-pilot scope | Blocked |
| Corpus | 12 unique licensed intents, project IDs, hashes, near-clone review, manipulation checks | Blocked |
| Providers | Two runtime-native configurations pass temporal, schema, failure, and hash qualification | Blocked |
| Annotation | Frozen rubric, two trained annotators, outcome-blind 20% duplicate subset, adjudicator | Blocked |
| Leakage | T1–T3 cannot load artifact, oracle, mutation, provider identity, or outcome label | Implemented; rerun on qualified configurations |
| Budget | Provider estimate plus 25% contingency and annotation-hour estimate approved | Blocked |
| Reproducibility | Versioned prompts, configuration hashes, execution window and immutable run manifest | Blocked |

Run the gate with:

```bash
python -m eval.prepilot_readiness
```

It exits non-zero while blocked. `make prepilot-readiness` writes the current
report for review without treating a blocked candidate as a CI failure.

## Provider qualification protocol

For each configuration, execute at least one clean and one defective smoke
episode and verify:

1. the adapter reports the intended provider, model and immutable model version;
2. T1 and T2 are bounded provider responses;
3. deterministic T3 validates T1-to-T2 semantic coverage without reading T4;
4. all T1–T3 timestamps precede the artifact request;
5. request, response and configuration hashes are present;
6. malformed T2 and a simulated timeout fail before artifact generation;
7. no prompted snapshot or replay trace is promoted to runtime-native;
8. latency, token usage and cost are exported without prompts, artifacts or secrets.

The qualification report path and configuration hash are recorded in
`data/prepilot/launch-plan.candidate.json`. Credentials never enter that file.

## Annotation rehearsal

Before collection, two annotators independently label a small training set that
is not part of the 12-intent pre-pilot. They receive only the final artifact and
the independent reference constraints. Variant, defect family, provider/model,
checkpoint evidence, oracle outcome and detector predictions remain hidden.

The 20% duplicate subset is selected before annotation. The pre-pilot reports
ordinal Krippendorff alpha with its bootstrap interval. Alpha at least 0.70
supports continuing; below 0.60 after adjudication requires rubric revision or
claim narrowing. No label is imputed.

## Cost worksheet

Provider cost is estimated from qualified smoke runs, not advertised token
prices alone:

`estimated pre-pilot cost = mean observed episode cost × 120 × 1.25`

Annotation effort includes first coding, duplicate coding, adjudication and
quality control. The launch plan records both provider dollars and human hours;
neither may remain zero when the gate is promoted to `pilot_ready`.

## After the pre-pilot

Use only outcome-blind aggregate estimates of prevalence, variance,
intraproject dependence, checkpoint availability and cost to update the H2
precision grid. The current 220/36 candidate may increase or decrease. Freeze
the final precision plan and preregistration before confirmatory collection.
