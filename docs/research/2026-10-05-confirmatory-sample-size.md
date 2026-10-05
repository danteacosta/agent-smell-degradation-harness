# Confirmatory H1a sample-size simulation

Status: exploratory planning, not a confirmatory result. Script:
`scripts/confirmatory_power.py`. Output:
`data/confirmatory-planning/power.json` (seed 2026100501). No model call is
made by this analysis.

## Simulation design

Each simulated study resamples projects from the nine-project exploratory
collection and then resamples requirements within each selected project. A
requirement keeps all of its evaluable A/C pairs (two models and two
replications). Forty-four of the 46 requirements have at least one evaluable
pair. The point estimate and project-cluster percentile interval use the
pre-registered `paired_probability_of_superiority` estimator.

Two perturbations reduce the optimism of resampling a dataset with no observed
C-better-than-A pair:

- **Effect attenuation.** Each C-worse pair becomes a tie with probability
  `q`. The grid represents the observed effect, effects around 0.60 and 0.55,
  and the null.
- **Symmetric reversals.** A pair is redrawn as worse or better with equal
  probability at rates 0.047 and 0.14. The first rate is the observed B/A
  wording discordance; the second is a stress scenario. This is a simple noise
  model, not an estimate of the future reversal rate.

## Independence-unit correction

The original draft used the estimator's requirement-level sign-flip p-value as
one of two confirmatory gates. That test requires independently exchangeable
requirement signs. Requirements from the same repository share a scaffold,
oracle family, model calls, and project context, so project bootstrap does not
make those signs independent.

Version 2 therefore reports two tests separately:

- `power_intent_p_below_05_optimistic`: the original requirement-level test,
  retained only as a diagnostic;
- `power_project_p_below_05`: an exact test that flips all centered
  requirement scores in one project together and enumerates all `2^G` project
  assignments.

The planning decision rule is now the conjunction of the exact project-level
test and a project-cluster bootstrap lower bound above 0.5. This correction
does not prove that the percentile interval has nominal 95% coverage with only
8–9 projects. Cameron and Miller (2015) show that inference with few clusters
is a finite-sample problem and recommend explicit small-cluster corrections;
they also caution that pairs-cluster bootstrap may still over-reject. The
current simulation must therefore be treated as a design sensitivity, not a
sample-size certificate.

## Reading the output

The regenerated JSON is the canonical table. For every design and effect
scenario it reports:

- the mean simulated estimate;
- the project-cluster interval decision rate;
- the optimistic requirement-level sign-flip rate;
- the exact project-level sign-flip rate;
- the rate at which both project-level conditions hold.

The regenerated grid materially changes the planning conclusion for an effect
around 0.60:

| Design | Requirements | Calls with A/B/C | Project-level power, noise 0.047 | Project-level power, stress noise 0.14 |
| --- | ---: | ---: | ---: | ---: |
| 8 projects × 3 | 24 | 288 | 0.808 | 0.619 |
| 8 projects × 4 | 32 | 384 | 0.917 | 0.756 |
| 8 projects × 5 | 40 | 480 | 0.960 | 0.835 |
| 8 projects × 6 | 48 | 576 | 0.976 | 0.907 |
| 9 projects × 4 | 36 | 432 | 0.966 | 0.865 |

The original requirement-level test had reported 0.949 power for 9×4 under
stress, close to the interval rate. The corrected project-level decision gives
0.865 and exposes the dependence that the original simulation hid. For an
effect around 0.55, even 8×6 reaches only 0.441 under stress.

The earlier recommendation of **9 projects × 4 requirements** is therefore
withdrawn. It is also infeasible in either frame currently proposed in PR #170
when used alone: the reserve frame has eight projects and the 2024 window has
seven. If the reserve frame is selected and the minimum effect of interest is
0.60, **8 projects × 5 requirements** is the smallest tested design above 0.80
under the stress model. The 2024 frame cannot satisfy the pre-registered
minimum of eight projects without being expanded or combined under a
prospectively frozen rule.

Applied retrospectively as a sensitivity only, the exact project-level
sign-flip p-value for the exploratory 46-case result is 0.00390625 (44
evaluable requirements, nine projects). This does not make that collection
confirmatory: selection, human-audit, provider and pre-registration gates still
apply.

## Limitations

- The resampling population is the exploratory sample itself. Its project and
  requirement heterogeneity may not represent the confirmatory frame.
- Designs with more than nine projects repeat observed projects and therefore
  cannot reveal additional between-project heterogeneity.
- The symmetric pair-noise model does not represent whole requirements or
  projects reversing direction.
- The project-level test has coarse resolution with few projects and assumes
  project-level sign symmetry under the null.
- Human manipulation/oracle audits, the model/provider freeze, and the final
  sampling-frame decision remain prerequisites for confirmatory collection.

## Reference

A. Colin Cameron and Douglas L. Miller. *A Practitioner's Guide to
Cluster-Robust Inference*. Journal of Human Resources 50(2), 317–372, 2015.
https://doi.org/10.3368/jhr.50.2.317
