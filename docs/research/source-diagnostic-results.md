# Source-based diagnostic: the pilot remains paused

The first source-based diagnostic completed all 96 planned calls on 6 September
2026. The frozen gate failed. No prospective pilot trajectory was generated.
Usage-priced cost was US$0.030728, with no pending charge in this pilot ledger.
Together with screening, the pilot has 168 completed calls costing US$0.062545.
These amounts are computed from reported usage and frozen prices, not invoices.

## Design and decision

Each judge received 30 constructed cases from six source seeds and 18 preserved
natural artifact clusters. The controls contain six long omissions, eighteen
complete variants (long, concise and distributed), and six partial excerpts.
Expected control answers, source identities and historical judgments were not
sent to the outcome judges. The six seeds cover only two projects. Variants of
one seed are dependent observations.

Both judges had to detect at least five of six omissions, make at most one
false omission on the eighteen complete variants, abstain on at least five of
six partial excerpts, and return valid responses for all 48 requests. Those
criteria were fixed before collection and were not relaxed after failure.

| Measure | OpenAI | DeepSeek |
|---|---:|---:|
| Detected long omissions | 6/6 | 6/6 |
| Abstentions on partial excerpts | 0/6 | 0/6 |
| Valid responses on complete variants | 15/18 | 2/18 |
| False omissions among valid complete-variant responses | 0/15 | 0/2 |
| Invalid responses across all requests | 3/48 | 16/48 |

The invalid complete-variant responses are failures, not correct classifications.
Reporting only zero false omissions would conceal this severe missing-validity
problem. The gate therefore remains `pause`; prospective preflight is `no_go`.

## What failed

Both configurations classified every partial excerpt as omitted rather than
uncertain. The evidence-v2 instruction explicitly says that missing text is not
uncertainty, while these cases state that only part of the artifact is available.
This reveals a mismatch between the observation scope and the decision contract.
It does not show that the unavailable part contains, or lacks, the obligation.

Twelve otherwise parseable responses exceeded the 120-character evidence limit
(three OpenAI, nine DeepSeek). Seven DeepSeek responses were invalid JSON. All
nineteen failures occurred on complete controls. Raw outputs are preserved; no
overlong quote was clipped and no JSON was repaired for scoring. A short single
quote is also insufficient evidence of full entailment for a compound reference.

## Transfer to preserved artifacts

On the eighteen natural clusters, OpenAI returned seventeen omitted and one
covered; DeepSeek returned fifteen omitted and three covered. All 36 responses
were schema-valid. These are model judgments, not independently established
semantic outcomes. The sample was selected before these responses and is
balanced by project; it is not a prevalence sample of the full corpus.

The historical 279 clean / 9 uncertain labels must remain intact. This diagnostic
does not replace them with ground truth, estimate H1, or provide reliable terminal
labels for H2. It establishes that judge behavior depends materially on the
evaluation contract and the supplied evidence.

## Subsequent development study

The separate [scope-aware v3 development study](scoped-judge-results.md) has now
completed 48 calls. Its gate also failed, primarily because of evidence-quote
contract failures. Its 96 evaluation calls were not dispatched. The original
source diagnostic and all of its thresholds remain unchanged.

The v3 study separated complete-artifact coverage from partial-observation
uncertainty and requested evidence per reference obligation. Keep
the failed v2 collection as development evidence. Any revised prompt, schema,
output limit or observation-scope field needs a new frozen configuration, an
explicit cost envelope and cases not used to tune it. A development improvement
cannot retroactively pass this gate or automatically launch the main cohort.

The [pilot protocol](source-based-pilot-protocol.md) retains the original gate.
The [operator guide](pilot-operator-guide.md) describes archival execution and
the boundary against resets. Human calibration and confirmatory authorization
remain unresolved.
