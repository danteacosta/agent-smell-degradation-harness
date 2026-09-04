# Pre-pilot launch pack

The executable procedures and the approval record are in the
[pre-pilot unlock plan](prepilot-unlock-plan.md) and the
[advisor approval memo](prepilot-approval-memo.md).

## Decision boundary

The pre-pilot is a non-confirmatory 120-episode feasibility study. It may
estimate failure prevalence, provider reliability, annotation effort, cost,
latency, intraproject dependence, and the availability of pre-final evidence.
It cannot support H1 or H2.

The previous `284 clean` count is diagnostic only. It records LLM judge
agreement under an older protocol and does not establish correctness,
degradation, or causal effect.

## Fixed pre-pilot design

- 12 independent software intents;
- one clean and one controlled `incompleteness_missing_condition` variant per
  intent;
- five replications per variant;
- acceptance-criteria generation as the primary task;
- 120 primary episodes;
- primary context condition `no_compaction`;
- a separate clean/smelly × `no_compaction`/`compaction_stress_test`
  interaction check;
- two distinct real provider/model configurations;
- runtime-native T1-T3 evidence emitted before T4; and
- independently generated outcome labels under a blinded rubric.

## Substantive pre-final evidence

T1 and T2 are not complete merely because their JSON shape is valid. Before T4,
the runtime now requires:

| Stage | Required substantive fields |
|---|---|
| T1 | `constraints` and `atomic_obligations` must be non-empty and valid |
| T2 | `validation_checks` and `coverage_targets` must be non-empty |
| T3 | deterministic validation must bind T1 evidence to the T2 plan |

The gate stops the episode with `incomplete_substantive_evidence` before the
terminal artifact if these conditions fail. The redacted report records the
failed stage and the number of stages that passed. It does not treat presence
as correctness.

## Context-management control

The primary 120-episode condition disables context compaction:
`context_management.primary_condition = no_compaction`. The secondary protocol
crosses clean/smelly variants with `no_compaction` and
`compaction_stress_test`. This is a separate interaction check, not additional
primary episodes or confirmatory H1/H2 evidence.

The runtime records prompt-free context metadata: operation, trigger, start and
end times, measured UTF-8 sizes, checkpoint ID, and checkpoint hash. A qualified
run must show that context events occur before T4, that the primary condition
has zero compactions, and that the stress condition is reproducible.

The typed compaction stress test is a mechanism proxy. It is not a replication
of a learned classifier or a token-matched benchmark. T1 atomic obligations
and T3 hash-bound observations are measured as runtime evidence, not as
outcome labels.

## Gates before the first full episode

| Gate | Required evidence | Current state |
|---|---|---|
| Advisor | Explicit authorization for the non-confirmatory scope and LLM-judge role | Authorized for exploratory use |
| Corpus | 12 unique, rights-reviewed intents across 6 projects, immutable references, hashes, clone review, and manipulation checks | Validated in private v4 manifest |
| Providers | Both real configurations pass native temporal, schema, completeness, failure, usage, and hash checks | Minimal smoke passed; full-run verification pending |
| Annotation | Frozen rubric, outcome-blind duplicate selection, and explicit label policy | LLM judge path authorized; human confirmatory path not established |
| Leakage | T1-T3 cannot read artifact, oracle, mutation, provider identity, or outcome label | Implemented; verify in the corrected run |
| Budget | Measured provider estimate, retries, 25% contingency, and approved cap | US$0.988200 reserved under US$1.00 |
| Reproducibility | Frozen prompts, configuration hash, model/version, price, source revision, and immutable run manifest | Corrected config is frozen; full-run report pending |

Run the readiness command with:

```bash
python -m eval.prepilot_readiness
```

Credentials never enter that file. They remain in the private runtime
environment and are excluded from tracked configuration and reports.

It remains fail-closed while any required evidence is missing. A passing
smoke does not change that state.

## Provider qualification protocol

For each configuration, verify at least one clean and one defective episode:

1. the adapter reports the intended provider, model, and version;
2. T1 and T2 satisfy both schema and substantive completeness;
3. deterministic T3 validates T1-to-T2 semantic coverage without reading T4;
4. all T1-T3 timestamps precede the artifact request;
5. context events include monotonic times, measured UTF-8 sizes, operation,
   trigger, and hash-bound checkpoint identity;
6. atomic-obligation fields are present in T1 and bind to T3 observations;
7. request, response, protocol, and configuration hashes are present;
8. malformed T2 and a simulated timeout fail before artifact generation; and
9. latency, token usage, and cost are exported without prompts, artifacts, or
   secrets.

The latest low-cost native smoke passed both RF-04 variants for OpenAI
`gpt-5.6-luna` and DeepSeek `deepseek-v4-pro`. It is still classified as
`smoke_only`.

## Labeling boundary

The advisor authorized the two LLMs as independent exploratory judges. Their
agreement is a machine-observation metric. It is not human ground truth and
must not be presented as an accuracy or degradation rate.

For confirmatory H1/H2 work, freeze the outcome packet first. Select the 20%
duplicate subset without labels, hide variant/provider/checkpoint/oracle data,
use at least two trained annotators, and name an adjudicator. Report missing
labels instead of imputing them.

## Cost and handoff

The current conservative worksheet reserves US$0.988200 for the corrected
120-episode exploratory configuration, including retries and the 25%
contingency. Annotation time is a separate approval item.

The private handoff package must include the redacted report, append-only cost
ledger, source and constraint hashes, configuration and protocol hashes,
execution window, platform information, and the private input locations. Raw
requirements, provider responses, generated artifacts, and credentials stay in
approved private storage.

The current 220/36 candidate may increase or decrease after the pre-pilot's
feasibility estimates. The confirmatory precision plan must be frozen only
after that review and before confirmatory collection.

Before interpreting any pattern, review the corrected report for complete
artifact and judgment counts, substantive completeness, native context events,
cost, errors, and hash identity. If the run stops early, it is a feasibility
failure report, not evidence for H1 or H2.
