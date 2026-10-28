# Options for Dante and Márcio: smallest H-b effect of interest and eligible sample

Date: 2026-10-28. Status: **decision sheet, no decision taken.** It lays out options,
consequences and open questions. It does not choose an effect, a sample size, testers or
a budget. Nothing here changes H1, H2, the #177 selection, the frozen materials or τ².
Inputs: `docs/preregistration/2026-10-28-qp4-tester-extension-draft.md`,
`data/confirmatory-planning/qp4-prospective-power.json` (simulation v2, corrected after
review by Codex), `data/verifier-coupling/v1/results.json`. All effect sizes below come
from post hoc analyses of 25 requirements in 8 projects.

## What H-b compares

Per requirement: share of oracle-confirmed losses detected by the union of k testers'
suites written from the incomplete request, minus the share detected by one tester's
suites written from the complete requirement (mean over testers). H-b predicts a negative
difference. Observed, by the number of pooled testers k:

| k pooled incomplete-source testers | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|
| union detection, incomplete request | 0.179 | 0.311 | 0.403 | 0.464 | 0.500 |
| minus one complete-source tester (0.824) | −0.645 | −0.513 | −0.421 | −0.360 | −0.324 |

**Consequence:** the H-b effect is not one number; it shrinks as k grows. The tester list
(how many testers are pooled) has to be fixed before the smallest effect of interest can
mean anything, and the simulation used k = 5.

## Decision 1: the smallest H-b effect worth detecting

Three ways to anchor it, each with what it implies. The figures are from the corrected
simulation (Holm over H-a and H-b, project heterogeneity τ = 0 or 0.10); only two effect
levels were simulated, so other levels would need a new offline run.

| Anchor | Smallest effect (k = 5) | Power at ~22 eligible (25 simulated) | at 40 | at 60–80 | What it implies |
|---|---:|---:|---:|---:|---|
| A. The exploratory estimate | −0.32 | 0.65–0.68 | 0.83–0.92 | 0.97–1.00 | Treats a post hoc estimate from a selected sample as the target; likely optimistic |
| B. Half the exploratory estimate | −0.16 | 0.21–0.23 | 0.27–0.37 | 0.49–0.67 | A hedge against selection and winner's curse; not reachable with the planned sample |
| C. A practical threshold (for example: pooling counts as a substitute if it comes within 0.10 of one complete-source tester) | not simulated | — | — | — | Ties H-b to a reviewer-relevant claim; requires defining the threshold and running the simulation for it |

Open questions for Decision 1:
- Which claim should H-b support: "pooling does not reach a complete-source tester" (a
  superiority test, as now), or "pooling is not within a practical margin" (which would
  need a margin and a different test)?
- Is k = 5 testers the planned design, given the budget? With fewer testers, the effect is
  larger (−0.51 at k = 2) but the claim is about a smaller pool.
- Should the effect of interest be set on the scale of detection differences (as now) or
  on the joint escape (loss × miss)?

## Decision 2: the eligible sample

Eligibility (as in `scripts/mutation_adequacy.py`): at least one correct arm-A
implementation and at least one oracle-confirmed arm-C loss. Exploratory rate 25 of 46
(54%); with 8 × 5 admitted, about 22 eligible are expected. The frozen #177 order lists
10 (Paperless), 11 (Mattermost) and 13 (Immich) provisional admissions before
qualification losses.

| Option | What changes | Consequences | Open questions |
|---|---|---|---|
| 1. More arm-C draws (e.g. 8 instead of 4) | Generation budget for arm C doubles | A rough Jeffreys-prior projection from the 46 cases moves expected eligibility from about 0.67 (four draws) to 0.76 (eight); the observed rate with four draws was 0.54, so the projection is optimistic, especially for rules never lost in four draws; also reduces the truncation that limits H-c | Budget; whether H1 analyses must weight the extra draws differently; registered before any generation |
| 2. Unequal targets per project | Draw more from longer lists (OpenProject 45, Zulip 29, Grist and WeKan 19) | More eligible requirements without more draws per requirement; projects become unequal in weight; the project sign-flip test keeps its unit (project) | Must be registered before selection; does it change H1's planned 8 × 5? |
| 3. Keep 8 × 5 and report H-b as estimation | No change to collection | H-b gives an interval, not a confirmatory claim; H-a remains confirmatory | Does a paper with only H-a confirmatory meet the ISSTA goal? |
| 4. Keep H-b confirmatory only if the sample reaches the size needed for the effect chosen in Decision 1 | Couples the two decisions | Under anchor A, ~40 eligible suffice in simulation; under B, even 80 do not reach 0.8 | Needs Decision 1 first; feasibility against #177 lists and the 15/11–15/12 window |

## What stays fixed regardless

- H1 and H2 as registered; H2's T1–T3 recorded in the same runs.
- The 25-requirement, 8-project exploratory results stay post hoc; they motivate, not
  confirm.
- Outcomes keep the distinction between zero (a valid failing result) and None/unknown
  (technical absence); unknowns are never imputed.
- The #185 blind human audit stays pending; mechanism claims stay conditional on it.
- No pilot, generation or τ² activity is implied by this sheet.

## Questions to settle in one meeting

1. Tester list and k for H-b (and budget).
2. Smallest H-b effect of interest, or a practical margin with a different test.
3. Eligible-sample option (1–4), registered before selection.
4. Whether H-b stays confirmatory or moves to estimation if (2) and (3) do not meet.
