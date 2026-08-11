# Master's Thesis Scope and Acceptance Boundary

## Thesis question

When does requirement-induced constraint loss become observable before the
terminal artifact of an agent workflow, and does provider-produced pre-final
evidence add useful warning value beyond deployable static and operational
baselines?

This is a study of an observable boundary, not a claim that all degradation is
detectable. The unit of contribution is the protocol and benchmark that make
that boundary measurable under controlled pairs, independent labels, project
holdout, calibration, and cluster-aware uncertainty.

## Primary workload and claims

Acceptance-criteria/test generation is the only primary workload. H1 measures
the paired clean-minus-defective ordinal severity difference. H2 measures the
held-out PR-AUC delta between provider-produced pre-final provenance and the
best deployable baseline. The primary practical margin is frozen at
`ΔPR-AUC >= 0.05`; the claim additionally requires the pre-registered interval
to exclude zero.

H1 and H2 are planned conditional claims, not current results. They cannot be
reported as confirmatory until all external gates pass:

- at least 24 independent source intents across at least 6 projects, with
  provenance, licensing, near-clone checks, and at least 8 intents per split;
- at least two real provider/model configurations producing genuine T1/T2/T3
  checkpoints with immutable provider metadata and cutoff hashes;
- blinded primary human labels, a double-coded subset, adjudication, missing
  label policy, Krippendorff's alpha, and bootstrap confidence intervals;
- a frozen feature manifest and deterministic train/calibration/test H2 report;
- a shadow pilot measuring false alerts, lead time, review time, escaped
  incidents, and cost per run.

The current seven-source seed, stub runs, oracle-derived labels, synthetic
replay fixtures, and product smoke reports are development evidence only.

## Relation to requirements-smell research

Requirements smells are the controlled upstream treatment and a static baseline,
not the claimed novelty. Existing smell taxonomies and studies establish that
smell effects are task- and metric-dependent. The thesis asks the downstream
question: which constraint-preservation failures are visible in the agent's
pre-final process, under what checkpoints, and with what operational cost?

This makes the project complementary to the EASY group's requirements-smell
program: the smell rubric and transformations can provide a principled
experimental treatment, while the thesis contributes process observability,
label-plane separation, and a reproducible evaluation boundary.

## Academic relevance and originality

The contribution is defensible when stated as the combination of:

1. a requirements-conditioned, provider-produced T1/T2/T3 feature plane;
2. strict separation of features from terminal labels and oracle metadata;
3. paired clean/defective variants with project holdout;
4. train-only family selection, calibration-only threshold fitting, and
   untouched test evaluation;
5. independent human labels plus clustered uncertainty; and
6. operational metrics that distinguish ranking from an actionable gate.

The novelty is a hypothesis until the confirmatory evidence exists. The thesis
must not claim a new smell taxonomy, the first smell effect on LLMs, or a
universal detector. A negative or weak H2 result remains scientifically useful
if it maps silent regions and shows where process observability does not help.

## Scope discipline

In scope: H1, H2, acceptance-criteria/test generation, two provider
configurations, the ARP/replay artifact, confirmatory annotation protocol, and
traceability as an external validation slice.

Out of scope for the primary thesis: a full production SaaS, memory/RAG
retrieval quality, a new smell catalog, automatic remediation, all agent task
families, and customer ROI as a scientific estimand. The product gate is a
demonstrator that makes the research artifact actionable; its commercial moat
requires a later shadow pilot and cannot be inferred from synthetic fixtures.

## Suggested dissertation structure

1. Motivation, requirements smells, and agent reliability.
2. Construct definition and threat model for semantic degradation.
3. Leakage-resistant protocol, ARP trace schema, and annotation procedure.
4. Confirmatory H1/H2 experiment and uncertainty analysis.
5. Silent-failure boundaries, operational utility, and external traceability
   validation.
6. Artifact evaluation, limitations, reproducibility, and product demonstrator.

## Acceptance verdict

The protocol/artifact is ready for data collection when the repository gates
are green. The thesis is ready for a confirmatory claim only when the external
data-acquisition gate, provider gate, annotation gate, preregistration freeze,
and H2 report all pass. Until then, the correct status is **protocol-ready,
empirically blocked**.
