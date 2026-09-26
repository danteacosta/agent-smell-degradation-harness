# E2E evidence matrix — 25 September 2026

The exploratory program now contains informative browser outcomes in six
projects. The rows below are a synthesis of separate pilots, not one pooled
experiment. Their scaffolds, requirements, denominators, and collection dates
differ, so totals must remain inside each row.

| Project | Observable obligation | Informative contrast | What was observed |
| --- | --- | --- | --- |
| TodoMVC | Focus the new-item field when the page opens | A/B versus C, two models | A and B each had 0/6 focus failures; C had 6/6 overall, three per model. |
| RealWorld | Show Delete Article only to the article author | A versus C by model | Luna: A 0/3 and C 3/3 failures. Sol: A 1/3 and C 0/3 failures. |
| Kanboard | Completing a task completes unfinished subtasks | A versus C under Luna | A passed 3/3; C had two target failures and one unknown. |
| Paperless-ngx | Dropping a file anywhere creates a visible document row | A/B/C by model, fixed scaffold | Sol: A and B passed 3/3; C failed 3/3. Luna passed all arms. |
| Nextcloud | Restoring a deleted file returns it to the visible file list | A/B/C by model, fixed scaffold | Sol: A and B passed 3/3; C failed 2/3. Luna passed all arms. |
| OpenProject | Saving Work copies it to Remaining work | A/B/C by model, fixed scaffold | C failed 3/3 under both models. Luna A/B passed 3/3; Sol A had two passes and one invalid output, while B passed 3/3. |

Across the three-project fixed-scaffold successor, 53 of 54 outputs were
executable. All 17 evaluable A outputs and all 18 B outputs passed. C produced
11 target-only failures among 18 executions, with no mixed or non-target
failure. Project-weighted C−A was +33.3 percentage points for Luna and between
+77.8 and +88.9 points for Sol. The bounds account only for the one invalid A
output and are not confidence intervals.

This matrix supports a bounded claim: removing an obligation can cause a
visible behavioral defect, and the effect can depend strongly on model and
context. It does not support a population prevalence or average causal effect.
Projects and obligations were selected purposively, repetitions are nested,
and the fixed-scaffold successor was designed after an earlier interface
failure. H1 and H2 remain open.

The measured E2E endpoint is the A/B/C target-failure contrast. It does not
estimate `H1.ordinal_delta`, whose outcome is human/adjudicated ordinal
severity. Before the next confirmatory freeze, browser failure must be assigned
explicitly as primary, co-primary, or construct-validation evidence, and the
chosen estimand must receive its own scale-appropriate precision analysis. No
retrospective relabeling of these pilots can make them estimates of the formal
H1 outcome.

The next collection should increase the number of independently sourced,
previously unexecuted obligations within projects instead of adding repetitions
to these six cases. The screened 12-slot pool contains 11 such obligations and
one TodoMVC persistence bridge replication. That bridge must be analyzed as a
replication and cannot count toward new requirement diversity. A defensible
block retains A/B/C and both models, qualifies each oracle with target and
non-target mutants before generation, and analyzes requirement-level effects
with project and model as grouping factors. Existing pilots remain a separate
exploratory stratum.

Evidence:

- TodoMVC focus chain: `data/focus-chain/results-20260922.json`
- RealWorld author visibility: `data/behavioral-expansion/realworld-author-ui-results-20260925/`
- Initial four-project expansion, including Kanboard: `data/e2e-six-projects/results-20260925/`
- Fixed-scaffold successor: `data/e2e-three-project-successor/results-20260925/`
