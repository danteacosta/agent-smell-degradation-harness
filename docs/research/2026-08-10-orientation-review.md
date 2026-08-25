# Orientation review: requirement-smell degradation and agent observability

Date: 2026-08-10

## Research question for the meeting

The defensible question is not whether requirement smells exist or whether
they affect an LLM. Those are already established directions. The narrower
question is whether provider-produced, pre-final evidence adds calibrated,
deployable warning value for material constraint-preservation failures in
acceptance-criteria/test generation, under independent labels and project
holdout.

## Literature position

| Source | What it establishes | Consequence for this thesis |
| --- | --- | --- |
| [Márcio Ribeiro's research portfolio](https://sites.google.com/a/ic.ufal.br/marcio/research) | EASY has a sustained empirical program on natural-language test smells, catalogs, transformations, perception, and reliability. | Use the program to position a downstream propagation study; do not rename it as a requirements-smell program or claim a new taxonomy. |
| [Manual Tests Do Smell!](https://arxiv.org/abs/2308.01386) | Natural-language test smells can be catalogued and detected with empirical evaluation. | Establishes the upstream smell/detection baseline; this work should study downstream propagation and observability. |
| [Catalog of Transformations to Remove Smells](https://arxiv.org/abs/2404.16992) | Smells can be associated with actionable transformations and professional perception. | Supports a controlled clean/defective pair design and motivates a future remediation extension, not a second primary thesis. |
| [On the Harmfulness of Smells in Natural Language Test Cases](https://doi.org/10.1109/ESEM64174.2025.00023) | Smells matter scientifically when they measurably harm task performance, not merely because they occur. | Motivates measuring material constraint loss and operational consequences rather than counting lexical indicators. |
| [NALABS](https://arxiv.org/abs/2202.05641) and [requirements-smell QA](https://arxiv.org/abs/1611.08847) | Requirements and test-language quality can be operationalized as smell signals. | Static smell indicators are legitimate baselines, but cannot be the claimed novel contribution. |
| [On the Impact of Requirements Smells in Prompts](https://arxiv.org/abs/2501.04810) | Smell effects in LLM-supported traceability are task- and metric-dependent. | Pre-register one primary construct and report traceability as external validation rather than mixing outcomes. |
| [Practitioners' perceptions on requirements smells](https://www.sciencedirect.com/science/article/pii/S0950584925001624) | Severity/frequency differ by smell type and lifecycle stage; ambiguity and unverifiability matter to practitioners. | Use type-specific labels and human annotation; avoid treating every smell as one scalar phenomenon. |
| [PrefixGuard](https://arxiv.org/abs/2605.06455) | Prefix monitors, calibration, held-out evaluation, observability ceilings, false-alert constraints, and lead time are now a direct comparator. | The thesis must report actionability/lead time and explicitly distinguish ranking from a usable gate. |
| [Validating Formal Specifications with LLM-generated Test Cases](https://arxiv.org/abs/2510.23350) | LLM-generated tests can validate formal specifications and expose specification defects. | Supports acceptance-criteria/test generation as a meaningful workload, while leaving process observability as the gap. |

## Working novelty boundary

The defensible contribution is a leakage-resistant paired protocol and open
benchmark for measuring the *observable boundary* of requirement-induced
constraint loss before the terminal artifact. The differentiators are the
combination of controlled smell variants, provider-produced T1--T3 evidence,
independent human labels, train/calibration/test separation, project holdout,
clustered uncertainty, and explicit silent-failure/negative-control analysis.

This is a hypothesis until the external dataset, live-provider traces, human
labels, and confirmatory H2 report exist. Code and protocol alone are not the
scientific moat.

## Downstream work required before a confirmatory claim

1. Map each adopted EASY smell to an expected constraint-preservation failure
   and a versioned secondary annotation rubric; keep it separate from the
   primary constraint-loss label.
2. Collect the required independent intents and projects with source,
   license, project IDs, and near-clone checks.
3. Run at least two real providers/models with genuine T1--T3 checkpoints and
   immutable request/response/configuration hashes.
4. Complete blinded human labels, double-coding, adjudication, alpha, and
   bootstrap confidence intervals.
5. Produce the frozen H2 report with deployable baselines, delta PR-AUC,
   clustered interval, false-alert rate, lead time, and an automatic claim
   decision.

## Repository implications

The three repositories are useful as a protocol/harness/product stack, but
their public credibility depends on one released ARP contract, synchronized
canonical `main` branches, reproducible install instructions, and a public
dataset/replay bundle. The current local seed, stub runs, and synthetic product
fixtures must remain explicitly non-confirmatory.
