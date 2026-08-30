# LLM panel smoke analysis — 2026-08-30

Status: operational smoke evidence only. This run does not authorize or
support a thesis claim, a confirmatory collection, or a provider qualification
decision by itself.

## Result

Run `llm-panel-20260830-smoke-v16` sent 10 selected tasks to each of two
configured judge slots, using the same selected item set for both judges. It
made 20 provider calls and completed all selected tasks:

| Measure | Result |
| --- | ---: |
| Valid normalized responses | 19/20 |
| Recorded errors | 1/20 |
| `judge-a` valid responses | 9/10 |
| `judge-b` valid responses | 10/10 |
| Measured provider cost | US$ 0.01773355 |
| Total measured tokens | 11,952 |
| Remaining selected tasks | 0 |

The one error was a DeepSeek chat-completions response with no final text.
Its usage was still recorded: 1,024 completion tokens, all attributed to
reasoning, and US$ 0.00238501. The run therefore remained measurable and did
not stop on an unknown-cost condition. This is an operational failure signal,
not evidence about requirement-smell prevalence or model quality.

## What the smoke establishes

The smoke is consistent with the panel runtime's operational contract:

- both real provider/model configurations accepted the private blinded task
  protocol;
- the exact limit of 10 tasks per judge was routed, with identical item
  coverage;
- model snapshots, request/response hashes, latency, usage, errors and cost
  were exported without prompts, responses or keys in the repository;
- the empty-content failure was retained as an error rather than silently
  converted into an annotation; and
- the measured cost stayed below the run cap of US$ 0.50.

The result is enough to qualify the local execution path for further gated
testing. It is not enough to qualify the providers for the master's
pre-pilot, because that gate also requires runtime-native T1–T3 checkpoint
evidence, temporal ordering before T4, schema/failure tests, and independent
human annotation readiness.

## What it does not establish for the master's experiment

The smoke and the thesis design are different units and should not be merged
in analysis:

1. The smoke is a 20-call panel-label run over 10 selected item IDs. The
   documented master's pre-pilot is 12 independent intents × 2 variants × 5
   replications = 120 episodes. The documented pilot is 480 episodes with two
   real model configurations. The task manifest used by this smoke is a
   natural-corpus panel input, not the frozen 12-intent pre-pilot corpus.
2. The smoke uses `require_negative_controls=false` and has no control strata.
   A thesis-facing run must use the declared clean/defective design and the
   required control matrix where that stage calls for it.
3. This is label-plane annotation traffic. It does not emit provider-native
   T1, T2 and T3 lifecycle checkpoints before T4, so it cannot satisfy the
   runtime-native provider gate.
4. No human labels, blinded duplicate subset, adjudication, Krippendorff
   alpha, bootstrap interval, or missing-label export was produced. Model
   agreement cannot substitute for the primary human/adjudicated label.
5. `consensus_required=2` is recorded in the runtime configuration, but this
   smoke did not merge the responses into a thesis outcome. Panel consensus is
   descriptive robustness evidence, never ground truth.
6. The natural-corpus source manifest remains candidate-generation-only, with
   third-party rights and the confirmatory provenance/annotation gates still
   open. Project-disjoint processing is useful, but it does not by itself
   make the source admissible confirmatory data.

The correct scientific decision is therefore: **go for continued tooling and
provider-path investigation; no-go for thesis collection or confirmatory
claims**.

## Budget recommendation

The observed mean cost was US$ 0.0008866775 per provider call. If the pilot's
480 episodes receive both configured judges, the operational count is 960
provider calls. The direct projection is:

```text
960 × 0.0008866775 = US$ 0.85121040
US$ 0.85121040 × 1.25 contingency = US$ 1.06401300
```

The proposed pilot cap is therefore **US$ 1.25**. This is a planning
recommendation, not an approved launch budget. If the study protocol defines
480 as total provider calls rather than episodes evaluated by both judges, the
same calculation gives US$ 0.53200650 with contingency; the protocol must
freeze this unit explicitly before the cap is approved.

The cap should be updated only in the private pilot configuration after the
advisor, corpus, provider, annotation, leakage and reproducibility gates pass.
The checked-in launch plan should remain blocked while its approved budget is
zero.

## Required next gates

Before treating the panel as evidence for the master's experiment:

- freeze the corpus, project-held-out split, variants, replications and panel
  task manifest; record the provider-call denominator explicitly;
- run the separate runtime-native T1–T3 provider qualification protocol on
  both configurations, including clean/defective cases and malformed/timeout
  failures;
- decide and preregister the retry policy. Retries must be bounded, counted,
  and retained in failure-rate reporting;
- use a response-format contract appropriate to each provider and preserve
  empty/truncated responses as measured failures;
- select the outcome-blind 20% human duplicate subset before annotation,
  complete double coding and adjudication, and report alpha with its bootstrap
  interval; and
- export the final thesis analysis only after the data-acquisition gate,
  annotation gate, split freeze and confirmatory precision plan pass.

The smoke artifact remains useful as a private operational qualification
record, but its 19/20 response rate and cost projection must not be promoted
to thesis performance, prevalence, generalization, or effectiveness results.
