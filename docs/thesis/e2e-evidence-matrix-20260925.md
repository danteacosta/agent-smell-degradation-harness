# E2E evidence matrix — through 26 September 2026

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

## 26 September: second OpenProject obligation

The [prospectively frozen Remaining work pilot](../research/openproject-remaining-pilot-20260926.md)
adds a **second obligation within OpenProject**, not a seventh project or an
additional observation of the earlier copy-Work obligation. With Work already
set, entering % Complete should derive Remaining work. In 18/18 evaluable
browser executions, A and B passed 3/3 per model and C failed only this target
3/3 per model. Two numeric fixtures were checked after save and reload.
The [post-outcome label audit](../research/openproject-remaining-label-audit-20260926.md)
records two revised-prompt LLM reviewers agreeing with all 18 browser labels
and one reviewer disagreeing on five passing outputs. Its prompt revision was
post hoc; browser outcomes remain primary.

This updates the descriptive count to **six projects with informative E2E
evidence, including two distinct OpenProject obligations**. The pilots are
separate strata and cannot be pooled into a population effect. Of the 12-slot
screened pool below, ten previously unexecuted obligations remain after this
pilot, plus the TodoMVC persistence bridge replication. Candidate admission
alone is not an E2E outcome.

The next collection should increase the number of independently sourced,
previously unexecuted obligations within projects instead of adding repetitions
to these cases. The screened 12-slot pool originally contained 11 such
obligations; OpenProject Remaining work has now been executed, leaving ten.
The TodoMVC persistence bridge must be analyzed as a
replication and cannot count toward new requirement diversity. A defensible
block retains A/B/C and both models, qualifies each oracle with target and
non-target mutants before generation, and analyzes requirement-level effects
with project and model as grouping factors. Existing pilots remain a separate
exploratory stratum.

## 26 September: second Kanboard obligation

The [duplicate-title pilot](../research/kanboard-duplicate-title-qualification-20260926.md)
adds a second obligation in Kanboard, in a different interaction from
completing unfinished subtasks. All 18 code generations passed the frozen
HTML admission check. The original browser run had seven passes, two
target-only C failures, and nine unknown browser errors. Every unknown used
`crypto.randomUUID()`, unavailable at the frozen fixture origin. These are
not evidence of a title defect. The original planned-denominator C−A
target-failure difference was +2/6; unequal unknowns prevent a clean
interpretation.

A separately qualified, **post-outcome** diagnostic changed only the runner
origin to `localhost` and re-evaluated the same saved artifacts, with no new
model calls. It yielded 16 passes and the same two C title failures. Luna
had two C failures in three runs, while Sol passed C in all three. The two
failures appended `(Copy)`/`(copy)` to the duplicated title; A and B passed
3/3 in each model. This explains the original unknowns but is not a
prospectively frozen replacement result. It leaves the project count at six,
with two distinct obligations now executed in both Kanboard and OpenProject.
Nine of the original 11 previously unexecuted obligations remain, plus the
TodoMVC persistence bridge replication. The formal H1/H2 outcomes remain
unmeasured.

Evidence:

- TodoMVC focus chain: `data/focus-chain/results-20260922.json`
- RealWorld author visibility: `data/behavioral-expansion/realworld-author-ui-results-20260925/`
- Initial four-project expansion, including Kanboard: `data/e2e-six-projects/results-20260925/`
- Fixed-scaffold successor: `data/e2e-three-project-successor/results-20260925/`
- Second OpenProject obligation: `data/e2e-openproject-remaining/results-20260926/`
- Second Kanboard obligation, original and post-outcome diagnostic:
  `data/e2e-kanboard-duplicate-title/results-20260926/` and
  `data/e2e-kanboard-duplicate-title/secure-origin-diagnostic-20260926/`

## 26 September: later qualified obligations

The [new Kanboard replication](../research/kanboard-duplicate-title-qualification-20260926.md#nova-replicação-prospectiva-com-origem-segura)
ran 18 fresh generations under a qualified origin: A/B passed 6/6 each,
while C had two selective title failures and four passes. This replaces no
earlier outcome and adds no requirement diversity.

The [Paperless duplicate-consumption pilot](../research/paperless-duplicate-consumption-20260926.md)
added a third previously unexecuted obligation in the planned block. A/B
passed 12/12 and C had four selective failures in six evaluable outputs.
Its first 18-generation lot remains an instrument failure, not part of that
contrast.

The [RealWorld favorites-route pilot](../research/realworld-favorites-20260926.md)
added a fourth obligation but **no observed omission effect**: its qualified
successor had 18/18 evaluable outputs, with A/B/C each passing 6/6. The
models reconstructed the favorites rule in C from the route and common data
schema. Its first 18-generation lot also remains a separate instrument
failure. The evidence matrix now includes a successful recovery case alongside
selective defect cases. Seven planned new obligations and the TodoMVC bridge
remain; the project count stays at six. These selected, separate pilots do not
estimate formal H1 or test H2.

The [TodoMVC persistence bridge](../research/todomvc-persistence-bridge-20260926.md)
has now run with a prospectively qualified selector and 18 fresh generations.
A/B passed 6/6 each. C passed 5/6, while one C output was an interface error
before the target could be assessed. There was no observed target failure in
the five evaluable C outputs. This is a replication of an existing obligation,
not a fifth new requirement; seven planned new obligations remain.
