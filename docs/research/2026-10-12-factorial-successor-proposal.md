# Proposed factorial successor to the completed shared-omission study

The completed three-arm study cannot isolate requirement omission from code
context when its comparison changes both at once. A separate 2×2 successor
could isolate those factors. This is an unexecuted proposal retained from
[PR #183](https://github.com/danteacosta/agent-smell-degradation-harness/pull/183),
not an amendment to the completed study or authorization to collect new data.

The original collection used PR #181 at frozen commit
`eec5110c4353dc5da3c6dc29f36be23bd2b090e9` and had already started before
PR #183 was opened. [PR #184](https://github.com/danteacosta/agent-smell-degradation-harness/pull/184)
publishes the completed three-arm study. Its collector, registered protocol,
receipts, results and analysis remain unchanged. The historical
[three-arm protocol](../preregistration/2026-10-05-shared-omission-e2e.md)
continues to describe that study. No four-arm packet has been frozen or run.

## Proposed comparison

The candidate successor uses the same 25 eligible requirements from eight
projects and 191 pages. For each requirement, select one previously confirmed
mutant from the 81 available mutants with
`Random("2026100508:<case>")` over sorted slot IDs, without selecting by the
performance of earlier generated suites. The prior correct reference remains
separate from the code shown to the test generator.

| Source | Requirement text | Implementation context |
| --- | --- | --- |
| `spec_complete` | Complete | Scaffold without feature code |
| `spec_incomplete` | Incomplete | The same scaffold |
| `code_complete` | Complete | Selected confirmed mutant |
| `code_incomplete` | Incomplete | The same selected mutant |

The proposed primary contrast is `code_complete - code_incomplete`, holding
faulty code constant. The scaffold completeness contrast is a separate
replication. Differences between scaffold and mutant-code contexts, and the
interaction between context and completeness, remain separate exploratory
readouts. They cannot replace a failed primary comparison.

Generate both repetitions of all four sources in a fresh batch: 25 requirements
× 4 sources × 2 suites = **200 fresh model calls**, with **1,528 planned
suite/page pairs** (191 pages × 4 sources × 2 suites). This is not a 50-call
top-up to the completed 150-call, 1,146-pair study. Earlier calls, failures and
results are neither reused as new observations nor replaced. The proposal is
informed by the now-known results of both preceding studies.

## Candidate analysis and evidence boundaries

Average the two suites within each requirement, then weight requirements
equally. A suite can kill a mutant only when usable and quiet on the frozen
correct reference. Generation and runner failures retain their planned
positions with zero scores. The proposed local-support gate combines a
4,000-draw project bootstrap interval with lower bound above zero and a
bilateral exact project sign-flip p-value below 0.05. It has not been approved
or preregistered for a new collection.

Report quiet outcomes on the selected mutant both unconditionally and among
eligible suites, alongside failures and alarms on correct or recovered pages.
Repeated suites and page executions are not independent units. Selection from
known losses, eight projects, one provider, two suites per source and simplified
scaffolds limit generalization. This does not estimate defect prevalence,
psychological confidence or confirm H1/H2.

The earlier audit's claim that the original three-arm adapter inevitably
attempted to overwrite its output was unsupported and withdrawn. That adapter
delegates once to `ma.execute`. Four-arm finalization developed in PR #183 is
not evidence that the completed collector was broken.

## Decisions before any execution

Adopting this note preserves a design option only. Fresh collection requires
separate approval of scope and the 200-call budget, a distinct preregistration
that acknowledges the known prior results, independent custody, a new source
and prompt freeze, and runtime qualification with the authored controls.
Neither the existing collector nor the completed study's protocol should be
replaced to implement the successor. Any future implementation needs its own
identity and tests proving identical mutant code in both code arms, preserved
scheduled denominators, and rejection of drift, retries or repair.

This documentation change makes no provider calls, changes no scientific data,
and authorizes no model execution. Raw pages, prompts and responses remain
private. Only separately reviewed structured outputs may be published.
