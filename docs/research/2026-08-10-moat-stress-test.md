# Moat stress test: semantic reliability gate

Date: 2026-08-10

## Question

Does the thesis and the three-repository stack create a defensible scientific
and product moat, or is it primarily another tracing/evaluation harness?

## External evidence

| Source | What it already covers | Consequence for this project |
| --- | --- | --- |
| [Phoenix](https://arize.com/docs/phoenix) | OpenTelemetry/OpenInference tracing, evaluations, human annotations, datasets, experiments, replay, and provider integrations. | Tracing, labeling, replay, and generic evals are table stakes. The product must consume these traces and add a constraint-preservation decision, not compete as another observability UI. |
| [Braintrust evaluations](https://www.braintrust.dev/docs/evaluate) | Dataset/task/scorer evaluations, immutable experiments, CI/CD, online scoring, and production traces becoming test cases. | A generic pre-merge eval gate is not differentiated. The wedge must explain which requirement constraint was lost and where in the pre-final process. |
| [PrefixGuard](https://arxiv.org/abs/2605.06455) | Trace-to-monitor induction, online prefix failure warnings, calibration, and the gap between ranking and operational utility. | The thesis must position itself as a requirements-conditioned constraint-preservation monitor, with project holdout, human labels, false alerts, lead time, and a usable gate. |
| [Requirements smells in prompts](https://arxiv.org/abs/2501.04810) | Smell effects are task- and metric-dependent, with mixed traceability effects. | Do not claim a new smell taxonomy or universal smell effect; isolate one primary construct and use traceability as external validation. |
| [ReliabilityBench](https://arxiv.org/abs/2601.06112) | Repetition consistency, semantic perturbation robustness, and tool/API fault tolerance. | Repetition and fault injection are necessary controls, not the unique contribution. The project needs the additional requirement-to-checkpoint lineage and pre-merge decision layer. |

## Moat verdict

The moat is still a hypothesis, but the pre-data foundation is now executable
and reviewable rather than merely designed. The implementation closes the
reproducibility, leakage, and release-hygiene risks; it does not manufacture
evidence of generalization, adoption, or ROI.

## Foundation completed in this cycle

- ASD now ships a versioned `constraint-replay/v1` bundle with five public
  synthetic cases: clean approve, controlled loss block, weak signal warn, and
  two negative controls that must approve.
- The replay CLI accepts both a checked-in fixture and an arbitrary bundle,
  validates the full ARP 2.0.5 lifecycle envelope through the installed ARP
  2.0.6 validator, and fails closed with exit `30` for contract mutations.
- Reports include deterministic trace/report hashes, deployable features,
  namespaced retrospective baselines, bounded evidence, and JSON/SARIF parity;
  the GitHub Action keeps SARIF as a fork-safe artifact so a synthetic block
  does not masquerade as a CI infrastructure failure.
- ASD, RAG, and ARP now have explicit release metadata and contribution/security
  guidance. RAG remains pinned to immutable ARP v2.0.6; the ARP package remains
  MIT-licensed and was not retagged.
- The product boundary now includes SDK-free normalization contracts for
  Phoenix, Langfuse, and Braintrust exports, a versioned policy/failure-case
  registry, ROI metric computation, dependency constraints, and a documented
  shadow-to-warn-to-block pilot. These are integration and measurement
  primitives, not evidence that a customer adopted the product.
- Local verification is 313 ASD tests, 104 RAG tests, and 26 ARP tests; the
  GitHub checks for the merged PRs are green. These are engineering checks,
  not confirmatory thesis results.

| Layer | Current evidence | Moat strength today | What makes it defensible |
| --- | --- | ---: | --- |
| Scientific | Leakage-resistant protocol, feature/label separation, strict manifest binding, and a narrow H2 estimand. | 3/10 | A confirmed cross-project dataset with human labels and provider-produced T1-T3 traces showing incremental warning value over generic baselines. |
| Data | Seven local development records; no project IDs, external provenance, live traces, or frozen human labels. | 0/10 | A licensed, versioned corpus of requirement-smell pairs, traces, adjudications, silent failures, and outcomes that others cannot recreate cheaply. |
| Protocol | ARP v2.0.6 package with a 2.0.5 wire-schema compatibility matrix; ASD and RAG consumers are separated; replay validates the installed ARP lifecycle contract. | 4/10 | Independent providers/frameworks emitting the same typed T1-T3 contract and third-party consumers using it. |
| Workflow | Local/CI approve-warn-block, deterministic JSON/SARIF evidence, five-case replay benchmark, and fork-safe artifact upload. | 4/10 | A low-friction GitHub Action with integrations for Phoenix/Langfuse/Braintrust traces, policy packs, historical baselines, and measurable reduction in escaped semantic regressions. |
| Distribution | Public repositories now have explicit license, NOTICE, contribution, and security metadata; merged replay and release-hygiene PRs are reproducible. | 1/10 | A permissively licensed, documented starter kit, reference integrations, users contributing traces/failure cases, and published benchmark results. |
| Commercial | No live customer deployment or ROI evidence; pilot instrumentation and policy history schema now exist. | 0/10 | Proprietary cross-customer failure priors, calibrated policy history, incident/lead-time outcomes, enterprise privacy controls, and deployment support. |

## Falsification tests

The moat claim should be rejected if any of these occur:

1. A Phoenix/Braintrust baseline plus a standard evaluator matches the gate's
   incremental warning value without typed requirement constraints.
2. The provenance signal disappears under a new provider, project holdout, or
   paraphrased requirement family.
3. Human labels do not agree beyond the preregistered reliability threshold,
   or the result is driven by variant/smell leakage.
4. The product produces more than the accepted false-alert budget and does not
   improve review time or escaped-incident rate.
5. External users can reproduce the result from public generic traces without
   needing the protocol or dataset.

## Acceptance bar for a real moat

Before calling the project defensible, publish:

- at least 24 independent intents across 6 projects, with licensing and
  near-clone checks;
- two providers/models and two agent/framework configurations;
- blinded double annotation, adjudication, Krippendorff alpha, and clustered
  bootstrap intervals;
- a frozen H2 report with baseline PR-AUC, delta, confidence interval, negative
  controls, false alerts, lead time, and automatic claim status;
- a replay bundle and an OSS GitHub Action that consumes standard traces and
  emits constraint-level SARIF;
- a pilot showing review-time, escaped-incident, and cost impact.

Until then, the correct claim is “protocol-ready research prototype with a
promising wedge,” not “established moat.”
