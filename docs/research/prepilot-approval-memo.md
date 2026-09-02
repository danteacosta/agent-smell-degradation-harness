# Advisor approval memo: non-confirmatory pre-pilot

Date prepared: 2026-09-01  
Decision status: **pending approval**

## Decision requested

Approve preparation and execution of the structured, non-confirmatory
pre-pilot only after the technical and human gates below return \`go\`.

The requested scope is exactly:

- 12 independent source intents;
- one clean and one controlled
  \`incompleteness_missing_condition\` variant per intent;
- five replications per variant;
- acceptance-criteria generation as the primary task;
- 120 primary episodes;
- primary context condition \`no_compaction\`;
- a separate clean/smelly ×
  \`no_compaction\`/\`compaction_stress_test\` interaction check;
- two distinct real provider/model configurations;
- runtime-native T1–T3 evidence before T4;
- blinded human/adjudicated outcome labels.

This approval is not approval for confirmatory collection or for changing H1,
H2, the smell taxonomy, the precision plan, or the 120-episode design.

## Evidence required before launch

| Decision item | Required evidence | Status |
|---|---|---|
| Corpus and rights | 12 unique intents, at least 6 projects, exact source/license evidence, hashes, near-clone review, manipulation checks, and a timestamped review of redistribution, derivative-use, attribution, and external-provider processing rights | pending; candidate pool is not admitted |
| Provider qualification | One clean and one defective smoke per provider, native T1–T3, temporal ordering, atomic obligations, context events, usage, latency, hashes, and cost | pending; adapter and smoke are implemented |
| Annotation | Frozen rubric, two trained annotators, outcome-blind 20% duplicate subset, missing-label policy, and named adjudicator | pending; preparation tool is implemented |
| Budget | Measured provider estimate × 120 × 1.25 plus annotation hours and approved cap | pending |
| Reproducibility | Immutable source/config/model versions, resolved configuration hash, private raw inputs, redacted report, and clean-environment command | pending |
| Ethics/data governance | Advisor/institution determines whether human annotation or external-provider transmission needs ethics, privacy, or data-processing approval | pending |
| Context mechanism | Primary no-compaction isolation and separately reported typed-hard-lane interaction/mechanism ablation | implemented in protocol; real qualification pending |

## Human decisions requested

Please record one answer for each:

1. Is the 120-episode structured pre-pilot approved once every evidence row
   above is complete?
2. Is a six-project minimum appropriate for the pre-pilot, with larger
   project-held-out requirements reserved for the confirmatory precision plan?
3. May a source with written permission, but no machine-readable license, be
   admitted when the permission covers redistribution, the planned
   missing-condition transformation, required attribution, and transmission to
   the selected external providers?
4. Who are the two annotators and the independent adjudicator?
5. What provider-cost cap and annotation-hour cap may the operator use?
6. Does the institution require an ethics/privacy review before annotation or
   external API calls?
7. Is the private storage location for raw requirements, traces, artifacts,
   labels, and provider reports approved?

## Sign-off

- Advisor: ______________________________
- Date: _________________________________
- Scope approved: yes / no
- Corpus/right-of-use decision: _________________________________
- Annotation/adjudication decision: ____________________________
- Provider budget cap (USD): _________________________________
- Annotation-hour cap: ________________________________________
- Ethics/privacy review required: yes / no / to be determined
- Conditions or requested changes: _____________________________

The fail-closed readiness command remains
\`python -m eval.prepilot_readiness\`. No field in
\`data/prepilot/launch-plan.candidate.json\` should be changed to true merely
because this memo exists.
