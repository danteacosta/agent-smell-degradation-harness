# One omission, two blind spots: verifier coupling in the shared-omission runs

Date: 2026-10-28. Status: exploratory, post hoc, descriptive. No model call, no new
generation, no change to any published number. Script: `scripts/verifier_coupling.py`;
results: `data/verifier-coupling/v1/results.json` (`--check` recomputes and compares);
tests: `tests/test_verifier_coupling.py`, including a check that the per-requirement
score used here reproduces each run's published `mean_requirement_mutation_score`.

## Why this analysis

After the 28/10 advisor decision, QP4 (do LLM-written review tests notice an omitted
obligation?) is the thesis axis. Close work already studies recoverable omissions
(TiGanEval), evaluator sensitivity separated from agent sensitivity (TRACE), verifier
quality with positive and negative cases (VerifierBench) and the information given to
test writers (Haeri and Ghelichi). The question that none of them answers in this form
is what happens when **the same obligation is missing from the request that drives the
implementation and from the source used to write its review tests**. The five evaluated
tester runs already contain the data to describe that coupling.

Inputs: the five evaluated runs listed in `data/shared-omission-e2e/testers.json`
(gpt-6-astra, Claude Sonnet/Opus 4.6, Claude Sonnet/Opus 5.5), the same 25
requirements and frozen implementations from eight projects, and the context-cue panel.
Soundness and alarms follow `scripts/mutation_adequacy.py` exactly.

## Results

**F1 — More testers do not replace the missing information (Q1).** Detection is the
share of oracle-confirmed losses (mutants) killed by at least one sound suite,
averaged with equal weight per requirement.

| Source | 1 tester | 2 | 3 | 4 | all 5 |
|---|---:|---:|---:|---:|---:|
| complete requirement | 0.824 | 0.964 | 0.992 | 1.000 | 1.000 |
| incomplete request | 0.179 | 0.311 | 0.403 | 0.464 | 0.500 |
| incomplete request + mutant code | 0.064 | 0.114 | 0.154 | 0.188 | 0.220 |

Pooling all ten incomplete-source suites of the five testers still detects less than
the two complete-source suites of a single tester: difference −0.324, project
bootstrap 95% [−0.574, −0.088], exact project sign-flip p = 0.047 (8 projects); the
pooled incomplete ensemble reaches the single complete tester in 11 of 25
requirements. Budgets differ on purpose (10 suites against 2).

**F2 — The blind spots are shared, and they are shared at the requirement level (Q2).**
With the incomplete request, 60.5% of the 81 confirmed losses were missed by all five
testers and none was caught by all five. Independent testers with the same marginal
rates would miss 43.7% jointly; excess 0.168, project bootstrap [0.078, 0.225]. Using
each tester's rate inside the requirement instead, the expectation is 58.6%, close to
the observed value: the testers agree because they fail on the same requirements, not
because of an extra mutant-level correlation. With the complete requirement no loss
was missed by all five.

**F3 — Generator recovery and tester detection are coupled (Q3).** Across the 25
requirements, the share of arm-C implementations that kept the omitted rule
(generator recovery, from the 46-case collection) correlates with the incomplete-source
detection rate averaged over testers: Spearman ρ = 0.59; permutation p = 0.002; with
permutations only within projects, p = 0.015. In the four requirements with a context
cue (panel κ = 0.65), mean generator recovery is 0.375 against 0.143 and mean tester
detection 0.200 against 0.121. Eligibility required at least one confirmed mutant, so
fully recovered rules are absent and the recovery range is truncated.

**F4 — Code anchoring shows up as rejecting the correct implementation (Q5).** Suites
written from the incomplete request plus the mutant's code alarm on the correct
reference in 17–34 of 50 suites per tester (34–68%); complete-source suites do so in
1–11 of 50 for four testers and 23 of 50 for Claude Sonnet 4.6.

**F5 — No sound suite rewards the loss (Q4).** Within arm C, sound suites alarm on
recovered implementations at most 0.136 (mean per tester and source), and in no
tester–source pair more often than on mutants; averaged over testers, the per-requirement
difference is negative for all three sources. The earlier pooled recovered-alarm rate of
code-anchored suites (0.735, `results.json`) comes from unsound suites; restricted to
sound suites the "suite prefers the defect" reading is not supported.

## What this does and does not show

Together, F1–F3 describe a single pattern: the obligation that the request omits is
lost by some generators, missed by testers who receive the same request, and missed by
all of them in the same requirements; where the remaining context lets generators
recover the rule, it also lets testers detect its loss. This is a candidate thesis
claim ("one omission, two blind spots"), not a confirmed mechanism.

Limits: post hoc questions on known results; 25 requirements from 8 projects, selected
because they had a confirmed loss; testers share pages and implementations, so they are
not independent replications; the context-cue split has 4 requirements; recovery is
estimated from at most four arm-C implementations per requirement; alarms count both
assertion and error alarms, and an alarm is not proof that the target rule was checked
(the blind human audit #185 remains pending). Nothing here changes H1/H2, the 46-case
results, the τ² collection or any frozen artefact.

## Next steps this suggests

1. Pre-register F1–F3 as hypotheses for a new requirement sample instead of claiming
   them from these data.
2. In the confirmatory collection, record tester detection next to generator recovery
   for every requirement, so the coupling (F3) is estimated without truncation.
3. Use F2 in the related-work positioning: ensembles of testers or judges drawn from the
   same incomplete source do not cover the obligation, which separates this result from
   evaluator-diversity remedies.
