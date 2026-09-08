# Whole-context comparison: complete development, failed scope gate

The v4/v5 comparison completed all 48 development calls at US$0.032449, with
verified usage and no pending accounting. All responses met the evidence
interface contract. The preselected v5 candidate failed one required partial-scope
decision, so none of the 96 evaluation calls was dispatched. Main collection
remains blocked. This is a completed negative development result.

The [approved comparison](qualified-evidence-comparison.md) kept source context
contiguous and supplied identical revised inputs to both arms. V5 added an
instruction to check every required qualifier. The parser, construction answers,
thresholds, provider configurations and spending caps remained fixed.

## Planned-denominator results

Each row contains six dependent variants from each of two development source
locators, not twelve independent requirements. Provider aliases are local to
this study; their configuration identities remain private.

| Provider | Arm | Completed | Valid | Exact construction vectors |
| --- | --- | ---: | ---: | ---: |
| 1 | v4 | 12/12 | 12/12 | 11/12 |
| 1 | v5 | 12/12 | 12/12 | 12/12 |
| 2 | v4 | 12/12 | 12/12 | 12/12 |
| 2 | v5 | 12/12 | 12/12 | 11/12 |

Both arms matched 23/24 vectors. All 24 matched pairs were valid: 22 matched
in both arms, one only in v4 and one only in v5. Aggregate-label matches had
the same counts. This run does not demonstrate an overall advantage for v5.

Provider 1's v4 mismatch was `uncertain` on a construction-defined long omission;
v5 returned the expected `omitted`. Provider 2's v5 mismatch went in the other
direction: it returned `omitted` where a partial observation required `uncertain`.
The absent excerpt cannot establish whether the complete artifact omitted that
condition. This was an unsupported omission judgment, not false coverage.

The gate requires both providers to satisfy every specified long-omission and
partial-scope control. The second mismatch fails that rule. Selecting v5 for
provider 1 and v4 for provider 2 after inspecting these results would be a new,
unvalidated selection policy, not a pass of the registered comparison.

## Interpretation and remaining limits

The evidence interface is usable on these development cases, but reliable
distinction between complete-scope omission and incomplete observation remains
unresolved. The new instruction improved one provider's observed omission
decision while another provider made a scope error. One call per configuration
and case cannot establish a reproducible causal effect of the prompt.

The instruction's final uncertainty restriction is not explicitly limited to
complete observation, which warrants a post-hoc scope review. This is a plausible
instruction conflict, not a demonstrated account of the model's reasoning.
Do not change the frozen prompt or rescore this result. Any further prompt
revision needs a separate prospective design, freeze and collection decision.

Construction answers remain AI-assisted, without independent human calibration.
Source-derived controls and valid citations do not establish natural-artifact
ground truth, H1/H2, degradation prevalence or early-warning benefit.

## Accounting and preservation

V4 cost US$0.014151 and v5 US$0.018298. Cache usage differed, so these observations
do not isolate the prompt's effect on cost. Amounts use verified tokens at frozen
rates, not invoices or current provider balances.

The parent pilot and three auxiliary studies total 312 completed calls and
US$0.146193. This subtotal excludes the earlier pre-pilot and other comparisons.
The older unresolved US$0.000218 remains retained. Current shared commitments
are US$6.849510, including remaining reservations and contingency; the failed
gate does not automatically release them.

All 16 bound historical custody files were verified unchanged. Raw inputs,
responses, hashes, journals and the original collection runtime remain private
and preserved. The subsequent PR #49 portability fix belongs to the integrated
software, not the frozen collection runtime. Reproduce the historical report
from its preserved worktree; do not apply later source changes there.
