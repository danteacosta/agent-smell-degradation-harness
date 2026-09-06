# Judge prompt comparison: incomplete collection and schema diagnosis

The revised evaluator detected all deletion controls in a separate 16-call
schema-repair smoke, but the larger comparison remains incomplete. The small
smoke does not validate the earlier natural-artifact labels or establish H1/H2.

PR #40 was merged as `3383f1fd1efa7430741b444455887ea1dfca47d9`.
The comparison used source `09b46c87abe9c34ade9c2a82157efd456dfcd74f`,
with the [plan](judge-prompt-comparison-plan.md) committed before collection.
The [protocol](judge-prompt-comparison.md) describes the two arms and controls.

## Collection status

The 288-call plan stopped after 274 attempts. There were 273 received responses,
one ambiguous OpenAI call without verifiable usage, and 14 unattempted calls.
The stop state is `stopped_cost_unverified`; no retry or resume was performed.
Reconciled cost is US$0.044971 at the frozen rates. A further US$0.000218 remains
reserved for the ambiguous attempt. This is not a fully reconciled final bill.

Of the received responses, 196 satisfied their arm's schema and 77 did not.
The report counts the failed call separately from the 14 missing calls; its
combined invalid-or-failed total is 78. Zero pending attempts does not mean
zero unresolved cost: the in-flight reservation remains held.

## Planned-denominator results

Each row has 72 planned occurrences: 24 development and 48 newly authored.
The new-deletion denominator is 12 occurrences over six templates.

| Configuration | Valid responses | Correct / planned | Invalid or failed | Not attempted | New deletions correct / planned |
| --- | ---: | ---: | ---: | ---: | ---: |
| OpenAI, historical prompt | 66 | 37/72 | 1 | 5 | 0/12 |
| OpenAI, evidence v1 | 61 | 61/72 | 7 | 4 | 9/12 |
| DeepSeek, historical prompt | 69 | 41/72 | 0 | 3 | 0/12 |
| DeepSeek, evidence v1 | 0 | 0/72 | 70 | 2 | 0/12 |

For OpenAI evidence v1, the new deletion subset contains nine correct valid
responses, two invalid responses and one unattempted call. Its historical arm
has zero correct out of eleven valid deletion responses, plus one missing call.
Do not report the evidence result simply as 100% deletion sensitivity.

All 61 valid OpenAI evidence responses matched their construction oracle, and
their excerpts passed the literal grounding check. On complete controls there
were zero false alarms among 32 valid responses, with two invalid and two
unattempted positive occurrences. Thus there is a promising instrument signal,
but excluding invalid/missing observations would overstate reliability.

DeepSeek evidence v1 has no valid response on which to estimate semantic
accuracy or false-alarm rate. Its zero-correct count is a contract failure,
not evidence that every underlying semantic judgment was wrong.

## Schema failure diagnosis

All 138 received evidence-arm payloads were JSON objects with the requested
three keys and string excerpts within the length bound. The failures concerned
the allowed values: 62 DeepSeek and five OpenAI responses interchanged coverage
and severity fields. Eight other DeepSeek responses used unregistered labels
(seven `contradiction`, one `contradicts`); two other OpenAI responses put a
criterion description in `label`.

The v1 prompt defined coverage and severity but did not explicitly bind their
enumerations to `status` and `label`. The strict parser correctly rejected these
responses. The recorded v1 scores are not repaired by swapping fields or
reinterpreting labels after collection.

## Interpretation

Explicit comparison instructions with an evidence requirement produced a useful
signal in the valid OpenAI responses. The evidence v1 contract was nevertheless
not operationally reliable across providers. Incomplete collection, unequal
missingness, only six new templates and author-defined construction oracles
limit the comparison. Changes to instructions, formatting and evidence output
are combined; no individual causal mechanism has been isolated.

The earlier 279 clean / 9 uncertain natural-artifact distribution remains
unvalidated. Neither this comparison nor a repaired-schema smoke can establish
human agreement, natural degradation prevalence or H1/H2.

## Separate schema-repair smoke

The v1 prompt and report remain preserved. Evidence v2 explicitly enumerates
the allowed values for each JSON key and forbids interchanging them. A separate
16-call smoke uses two new templates with literal and deleted variants, two
providers and two repetitions. It does not retry the ambiguous occurrence or
complete the interrupted comparison. Its result must be reported separately.

The smoke used source `714bd71` and completed 16/16 calls at a reconciled cost
of US$0.002708, with no failed, invalid, missing or unverified-cost attempt.
Both providers produced eight valid correct responses: four literal-coverage
and four deletion occurrences, across two templates repeated twice. There were
no false alarms or invalid evidence excerpts. This verifies the repaired
contract on a small smoke, not general sensitivity or natural-language validity.

Total reconciled cost across the comparison and smoke is US$0.047679. The
original US$0.000218 unresolved reservation is still separate; it was not
released, silently retried or declared reconciled by the second experiment.

Next: reconcile that ambiguous attempt and freeze a larger evidence-v2
comparison with additional new templates before collecting more outcomes.
The first comparison's cases are development material now. Do not promote the
prompt automatically or overwrite natural-artifact labels after this smoke.
