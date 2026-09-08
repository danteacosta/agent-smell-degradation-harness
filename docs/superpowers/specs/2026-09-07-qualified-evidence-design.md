# Preserve source blocks and test obligation completeness

The user approved this bounded follow-on design: preserve source blocks, compare
v4 with a more explicit completeness instruction, retain the existing pass
criteria, run 48 development calls and dispatch 96 evaluation calls only after
a pass. Both approved spending caps remain unchanged. This written specification
is the review checkpoint before implementation and collection.

## Observed problem and limits of the diagnosis

The preceding comparison completed 48 calls. V4 produced 24 valid responses and
23 exact construction matches. Its single mismatch was `uncertain` on a required
long omission. That failed decision remains authoritative for that version.

A read-only inspection found that `scoped_judge.build_cases` inserts a clause
at the midpoint of the context's line inventory. In both development sources,
this point falls inside a structured block: one table header/separator pair
and one wrapped list instruction. The insertion interrupts their continuity.
Existing tests use repeated independent one-line context and do not exercise
these boundaries.

The failed case also includes visible context about a related capability. The
cited segment contains that context and neighboring obligations. Literal target
deletion therefore does not, by itself, verify that all meaning-equivalent
support is absent. This is a concrete construction weakness and a plausible
contributor to abstention, not a demonstrated causal account of the model's
decision. No hidden reasoning or independently validated human oracle exists.

## Options considered

1. Preserve blocks and compare the unchanged v4 prompt with an explicit
   completeness instruction on the same revised cases. This tests the prompt
   change without selectively removing the failed case. Recommended and approved.
2. Preserve blocks and use only v4. This is smaller, but a remaining failure
   would not test whether unspecified required qualifiers explain the decision.
3. Add another evaluator pass or an explanation/reason schema. This adds calls,
   response variation and dependencies; it is outside this bounded correction.

The old gate will not be relaxed, the old response will not be rescored, and the
nearby capability will not be removed from the source context to simplify a case.

## Acceptance contract

Given a source context containing wrapped prose, lists, tables or code, when
the distributed and long-omission variants are built, then the entire context
remains one contiguous, byte-identical block. Place the first obligation before
that block and remaining obligations after it. Preserve existing complete and
partial variants, reference, target index, source joins and construction answers.
Use a new layout version and new case identities with explicit lineage.

Given complete observation and an obligation with a required actor, interface,
trigger or restriction, when only a related capability is specified, then the
candidate instruction requires checking every part before calling it covered.
Missing support for a required part is omission; genuinely ambiguous visible
wording can remain uncertain. Partial observation retains its existing absent
support rule. This is a rubric clarification, not a new smell taxonomy.

Given a syntactically valid response with immutable artifact-segment IDs, when
it is parsed, then the existing v4 location checks apply unchanged. The new
prompt has a distinct version. Parsing does not infer support, repair statuses,
or expose reference text as artifact evidence.

Given the failed predecessor with all 48 calls reconciled, when the new plan is
prepared, then only its unused direct reserve and contingency may be transferred
through a separate exclusive closure. Retain all ancestor spending, the earlier
unresolved amount, parent reservations and parent contingency. Reject concurrent
successors, changed custody, missing usage, runtime drift or exceeded caps before
dispatch. No private file or previous claim is overwritten.

Given a frozen v4/v5 plan with a verified budget, when development finishes,
then candidate v5 must meet the existing rule for both providers: all outputs
valid, at least 5/6 exact construction vectors overall, and every long-omission,
partial-missing, partial-complete and partial-contradiction vector exact.
Only a pass permits evaluation. Apply the same candidate rule to evaluation.
Baseline v4 results remain comparison outcomes, not a post-hoc alternate winner.

## Components and boundaries

- A new source-block case builder composes the revised artifacts from the
  preserved seeds. It validates provenance through the existing seed contract
  without editing the historical builder. It has no provider access.
- A new candidate prompt module reuses the v4 input, snapshot and parser
  boundaries. It changes only the instruction and version identity.
- A bounded successor plan freezes both prompt arms, identical revised inputs,
  provider/price configuration, output allowance, runtime and phase decisions.
- A custody adapter checks the failed predecessor using its preserved runtime,
  then binds the verified report to immutable private files. It invokes only the
  read-only report command with explicit argv, fixed interpreter/worktree paths,
  bounded output and timeout; it never loads credentials for that command.
- A sequential coordinator reuses the provider adapters and durable cost journal.
  It reserves before dispatch, disables SDK retries, rechecks predecessor bytes
  under locks, skips reconciled calls and stops on ambiguous accounting.
- A redacted audit keeps planned, valid, invalid, missing and exact counts by
  provider, arm, phase and operation. Citation integrity remains separate from
  semantic validity. Raw cases, provider identities and ledger hashes stay private.

The custody adapter isolates the frozen predecessor runtime from the new source
identity; importing it as if both studies used one runtime would invalidate the
old source fingerprint. Existing frozen production modules remain unchanged.
Use the established parent-to-descendant lock order. Perform any subprocess
report validation outside those locks, then recheck its bound file snapshot
inside the critical section to detect a stale result without deadlocking.

## Fixed collection and budget

Use the existing two development locators and four locked evaluation locators.
Do not inspect evaluation responses or change the case selection after freezing.
The construction/layout rule applies uniformly to all locators. Prior background
exposure remains a limitation; these are not certified contamination-free data.

There are six operations per locator, two providers and two arms: 48 development
calls plus 96 conditional evaluation calls. Keep 512 output tokens and the
existing conservative input-bound calculation. The candidate prompt is concise;
compute actual serialized prompt bounds instead of changing output limits to
force the plan into budget. If the exact envelope does not fit, do not collect
or silently change the design.

The shared cap is US$7 and cumulative auxiliary cap US$1. The predecessor's
US$0.028024 and earlier auxiliary's US$0.023175 remain spent. The earlier
US$0.000218 remains unresolved. A planning-only calculation leaves US$0.650749
for the new conservative envelope after audited closure; this is a protocol
allowance, not an API credit balance or authorization for unrelated spending.

No additional repetitions, repaired outputs, provider selection or prompt tuning
are allowed after this freeze. Preserve a failure if it occurs. Even a successful
auxiliary evaluation does not automatically release main-cohort generation;
record the result and the remaining main-launch decision explicitly.

## Verification and delivery

Behavioral tests must cover context continuity, exact target transformation,
unchanged controls, prompt/oracle isolation, old/new parser separation, both
phase outcomes, accounting ambiguity, custody tampering, resume, budget limits,
exclusive succession and redaction. Use provider doubles only at the network
boundary. Verify the CLI without credentials or provider access.

Run the complete suite, eval, replay and wedge gates, compile and packaging
checks. Review authorization, private paths, subprocess execution, logging,
cost accounting, SOLID and clean-code boundaries before freezing the runtime.
Work sequentially, without subagents or dependency changes. Update the results
and operational documentation with actual denominators and costs; software tests
are not evidence of human validity, H1/H2 or early-warning benefit.
