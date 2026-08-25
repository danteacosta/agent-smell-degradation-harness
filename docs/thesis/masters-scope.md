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

Acceptance-criteria generation is the only primary workload. H1 measures
the paired clean-minus-defective ordinal severity difference. H2 measures the
held-out PR-AUC delta between fixed nested models B3 (`static + operational +
provenance through T3`) and B0 (`static + operational`). The primary practical margin is frozen at
`ΔPR-AUC >= 0.05`; the claim additionally requires the pre-registered interval
to exclude zero.

H1 and H2 are planned conditional claims, not current results. They cannot be
reported as confirmatory until all external gates pass:

- a frozen outcome-blind H2 precision plan that simulates the untouched test
  partition and resamples projects; the unconditional floor is 60 independent
  source intents/12 projects with at least 6 test projects and 24 test intents.
  The conservative design-stage candidate is 220 intents/36 projects under a
  50/20/30 project split, but remains unfrozen because its weak-signal scenario
  misses the target; 24 intents/6 projects is a pilot floor only;
- at least two real provider/model configurations producing genuine,
  runtime-native ARP 3.0 T1/T2/T3 checkpoints from the same execution that
  produces the artifact, with immutable provider metadata and cutoff hashes;
  here runtime-native means externally materialized by the instrumented
  runtime, never chain-of-thought or a retrospective snapshot;
- blinded primary human labels, a double-coded subset, adjudication, missing
  label policy, Krippendorff's alpha, and bootstrap confidence intervals;
- a frozen feature manifest and deterministic train/calibration/test H2 report;
- a shadow pilot measuring false alerts, lead time, review time, escaped
  incidents, and cost per run.

The current seven-source seed, stub runs, prompted checkpoint summaries,
oracle-derived labels, synthetic replay fixtures, and product smoke reports
are development evidence only.

## From natural-language test smells to requirement-induced constraint loss

Natural-language test-smell research has progressed from cataloguing and
detecting smells, through systematic transformations, to controlled evidence
about harmfulness. This thesis extends that trajectory without proposing
another catalog: it studies whether a controlled upstream requirement defect
propagates into material constraint loss in agent-generated acceptance criteria
and whether the loss is observable before the terminal artifact.

A requirement smell is a risk indicator. The confirmatory treatment is the
independently reviewed removal of one test-relevant condition, not the mere
presence of a lexical marker. Static smell signals remain baselines because
prior effects are task- and metric-dependent.

This interpretation is deliberately contextual. Requirements-smell quality
assurance work shows that lightweight detection can surface useful defects but
that some smell categories are not clearly distinguishable in practice
([Rapid quality assurance with Requirements Smells](https://www.sciencedirect.com/science/article/abs/pii/S0164121216000789)).
Recent evidence on smells in LLM prompts likewise reports mixed, task-dependent
effects rather than a universal degradation law
([On the Impact of Requirements Smells in Prompts](https://arxiv.org/abs/2501.04810)).
Accordingly, the thesis treats smell family and project/lifecycle context as
heterogeneity variables and does not redefine the primary treatment or outcome
after seeing results.

For conditional requirements, T1 records the antecedent, consequent, whether
the antecedent is sufficient or also necessary, the temporal relation, and the
explicitly specified negative case. This is a measurement safeguard, not a
claim that one formalization is correct: practitioners have been shown to
disagree about whether an antecedent is sufficient or necessary and about the
formal interpretation of natural-language conditionals
([How Do Practitioners Interpret Conditionals in Requirements?](https://arxiv.org/abs/2109.02063)).
Requirements without a conditional clause record an empty semantic list.

This makes the project complementary to the EASY group's natural-language
test-smell program. Its catalogs inform a preregistered secondary analysis of
whether defective requirements induce recognizable smells in generated
acceptance criteria; its transformations inform exploratory intervention
design. Neither defines the primary H1/H2 treatment or outcome. The thesis
contributes upstream-to-downstream propagation, process observability,
label-plane separation, and a reproducible evaluation boundary.

The optional RQ3 compares a structure-preserving rewrite and a targeted
clarification question. Both must operate without the clean pair or oracle.
Perfect restorations that read those fields are retained only as development
upper bounds and are excluded from scientific claims.

## Academic relevance and originality

The contribution is defensible when stated as the combination of:

1. a requirements-conditioned, provider-produced T1/T2/T3 feature plane;
2. strict separation of features from terminal labels and oracle metadata;
3. paired clean/defective variants with project holdout;
4. trace-recomputed raw feature manifests, one fixed estimator for B0–B3,
   calibration-only threshold fitting, and untouched test evaluation without
   in-sample family selection;
5. independent human labels plus clustered uncertainty; and
6. operational metrics that distinguish ranking from an actionable gate.

The H2 implementation now fits the same auditable dependency-free ranker to
the preregistered nested B0–B3 rows and reports the held-out T1/T2/T3 boundary map.
This closes the earlier loophole in which a frozen manifest could contain
precomputed scores. It does not turn the development corpus into evidence: the
models and boundary map remain unestimated until eligible provider traces and
independent labels are collected.

The novelty is a hypothesis until the confirmatory evidence exists. The thesis
must not claim a new smell taxonomy, the first smell effect on LLMs, or a
universal detector. A negative or weak H2 result remains scientifically useful
if it maps silent regions and shows where process observability does not help.

## Scope discipline

In scope: H1, H2, acceptance-criteria generation, two provider
configurations, the ARP/replay artifact, confirmatory annotation protocol, and
traceability as an external validation slice.

Each source record also records project domain, lifecycle role, and lifecycle
phase. These fields support planned heterogeneity and external-validity
checks; they are dataset metadata and cannot enter deployable feature rows or
labels.

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
