# Proposed factorial successor: shared omission and mutant-code context

Status: unexecuted factorial-successor proposal in PR #183. The completed
three-arm study in PR #184 used PR #181 at frozen commit
`eec5110c4353dc5da3c6dc29f36be23bd2b090e9`; its collection had already started
before PR #183 was opened. This proposal did not govern that collection and
must not replace its protocol or analysis retrospectively. No four-arm packet
has been frozen or executed. Human approval must consider the now-known
results of both PR #180 and PR #184 before a fresh successor is registered.
The proposed successor remains exploratory and cannot confirm H1 or test H2.

## Scientific contract

The study reuses the same 25 eligible requirements from eight projects and the
same 191 pages as the mutation-adequacy study. It generates no new
implementation. For each requirement, it selects one oracle-confirmed mutant
from the 81 available mutants by applying
`Random("2026100508:<case>")` to sorted slot IDs. Selection does not inspect
which suites killed the mutant in PR #180. The prior correct reference is
preserved. The selected slot is metadata and never appears as a label in a
prompt.

The experiment is a 2×2 design. It crosses requirement completeness with code
context while keeping the selected defective implementation fixed in both code
arms:

| Source | Requirement | Implementation context |
| --- | --- | --- |
| `spec_complete` | complete | scaffold without feature code |
| `spec_incomplete` | incomplete | scaffold without feature code |
| `code_complete` | complete | selected confirmed mutant |
| `code_incomplete` | incomplete | the same selected confirmed mutant |

The proposed fresh collection would generate two suites per source and requirement: 25 × 4 × 2 = **200 new
calls** to `gpt-6-astra`, contemporaneously, without retry or repair. The call
order is shuffled with seed 2026100508. Earlier calls and failures are neither
reused nor replaced. The complete/incomplete code comparison therefore changes
only the requirement text; it no longer conflates omission with the presence of
code.

## Outcomes and decisions

The estimand is preserved: average the two suites within each requirement, then
weight requirements equally. A suite can kill a mutant only if it is usable and
quiet on the frozen correct reference. Generation and runner failures stay in
the denominator with score zero.

**Primary comparison.** `code_complete - code_incomplete`. This holds the
selected defective implementation constant and asks whether omitting the rule
from the requirement makes generated tests less able to expose that known
loss. Local support requires both a 4,000-draw project bootstrap interval with
lower bound above zero and a two-sided exact project sign-flip p-value below
0.05.

**Proposed secondary comparisons.**

- `spec_complete - spec_incomplete`: contemporaneous replication of MA1
  without implementation code;
- `spec_complete - code_complete`: whether showing defective code reduces
  mutation detection even when the complete rule is visible;
- `spec_incomplete - code_incomplete`: the corresponding contrast under the
  incomplete requirement.

The difference-in-differences between the completeness effects with code and
with scaffold is reported as exploratory, with no decision gate. No secondary
comparison can replace a failed primary result.

For the selected mutant, report quiet outcomes both unconditionally and among
suites eligible after the correct-reference check. This is operational false
security against a confirmed loss, not a population rate or a psychological
claim about confidence. Also report denominators, assertion/error alarms,
generation failures, and conditional and unconditional alarms on other correct
and recovered pages. Repetitions and page executions are not independent
units.

## Custody and acceptance

- Every page remains bound to its prior public hash and private receipt.
- Prompts, page roles, selected mutants, scripts, runner and image are frozen
  before the first call.
- Script, page or prompt drift blocks generation or execution.
- A started packet cannot be resumed, retried or repaired.
- A generation failure remains a zero in its planned position.
- Both code arms receive the exact same selected confirmed mutant; neither
  receives the correct reference as implementation context.
- Regression tests must prove the 2×2 boundary and the primary comparison.

The three authored browser controls must qualify the runtime before any model
call. Final verification must reconcile 200 attempts, 1,528 planned
suite/page pairs, real reports versus placeholders, and the complete receipt.
Only structured results and a path-free public manifest may be published;
prompts, pages and raw responses remain private.

## Limits and future work

The cases were selected from known losses; there are only eight projects, one
tester from the same provider, two suites per source and a simplified scaffold.
The four-arm experiment isolates two prompt factors within this selected set,
but it does not estimate defect prevalence or confirm the thesis. PR #180
remains a separate completed study.

A future tool-using-agent study would require licensed public policies,
independently frozen obligations, isolated actions/state and complete versus
incomplete evals. No result from this browser study may be presented as evidence
for that domain.
