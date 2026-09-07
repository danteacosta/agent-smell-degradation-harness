# Scope-aware evaluator: development gate failed

The separately frozen v2/v3 development comparison completed **48/48 calls** on
7 September 2026. Usage-priced cost was **US$0.023175**. Every call had verifiable
usage and cost; there is no pending charge in this study's ledger. The gate
failed, so **none of the 96 evaluation calls were dispatched** and the main
pilot remains paused.

This is a completed negative development result, not an interrupted collection.
The [design](../plans/2026-09-07-scoped-judge-study.md) fixed the gate before
collection. The [runner contract](scoped-judge-study.md) preserves the failed
parent run and prevents a new budget or an automatic main-cohort release.

## Planned-denominator results

Two source locators, one per project, generated six dependent control variants
each. Both providers evaluated both arms once. Each row below therefore has
12 planned calls, not 12 independent requirements.

| Configuration | Valid responses | Valid and construction-matching | Invalid responses |
| --- | ---: | ---: | ---: |
| OpenAI, v2 | 7/12 | 5/12 | 5/12 |
| DeepSeek, v2 | 7/12 | 5/12 | 5/12 |
| OpenAI, v3 | 6/12 | 6/12 | 6/12 |
| DeepSeek, v3 | 5/12 | 5/12 | 7/12 |

The v3 gate required every response to be valid, at least 10/12 aggregate
construction matches per provider, and success on all omission and partial-scope
controls. Neither provider passed. All valid v3 responses matched their
construction oracle, but excluding invalid responses would hide half or more of
the planned observations. The 512-token allowance did not by itself solve output
reliability; no response exhausted it (the largest used 178 output tokens).

The operation-level counts below retain both planned source cases in every cell.
Each entry is **valid and construction-matching / planned**, not correctness
conditional on receiving valid output.

| Operation | OpenAI v2 | DeepSeek v2 | OpenAI v3 | DeepSeek v3 |
| --- | ---: | ---: | ---: | ---: |
| Concise complete | 1/2 | 0/2 | 1/2 | 1/2 |
| Distributed complete | 1/2 | 1/2 | 1/2 | 1/2 |
| Long omission | 0/2 | 1/2 | 1/2 | 0/2 |
| Partial missing | 0/2 | 0/2 | 1/2 | 1/2 |
| Partial complete | 1/2 | 1/2 | 1/2 | 1/2 |
| Partial contradiction | 2/2 | 2/2 | 1/2 | 1/2 |

All six OpenAI and five DeepSeek valid v3 responses came from the same second
source locator. Their complete per-obligation status vectors also matched the
construction answers. The other locator yielded no valid v3 response. Reporting
only valid-output accuracy would therefore hide a source-specific exclusion,
not merely reduce the sample size randomly.

## Two distinct evidence failures

Twelve of the 24 v3 responses exceeded the 120-character quote limit. They all
belonged to the same source locator, whose two contextual clauses are longer
than that limit. Models repeatedly copied the full clause instead of choosing a
shorter excerpt. The limit is an output contract, not a scientific definition
of semantic correctness. This concentration matters more than an aggregate
invalid percentage suggests.

Two DeepSeek v3 responses quoted text absent from the artifact but present in
the reference. One also violated the length limit. In the long-omission case,
the cited phrase named the very obligation removed from the artifact. This is
a grounding failure that a larger quote allowance would not repair.

These are response-level counts with overlap: twelve length failures plus two
absent-quote failures account for thirteen invalid v3 responses, not fourteen.
No excerpt was clipped, substituted or accepted retrospectively.

## Secondary diagnosis, excluded from the gate

A post-collection inspection considered the raw coverage statuses separately
from evidence validation. OpenAI v3's statuses matched 12/12 construction
answers; DeepSeek v3's matched 10/12. On the two partial-missing cases, their raw
statuses were uncertain in 2/2 and 1/2 cases respectively, versus 0/2 for each
v2 comparator. This suggests that explicit scope can help on these development
cases, but the strict valid-response results above remain authoritative.

This inspection is post hoc, uses author-defined construction answers, and does
not rescue the failed gate. V3 changes scope instructions, obligation inventory
and response representation together. The experiment cannot isolate which
component caused a difference or estimate general sensitivity from two sources.

## Implications and next decision

The result separates three questions: whether a model selected the intended
status, whether it supplied usable evidence, and whether the underlying oracle
represents the natural requirement correctly. Only the first two received a
limited construction-based diagnostic here. Independent semantic validity and
H1/H2 remain unresolved.

A sensible next design would return references to immutable artifact segments
instead of asking models to copy and count characters. The harness could then
resolve those references mechanically, keeping reference text outside the
artifact-evidence namespace. That would remove a transcription failure mode,
but would not prove that the selected segment entails the obligation. It needs
a separately reviewed protocol and new version; it is not implemented as a
silent repair or evaluated on the locked cases in this study.

For the advisor meeting, the defensible finding is that the instrument now
exposes where its judgments fail, and that apparently correct statuses can lack
acceptable supporting evidence. Main-cohort collection should wait for a new
documented diagnostic decision, not a retrospective relaxation of this gate.

The shared pilot accounting now contains 216 completed calls across the parent
and auxiliary ledgers, totaling US$0.085720 at the frozen rates. The earlier
pre-pilot and other comparison studies are separate; this is not total research
spending or an invoice. The historical US$0.000218 unresolved reservation remains
held separately and was included conservatively in the auxiliary budget check.
