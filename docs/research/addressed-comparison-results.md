# Artifact-addressed evaluator: usable citations, failed development gate

The frozen v3/v4 comparison completed **48/48 development calls** on 7 September
2026, costing **US$0.028024** at the frozen token rates. All calls have verified
usage and reconciled cost records; none is pending. The development gate failed,
so **0/96 evaluation calls were dispatched**. Main-cohort collection remains
blocked. This is a completed development result, not an interrupted batch.

The [comparison design](addressed-comparison.md) and
[live coordinator](addressed-comparison-live.md) fixed the inputs, response
contracts and phase gate before collection. Quote-based v3 and segment-ID v4
used matched source-derived cases. Historical responses were neither repaired
nor pooled with this comparison.

## Results against planned calls

Two development source locators, from two projects, each supplied six dependent
variants. Each provider evaluated every variant once under each arm. These are
12 planned calls per row, not 12 independent requirements. Provider slots below
are stable within this study; private configuration identities are not published.

| Provider slot | Arm | Completed | Valid evidence contract | Invalid | Valid and exact construction match |
| --- | --- | ---: | ---: | ---: | ---: |
| 1 | v3 | 12/12 | 6/12 | 6/12 | 6/12 |
| 1 | v4 | 12/12 | 12/12 | 0/12 | 11/12 |
| 2 | v3 | 12/12 | 4/12 | 8/12 | 4/12 |
| 2 | v4 | 12/12 | 12/12 | 0/12 | 12/12 |

An exact match requires the complete per-obligation status vector to match the
construction answer. Aggregate-label matches had the same counts in this run,
but are not interchangeable with vector matches. Contract validity establishes
that the response can be parsed and its evidence references resolved. It does
not establish that the cited text supports the obligation.

## Why evaluation stayed locked

The prospective v4 gate required, for each provider, 12/12 valid responses,
at least 10/12 exact vectors, and 2/2 exact vectors in each of four operations:
long omission, partial missing, partial complete and partial contradiction.
Both providers had valid output throughout. Provider 1 nevertheless matched
only **1/2 long-omission cases**, failing the mandatory operation-level rule.

In that case, the removed obligation received **`uncertain` instead of
`omitted`**. The other three obligation statuses matched. This was an abstention
on a construction-defined omission, **not a false `clean` judgment**. It still
fails the frozen detection criterion; the gate cannot be relaxed after seeing
which error occurred. Provider 2's pass cannot release evaluation alone because
the registered rule requires both providers to pass.

Across both providers, v4 matched 4/4 construction vectors in each other
operation: concise complete, distributed complete, partial missing, partial
complete and partial contradiction. Long omission matched 3/4. These small,
dependent counts describe these cases only, not population sensitivity.

## What improved, and what did not follow

The clearest observed gain is response/evidence-interface compliance: **24/24
v4 responses were valid, versus 10/24 v3 responses**. Against all planned
responses, v4 had 23/24 valid exact matches and v3 had 10/24. Fourteen invalid
v3 outputs remain in that denominator; they are not inferred semantic errors
or silently discarded observations.

Among the ten matched pairs where **both** arms were valid, nine were exact in
both arms. In the remaining pair, v3 matched the construction answer and v4
abstained. Thus this run does not demonstrate better semantic decisions among
jointly scorable responses. That subset is also selected by response validity
and cannot replace the planned-denominator comparison.

Segment IDs remove the need to copy evidence verbatim, but also change prompt
presentation and context length. This bundled treatment does not isolate a
causal effect of transcription. A resolvable citation can remain irrelevant.
Construction answers are AI-assisted, not independently validated human labels;
two source locators do not support general accuracy claims. H1/H2, semantic
degradation prevalence and the benefit of early warning remain unmeasured.

## Accounting and custody

V3 cost US$0.010545 and v4 cost US$0.017479. Cache-hit usage differed between
arms; this small run does not isolate the effect of the representation on cost.
These amounts use verified usage at frozen rates, not reconciled invoices or
current account balances. The [pricing check](2026-09-07-comparison-pricing-check.md)
records the rate basis.

All 18 recorded predecessor/parent custody files remained byte-identical.
The predecessor's unused allowance was handled through the approved separate
closure; its spending and the earlier unresolved US$0.000218 remain retained.
The new comparison still retains its unused evaluation reservation and
contingency. A failed gate does not automatically make those funds available
to another experiment. No ambiguous call was retried.

The parent and two auxiliary studies now contain **264 completed calls costing
US$0.113744**. This subtotal excludes the earlier pre-pilot and other comparison
studies. Raw inputs, outputs, configuration identities, hashes, closure and
append-only journals remain in approved private storage.

## Next decision

Preserve this failed version and do not execute its evaluation phase. The four
evaluation locators received no new comparison calls; prior background exposure
still prevents a claim that they are contamination-free. Review the abstention
and the construction rationale as a post-hoc diagnosis, without repairing the
score, changing the frozen prompt or converting locked cases into development
examples. Further collection needs a separately documented methodological and
budget decision, not an automatic retry to obtain a perfect score.

The result narrows the immediate problem: addressing made evidence usable on
these development cases, but did not satisfy every required omission decision.
The [advisor brief](advisor-brief-2026-09-08.md) separates that finding from the
still-unanswered thesis hypotheses and future product claims.
