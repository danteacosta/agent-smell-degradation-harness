# Expanded judge comparison: complete collection, improved control performance

The evidence-v2 prompt matched the construction oracle on all 96 planned
occurrences per provider. The historical prompt detected two of 24 omission
occurrences with OpenAI and none with DeepSeek. This supports further use of
v2 as an exploratory instrument on these control families; it does not validate
natural-artifact labels, human agreement or H1/H2.

## Design and collection

The [plan](judge-v2-expanded-plan.md) was committed before collection. Source
`dcf5060cd6104b3b7c23e6973bf660c07680923b` generated 48 controls over 12 new
templates: literal coverage, paraphrase, deletion and opposite behavior.
Two prompts, two providers and two repetitions produced 384 planned calls.
No previous control pack or response was reused; the v2 prompt was unchanged
from the separate schema-repair smoke. The new templates exercise familiar
constraint families and are not evidence of transfer to unseen domains.

Collection completed 384/384 calls. All responses satisfied their respective
schema. There were no missing calls, abstentions, retries or unresolved usage
events in this run. The two earlier reports and their ledgers remain unchanged.

## Results against construction oracles

| Provider and prompt | Correct / planned | Deletions detected | Opposite behavior detected | False alarms on complete/paraphrased cases |
| --- | ---: | ---: | ---: | ---: |
| OpenAI, historical | 55/96 | 2/24 | 5/24 | 0/48 |
| OpenAI, evidence v2 | 96/96 | 24/24 | 24/24 | 0/48 |
| DeepSeek, historical | 50/96 | 0/24 | 2/24 | 0/48 |
| DeepSeek, evidence v2 | 96/96 | 24/24 | 24/24 | 0/48 |

Both prompts accepted all 24 literal and all 24 paraphrased occurrences per
provider. Thus the observed improvement is not merely a change to always
predicting omission. The historical arm also produced 13 inconsistent
label/status pairs with OpenAI and 16 with DeepSeek. These are schema-valid
but not automatically correct judgments; they remain in the denominator.

All 192 v2 responses also passed the literal excerpt-grounding check. That
check establishes that a supplied excerpt occurs in the criteria, not that
the excerpt logically entails the reference. Empty evidence is permitted for
absent behavior under the frozen contract.

Each operation's 24 occurrences represent 12 templates repeated twice, not
24 independent requirements. The complete sample is synthetic and authored by
the same research workflow. No population-level accuracy, independent human
agreement, causal mechanism or statistical significance is claimed. Changes
to rubric instructions, formatting and evidence requirements are combined.

## Cost and verification

Usage-priced cost at the frozen rates was US$0.052009: US$0.012732 for OpenAI
and US$0.039277 for DeepSeek. This is the token ledger's reconciled amount,
not an independently verified invoice. Pending attempts and active reservations
are both zero for this study. The direct envelope with contingency was
US$0.466610; the conservative ledger envelope was US$0.832032 under US$1.

Offline rescoring exactly reproduced the preserved report. Response count,
call count and occurrence order match the frozen manifest. Local verification
passed 872 tests with seven skips and nine subtests; remote CI passed 879 tests
and nine subtests, with all three gates green for the executed source.
Raw responses, identities, hashes, latency and token ledgers remain private.

## What remains unresolved

The [earlier v1 comparison](judge-prompt-comparison-results.md) still has an
ambiguous call with US$0.000218 reserved. Read-only investigation found no
persisted provider request/response identifier or usage for that attempt.
The experiment key could not access OpenAI organization costs (HTTP 403),
and the available browser session required login. Exact cost or no-charge
reconciliation therefore remains dependent on external evidence. The old
ledger was not modified, the reservation was not released and no retry occurred.
See the [account-access note](2026-09-06-provider-account-checks.md).

The original 279 clean / 9 uncertain natural-artifact labels remain unvalidated.
A separately specified natural-artifact re-evaluation, retaining the original
labels and all methodological limits, is a possible next step. Passing these
controls does not automatically promote v2 into the primary pre-pilot or remove
the independent-outcome requirements for H1/H2.
