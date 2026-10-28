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
  incomplete-source suites (per-requirement difference > 0).
- **H-b.** The union of all testers' incomplete-source suites detects fewer confirmed
  losses than one tester's complete-source suites (difference < 0).
- **H-c.** Across requirements, generator recovery and incomplete-source detection
  (mean over testers) are positively associated.

## Analysis

- H-a and H-b: equal weight per requirement; two-sided exact project sign-flip test;
  95% project bootstrap interval; support requires the predicted sign and rejection
  after Holm correction over {H-a pooled over testers, H-b} at 0.05. Per-tester H-a
  results are reported without being counted as separate confirmations.
- H-c: Spearman ρ with a two-sided permutation test within projects and a project
  bootstrap interval. **Estimation only**: reported with its interval, not used as a
  confirmatory claim (see power below).
- Scripts: `scripts/mutation_adequacy.py` and `scripts/verifier_coupling.py`, frozen by
  hash before collection; any change after unblinding is reported as a deviation.
- Sensitivities: assertion alarms only; excluding the code_incomplete shown mutant;
  per-tester results.

## Planning simulation

`scripts/qp4_prospective_power.py` resamples the 25 exploratory requirements
(`data/confirmatory-planning/qp4-prospective-power.json`, 1,000 replications per cell).
Projects are clusters of resampled requirements, so real between-project heterogeneity
is not modelled, and observed effects come from post hoc analyses.

| Requirements / projects | H-a observed | H-b observed / halved | H-c observed / halved |
|---|---:|---:|---:|
| 25 / 8 | 1.00 | 0.71 / 0.64 | 0.82 / 0.28 |
| 40 / 8 | 1.00 | 0.91 / 0.89 | 0.98 / 0.43 |
| 40 / 10 | 1.00 | 0.92 / 0.93 | 0.98 / 0.43 |
| 60 / 12 | 1.00 | 0.99 / 0.99 | 1.00 / 0.60 |
| 80 / 12 | 1.00 | 1.00 / 1.00 | 1.00 / 0.75 |

"Halved" scales the H-a/H-b differences by 0.5 and, for H-c, replaces about half of the
detection values with values from other requirements. Reading: about 40 eligible
requirements in at least 8 projects are enough for H-a and H-b even with halved effects;
H-c would need roughly 80 or more under attenuation, so it stays as estimation. Note
that the eligible QP4 sample is smaller than the admitted H1 sample (exploratory: 25 of
46), so 40 eligible requirements may require more than 40 admitted.

## Feasibility of the eligible sample

In the 46-case collection, 25 requirements (54%) were QP4-eligible: 17 had no confirmed
mutant in their four arm-C implementations and 4 had a mutant but no correct A.
With the planned 8 × 5 design, about 22 eligible requirements are expected, which the
simulation puts at power 0.71 for H-b with observed effects (0.64 halved). Reaching
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
4. Literature positioning against Konstantinou, Tambon and Papadakis (arXiv 2607.05139),
   Haeri and Ghelichi (arXiv 2607.06636), TestSuiteBench (arXiv 2610.13065), TiGanEval,
   TRACE and VerifierBench.
