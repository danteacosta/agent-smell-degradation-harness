# Whole-context v4/v5 evaluator comparison

This separately authorized auxiliary tests obligation completeness without
rewriting the failed [v3/v4 result](addressed-comparison-results.md). It preserves
the complete source context and compares the existing v4 instruction with v5's
explicit check of every required qualifier. Both arms receive identical revised
cases. The [approved design](../superpowers/specs/2026-09-07-qualified-evidence-design.md)
and [implementation plan](../superpowers/plans/2026-09-07-qualified-evidence.md)
define the contract before collection.

## What changes

The historical builder inserted an obligation at the midpoint of source lines.
On the two development contexts, this interrupted a table header/separator and
a wrapped list instruction. The revised layout places the first obligation,
then the entire unchanged context, then the remaining obligations. Distributed
complete and long-omission variants use this rule uniformly. Other controls,
reference obligations, target index and construction answers remain unchanged;
every case receives a versioned identity with private lineage.

V5 requires the evaluator to check all required actors, interfaces and conditions.
Related functionality does not establish an unspecified qualifier. Under complete
observation, missing support is omission; genuinely ambiguous wording may remain
uncertain. Partial observation keeps the existing rule. The evidence parser is
unchanged: segment IDs prove location and byte integrity, not semantic support.

This comparison isolates v4/v5 instructions within the revised layout. It cannot
attribute differences from the earlier run to the prompt alone. Construction
answers remain AI-assisted, with no independent human calibration.

## Fixed collection and decision

| Phase | Source locators | Operations each | Arms | Providers | Calls |
| --- | ---: | ---: | ---: | ---: | ---: |
| Development | 2 | 6 | 2 | 2 | 48 |
| Conditional evaluation | 4 | 6 | 2 | 2 | 96 |

These are dependent variants, not 144 independent requirements. V5 is the
preselected candidate; v4 cannot replace it after results are observed.
For each provider and phase, every candidate response must be valid, at least
5/6 of full status vectors must match construction answers, and every long
omission, partial missing, partial complete and partial contradiction must match.
Every planned call needs a reconciled receipt. Invalid baseline judgments remain
visible but do not change the candidate rule. A missing baseline receipt blocks
the gate.

Development failure prevents all 96 evaluation calls. Evaluation failure is
preserved without a replacement prompt, extra repetitions or repaired responses.
Even two passing phases release only this auxiliary, never main collection.

## Private preparation and execution

Keep the original runtime and all predecessor evidence in place. From a clean,
verified successor runtime, use `eval.qualification_plan.prepare_plan` with the
failed predecessor directory and its frozen runtime directory. Persist the
returned plan with the existing exclusive private writer; `summary` provides
redacted counts and budget arithmetic without dispatching a provider call.

The CLI takes absolute paths supplied by the operator:

```sh
python -m eval.qualification_live prepare --directory PRIVATE_RUN --approved-plan PRIVATE_PLAN --approve-live
python -m eval.qualification_live development --directory PRIVATE_RUN --env-file PRIVATE_ENV --approve-live
python -m eval.qualification_live report --directory PRIVATE_RUN
```

Only after `phases.development == "pass_auxiliary_only"`:

```sh
python -m eval.qualification_live evaluation --directory PRIVATE_RUN --env-file PRIVATE_ENV --approve-live
```

The coordinator rechecks this rule itself. Editing a saved report cannot open
the gate. Phase exit code 0 means the auxiliary rule passed; 2 means pause or
failure. Report and preparation success use exit code 0 without implying a
scientific pass. Provider calls are sequential, reserved before dispatch and
have no hidden SDK retries. Resume skips reconciled calls. Missing usage or an
interrupted reservation blocks further dispatch rather than repeating the call.

## Custody and budget

A separate exclusive closure transfers only the failed predecessor's unused
direct allowance and contingency. Actual spending, ancestor reservations,
ancestor contingency and the earlier unresolved US$0.000218 remain retained.
Shared commitments must stay within US$7 and cumulative auxiliary commitments
within US$1. These protocol limits are not API account balances.

The frozen predecessor report runs read-only in its preserved runtime with no
inherited provider credentials or import path. Its import path is explicitly
bound to the verified runtime directory. File and source snapshots are checked
before and after that read. The successor acquires ancestor locks in order,
rechecks custody, and publishes its claim last. Partial preparations and missing
journals are never silently recreated; claims are not reset or overwritten.

Private records retain the cases, prompt/configuration/source hashes, closure,
responses, usage, cost, latency and append-only journal. Public reports expose
opaque provider/source/project groups, full planned denominators, missing and
invalid counts, jointly valid pairs, and phase decisions. Cost uses verified
usage at frozen rates, not invoice reconciliation. No result here estimates
human validity, H1/H2, natural degradation prevalence or early-warning benefit.

Run packaging checks in a separate source staging directory, not inside the
scientific runtime. Build-generated distribution metadata can change the frozen
environment inventory even when no dependency is installed.
