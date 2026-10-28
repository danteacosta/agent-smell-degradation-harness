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
the observed value. This is compatible with the shared misses being driven by
heterogeneity between requirements; it does not exclude residual association within a
requirement, and with one to four mutants per requirement the within-requirement
expectation is noisy. With the complete requirement no loss was missed by all five.

**F3 — Generator recovery and tester detection move together, mostly through one cluster (Q3).** Across the 25
requirements, the share of arm-C implementations that kept the omitted rule
(generator recovery, from the 46-case collection) correlates with the incomplete-source
detection rate averaged over testers: Spearman ρ = 0.59; permutation p = 0.002; with
permutations only within projects, p = 0.015. The correlation is carried by a
cluster: 11 requirements have zero recovery and zero detection. Split by recovery, the
14 requirements whose rule no generator kept have mean incomplete-source detection 0.048,
and the 11 with some recovery have 0.242; without the zero–zero cluster, Spearman is
−0.24 (n = 14, permutation p = 0.42). The supported reading is a dichotomy (rules never
recovered are almost never detected), not a monotone relation. In the four requirements with a context
cue (panel κ = 0.65), mean generator recovery is 0.375 against 0.143 and mean tester
detection 0.200 against 0.121. In practical terms the coupling changes little here: the
mean per-requirement product of loss and miss (an omitted rule shipped broken and
unnoticed) is 0.725, against 0.710 if loss and miss rates were unrelated (difference
0.014, project bootstrap [0.004, 0.022]), because both rates are high in this sample. Eligibility required at least one confirmed mutant, so
fully recovered rules are absent and the recovery range is truncated.

**F4 — Code anchoring shows up as rejecting the correct implementation (Q5).** Suites
written from the incomplete request plus the mutant's code alarm on the correct
reference in 17–34 of 50 suites per tester (34–68%); complete-source suites do so in
1–11 of 50 for four testers and 23 of 50 for Claude Sonnet 4.6.

**F5 — On average, sound suites do not reward the loss (Q4).** Within arm C, the mean
alarm rate of sound suites on recovered implementations is at most 0.136 for any tester
and source, and in no tester–source pair is the mean higher on recovered implementations
than on mutants; averaged over testers, the per-requirement difference is negative for
all three sources. Individual suites do: for example gpt-6-astra, zulip-unsubscribe-self,
spec_incomplete, suite `so-de94c162478caa49462d` alarms on 1 of 3 recovered and 0 mutants;
Claude Sonnet 5.5, zulip-private-channel-access, code_incomplete, suite
`so-a9a97807dfcf56c582f8` alarms on 1 of 2 recovered and 0 mutants (shown mutant
excluded); both counterexamples found in review by Codex. The earlier pooled
recovered-alarm rate of code-anchored suites (0.735, `results.json`) comes mostly from
unsound suites; restricted to sound suites and aggregated per tester and source, the
"suite prefers the defect" reading is not supported.

**Sensitivity: assertion alarms only.** `--assertion-only` writes
`data/verifier-coupling/v1/results-assertion-only.json` (soundness unchanged: quiet on the
reference). F1: one complete-source tester 0.776, all five incomplete-source testers
0.433, difference −0.343 [−0.605, −0.105], sign-flip p = 0.047. F2: 65.4% missed by all
five against 51.5% under independence. F3: ρ = 0.54, permutation p = 0.006, within-project
p = 0.040; dichotomy 0.038 vs 0.197. The direction of every result is unchanged.

## What this does and does not show

Together, F1–F3 describe a single pattern: the obligation that the request omits is
lost by some generators, missed by testers who receive the same request, and missed by
all of them in the same requirements; where generators never recover the rule,
testers almost never detect its loss. This is a candidate thesis claim
("one omission, two blind spots"), not a confirmed mechanism.

Close prior work, checked in the primary text by Codex on 28/10 (preprints, versions
inspected): Konstantinou, Tambon and Papadakis, *On the risk of coding before testing*
(arXiv 2607.05139; IV-E requires failing the faulty code and passing the reference; VII-B
weakens test descriptions in three variants over selected faulty implementations);
Haeri and Ghelichi (arXiv 2607.06636; 4.5 removes validation rules; appendix I analyses
partial specifications; ungrounded ensembles are a contrast); TestSuiteBench
(arXiv 2610.13065; generates implementations and tests from the same specification; 3.2
ablates official documentation against a refined specification). Also read on 28/10 by Claude: Liu et al., TiGanEval, *Instructions Are Evidence, Not
Objectives* (arXiv 2610.17757; 64 SWE and research tasks, partial vs full instructions,
requirements discoverable from the workspace, held-out evaluator; 53–67 point drop in
Success@1; its failure analysis mentions an agent whose own validation followed its fix
path, but agents' tests are not measured), and Gaonkar, TRACE (arXiv 2610.11678, read
from the abstract only; paired runs and rescoring of fixed trajectories to separate
agent from verifier effects; on τ²-bench identical reruns flipped 15–36% of task
outcomes, which matters for reading single τ² attempts). The candidate
contribution is therefore narrow: tracking the same removed obligation through both
sources, separating implementation loss, conditional detection and joint escape, against
a stable external reference. No priority over this combination is claimed.

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
