# Pre-registration draft: QP4 tester extension of the confirmatory collection

Status: **draft for review by Dante, Márcio and Codex; not frozen, not registered, no
calls authorised.** It extends `2026-10-06-osf-registration-draft.md` (H1a/H1b) and
does not change H1a, H1b, their analysis or the selection proposal (#177). τ² is out of
scope.

## Decisions this draft relies on (advisor meeting, 28/10/2026)

- QP4 is the thesis axis.
- H2 stays in the thesis; T1–T3 are recorded in the same H1 runs (base draft, section 4).
- Primary H1 outcome: the frozen browser oracle verdict on the target rule.
- The two covariates proposed on 22/10 (remaining relational cue, contractual
  indeterminacy) are secondary, estimation only, coded blind before generation on the
  requirements admitted by the primary selection, without rebalancing.
- The second human coder for the #185 audit is postponed; mechanism claims about the
  tests stay conditional on that audit.

## Question

When one obligation is omitted from the request, do LLM-written browser test suites
written from that same request detect the resulting loss, and how does that compare
with suites written from the complete requirement, with several testers pooled, and
with the generators' own recovery of the rule?

Exploratory basis (not part of this sample): `docs/research/2026-10-28-verifier-coupling.md`
and the five tester runs listed in `data/shared-omission-e2e/testers.json`.

## Sample

The requirements admitted to the confirmatory H1 collection by the procedure of #177
(target 5 per project, 8 projects). After the H1 generations, the QP4 sample is
determined mechanically, as in `scripts/mutation_adequacy.py`: requirements with at
least one correct arm-A implementation and at least one oracle-confirmed loss in arm C
(`target_only_failure`). This conditions on generation outcomes; the number of
eligible requirements and their projects are reported, and the eligibility rule is not
changed after the H1 results are known.

## Testers and sources

- [DECIDE] Testers: the five testers of the exploratory runs if the budget allows,
  otherwise at least two testers from two providers, fixed before any call. Exact
  dated identifiers go in the frozen receipt.
- Sources, as in the exploratory runs: `spec_complete` (complete requirement and page
  scaffold), `spec_incomplete` (incomplete request and scaffold), `code_incomplete`
  (incomplete request and the code of one seeded confirmed mutant).
- Two suites per tester and source, generated once; no retry, no repair.
- Every suite runs against every correct, mutant and recovered implementation of its
  requirement in the qualified, network-disabled image.

## Outcomes

Definitions are those of `scripts/mutation_adequacy.py`: a suite is sound when it is
quiet on the reference implementation; a confirmed mutant is killed by a sound suite
that raises an assertion or error alarm on it; unusable suites stay in the denominator
as unsound.

- Per tester, requirement and source: mean over suites of killed / confirmed mutants.
- Per requirement and source: share of confirmed mutants killed by at least one sound
  suite of k pooled testers (k = 1 averaged over testers; k = all).
- Per requirement: generator recovery = recovered / (recovered + confirmed mutants) in
  arm C.

Alarms are reported separately as assertion and error alarms. An alarm is not evidence
that the suite checked the target obligation; that claim waits for the blind human
audit.

## Hypotheses

- **H-a.** For each tester, complete-source suites detect more confirmed losses than
  incomplete-source suites (per-requirement difference > 0). Estimand: the per-requirement
  mean over suites of killed / confirmed mutants, as in the Outcomes section, averaged over
  testers for the pooled test; the union-of-suites detection is reported as a secondary
  description only.
- **H-b.** The union of all testers' incomplete-source suites detects fewer confirmed
  losses than one tester's complete-source suites (difference < 0).
- **H-c.** Requirements in which at least one generator implementation kept the omitted
  rule have higher incomplete-source detection (mean over testers) than requirements in
  which none did. Exploratory basis: a descriptive contrast of 0.242 against 0.048 and
  ρ = 0.59, much of it from 11 requirements with zero recovery and zero detection.
  Removing that cluster (ρ = −0.24) is a post hoc sensitivity on a subset chosen by both
  outcomes; it does not establish a dichotomy or exclude a monotone relation. The group
  contrast is chosen as the estimand because it is simple to pre-specify, not because the
  data showed the relation to be dichotomous.

## Analysis

- H-a and H-b: equal weight per requirement; two-sided exact project sign-flip test;
  95% project bootstrap interval; support requires the predicted sign and rejection
  after Holm correction over {H-a pooled over testers, H-b} at 0.05. Per-tester H-a
  results are reported without being counted as separate confirmations.
- H-c: difference in mean incomplete-source detection between the two recovery groups,
  with a project bootstrap interval; Spearman ρ with the within-project permutation test
  and the correlation without the zero–zero cluster reported alongside. **Estimation
  only**: not used as a confirmatory claim (see power below, which simulated ρ and is
  therefore only indicative for the group contrast).
- Scripts: `scripts/mutation_adequacy.py` and `scripts/verifier_coupling.py`, frozen by
  hash before collection; any change after unblinding is reported as a deviation.
- Sensitivities: assertion alarms only; excluding the code_incomplete shown mutant;
  per-tester results.

## Planning simulation

`scripts/qp4_prospective_power.py` (v2) resamples the 25 exploratory requirements
(`data/confirmatory-planning/qp4-prospective-power.json`, 1,000 replications per cell).
It is a planning aid built on post hoc effects, not evidence.

**Correction (28/10, after review by Codex).** The v1 table is withdrawn. v1 multiplied
every H-a and H-b contrast by the effect factor before the exact sign-flip test, which is
invariant to positive scaling, so its "halved" column did not lower signal to noise; the
differences between its columns were only different Monte Carlo draws (the factor was in
the seed). v1 also tested H-a and H-b separately at 0.05, and used the union of each
tester's suites for H-a instead of the planned mean over suites. The recommendation that
about 40 eligible requirements suffice "even with halved effects" is withdrawn with it.

Model in v2, stated as assumptions:

- Estimands as registered: H-a uses the mean over suites of killed / confirmed mutants
  (complete minus incomplete, mean over testers; observed mean 0.618); H-b uses the union
  of all testers' incomplete-source suites minus the union of one tester's complete-source
  suites (observed mean −0.324).
- Effect factor f as a location shift that keeps the requirement-level spread:
  d' = d − (1 − f)·mean(d) + u_project, clipped to [−1, 1]; f = 0.5 halves the mean
  effect (H-a 0.309, H-b −0.162).
- Between-project heterogeneity u_project ~ Normal(0, τ), τ ∈ {0, 0.10}, shared by the
  requirements of a project; resampled requirements carry none of their own.
- Decision rule as registered: Holm over {H-a, H-b} at 0.05 with the predicted sign.
- Common random numbers across f; regression tests check invariance of the sign-flip
  test to scaling, monotone power in f on common draws, and the Holm step.
- For H-c, attenuation replaces a share 1 − f of detection values with values from other
  requirements; H-c is estimation only and these figures are indicative.

| Eligible requirements / projects | τ | H-a (f = 1 / 0.5) | H-b (f = 1 / 0.5) | H-c (f = 1 / 0.5) |
|---|---:|---:|---:|---:|
| 25 / 8 | 0 | 1.00 / 1.00 | 0.68 / 0.23 | 0.82 / 0.23 |
| 25 / 8 | 0.10 | 1.00 / 0.96 | 0.65 / 0.21 | 0.81 / 0.27 |
| 40 / 8 | 0 | 1.00 / 1.00 | 0.88 / 0.35 | 0.98 / 0.44 |
| 40 / 8 | 0.10 | 1.00 / 0.99 | 0.83 / 0.27 | 0.98 / 0.46 |
| 40 / 10 | 0 | 1.00 / 1.00 | 0.92 / 0.37 | 0.97 / 0.43 |
| 40 / 10 | 0.10 | 1.00 / 1.00 | 0.86 / 0.33 | 0.98 / 0.41 |
| 60 / 12 | 0 | 1.00 / 1.00 | 0.99 / 0.55 | 1.00 / 0.61 |
| 60 / 12 | 0.10 | 1.00 / 1.00 | 0.97 / 0.49 | 1.00 / 0.62 |
| 80 / 12 | 0 | 1.00 / 1.00 | 1.00 / 0.67 | 1.00 / 0.76 |
| 80 / 12 | 0.10 | 1.00 / 1.00 | 0.99 / 0.58 | 1.00 / 0.76 |

Reading. H-a is well powered in every cell, including with the halved effect and
heterogeneity, so Holm adds no practical cost for H-b here (H-a almost always rejects at
0.025, which then tests H-b at 0.05). H-b is not: with the observed effect, about 40
eligible requirements give 0.83–0.92; with the mean effect halved, 0.27–0.37 at 40 and
0.49–0.67 even at 60–80. The observed H-b effect comes from 25 requirements selected post
hoc, so the halved scenario is not pessimistic. No sample size is recommended from this
table yet: the choice depends on which H-b effect is worth detecting, which is a decision
for Dante and Márcio, not an output of the simulation. Note that eligible requirements
are fewer than admitted ones (exploratory: 25 of 46).

## Feasibility of the eligible sample

In the 46-case collection, 25 requirements (54%) were QP4-eligible: 17 had no confirmed
mutant in their four arm-C implementations and 4 had a mutant but no correct A.
With the planned 8 × 5 design, about 22 eligible requirements are expected, which the
corrected simulation puts at power of about 0.65–0.68 for H-b with the observed effect and
about 0.2 with the effect halved. Reaching
about 40 eligible requirements needs roughly 70–75 admitted ones, but the frozen #177
order lists only 10 (Paperless), 11 (Mattermost) and 13 (Immich) provisional admissions
in three projects, before qualification losses. Options to decide before freezing:

1. Raise arm-C draws per requirement (for example 8 instead of 4). A rough
   Jeffreys-prior projection from the 46 cases moves expected eligibility from about
   0.67 to 0.76; this projection is optimistic for rules never lost in four draws, and
   the observed rate was 0.54. More draws also reduce the truncation that limits H-c.
2. Unequal targets per project, registered before selection, drawing more from the
   longer lists (OpenProject 45, Zulip 29, Grist and WeKan 19).
3. Accept about 22 eligible requirements and report H-b as estimation alongside H-c.
4. Keep H-b confirmatory only if the sample reaches the size needed for the smallest H-b
   effect judged worth detecting (to be fixed before freezing; see the planning table).

## Deviations, exclusions and missing data

- Generation failures, invalid suites and runner errors are unsound, never retried.
- Technical failures in the H1 runs keep their status; they do not create or remove
  mutants.
- Any change to scripts, eligibility or testers after the first call is a deviation
  with date and reason.

## Open items before freezing

1. Tester list and budget ([DECIDE]).
2. Whether the target of 40 applies to admitted or to QP4-eligible requirements.
3. The deterministic assertion-target check proposed as triage: specification and
   validation on public suites; it does not replace the blind human audit.
4. Training exposure. The protocol must not claim that requirements post-date the
   generators' or testers' training cutoff: provider aliases have no authenticated
   cutoff, and public dates do not prove absence of exposure. Default wording: the
   requirements come from the frames registered in #177, and training exposure is
   unknown. Codex proposed (28/10) adding a documentary window that starts after the
   prospective freeze; it would have to be a new registered frame (the #177 frames end on
   2026-09-30), and with collection planned from 15/11 it would contain only a few weeks of
   documentation changes, so its feasibility must be checked before deciding.
5. Claims about source versus model or number of testers are limited to the testers and
   budgets observed (pairing within requirement does not license a universal ranking).
6. Literature positioning against Konstantinou, Tambon and Papadakis (arXiv 2607.05139),
   Haeri and Ghelichi (arXiv 2607.06636), TestSuiteBench (arXiv 2610.13065), TiGanEval,
   TRACE and VerifierBench.
