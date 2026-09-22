# Cross-project omission pilot: 12 source intents

Status: finalized with complete generation and incomplete judgment collection.
Four provider timeouts triggered the frozen stop rule; no calls were retried.
The primary omission contrast remains negative under worst/best-case missingness
bounds in both generator configurations, conditional on panel label validity.

## Design

The user-authorized intermediate pilot expands from one source to 12 distinct
intent units in four public projects, three per project. Each source has a
literal complete version A, an assistant-reviewed rewrite B, and a version C
that deletes one contiguous obligation clause. These clauses can contain
multiple operative components; they are not necessarily atomic propositions.

Generation requested `gpt-5.6-luna` and `gpt-5.6-sol`, with three fresh-context
replications per intent/model/condition, giving 216 planned generations. The
fixed seed shuffles generation and judgment schedules before any model outcome.
Three judges (`gpt-6-astra`, `gpt-5.6-sol`, `gpt-5.6-terra`) evaluate one artifact
at a time against the full source and neutral obligation IDs. Condition,
generator identity, target marker, paired artifacts and previous votes are not
sent. Semantic inference of the condition remains possible.

All three judges passed eight authored calibration fixtures, including signed
negative obligations, partial compound coverage, contradictions and optional
preferences. Calibration verifies coverage labels and literal evidence contracts;
it does not establish correctness of every auxiliary addition annotation.

The primary endpoint is unanimous target-obligation coverage, separately for
each generator. Unclear/disagreeing/incomplete labels remain unknown and enter
explicit worst/best-case bounds. Comparisons subtract arm means within each
intent/configuration; replication numbers do not create natural pairs. Complete-
cell sensitivity requires all three binary outcomes in both compared arms.
Project effects, leave-one-project-out bounds and conditional project resampling
spread remain descriptive. Four purposively selected projects cannot support
population interval guarantees. Majority and agreement without Sol are separate
sensitivity analyses; Sol also generates artifacts.

## Operational collection

All 216 generation slots were attempted once: 212 valid JSON contracts and four
invalid outputs. All four invalid generations used Luna: three A and one C.
Sol produced 108 structurally valid outputs; Luna produced 104. No malformed
response was repaired or replaced. This is format compliance, not semantic
quality. The four invalid artifacts retain their 12 unattempted judgment slots;
636 judgments are eligible from the originally planned 648.

Calls use the official Codex CLI with saved ChatGPT subscription authentication,
low reasoning, tools disabled and fresh ephemeral contexts. There is no API-key
fallback. The 867 bound concerns observable CLI invocations, not undocumented
internal transport retries. Captures have a 2 MB per-stream limit with truncation
metadata. Requested model aliases are recorded; immutable response model snapshots
and API-equivalent USD cost are not exposed.

## Finalized results

The 784 observable calls comprise three calibration batches, 216 generations and
565 judgments. Judgments: 539 valid, 22 invalid and four provider timeouts. Of
648 planned judgment slots, 83 were unattempted: 12 belong to invalid generated
artifacts and 71 remained after the stop. The timeout captures record termination
without a completed response; they do not establish whether quota, service or
interruption caused the delay. The original packet is closed, without repair,
retry or resume.

| Condition | Target supported | Target absent | Target unresolved | Planned |
| --- | ---: | ---: | ---: | ---: |
| A: complete | 40 | 0 | 32 | 72 |
| B: rewrite | 45 | 0 | 27 | 72 |
| C: omission | 0 | 47 | 25 | 72 |

Thus no target recovery was confirmed in C, but 25/72 remain unknown. Across all
216 targets, 84 are unresolved (83 missing at least one usable vote, one panel
disagreement). Unknown does not mean absent.

| Primary contrast, percentage points | Luna | Sol |
| --- | --- | --- |
| C − A | [−100, −16.67] | [−100, −25.00] |
| B − A | [−38.89, +50.00] | [−36.11, +38.89] |

These are identification bounds from unresolved outcomes, not confidence
intervals. They assume resolved panel labels are correct. Equal weights apply
to 12 intent-level arm means within each generator. The secondary pooled C−A
bounds are [−100, −20.83] pp. B−A includes zero and does not establish equivalence.
Only one of 24 intent×generator cells has all six compared outcomes resolved:
StrictDoc SRS97×Luna, C−A = −100 pp and B−A = 0. Its complete-cell result cannot
represent the full sample. Ten C−A cells have strictly negative bounds; the other
14 include zero and must not be called null effects. Conditional bootstrap
spread is unavailable under the frozen completeness rule.

### Project-level C−A bounds (percentage points)

| Project | Luna | Sol |
| --- | --- | --- |
| CASS | [-100.00, -11.11] | [-100.00, -44.44] |
| realworld | [-100.00, 0.00] | [-100.00, -33.33] |
| strictdoc | [-100.00, -55.56] | [-100.00, -11.11] |
| todomvc | [-100.00, 0.00] | [-100.00, -11.11] |

Leave-one-project-out C−A bounds remain strictly negative in both configurations,
including removal of StrictDoc; this is internal robustness within four purposive
projects, not population generalization. Non-target obligations also retain
missingness: A 146 supported/0 absent/3 unclear/145 unresolved of 294; B
173/1/6/114; C 161/1/7/125. Unanimous unclear is unknown for binary coverage.

The prespecified Astra/Terra-only sensitivity gives C−A bounds [−100, −33.33] pp
for Luna and [−100, −50] pp for Sol. Majority changes only the B×Sol target
contrast to [−33.33, +38.89] pp. These do not replace the primary endpoint.
A supplementary generator-specific overlap diagnostic was added in commit
0244671 after freeze: Luna retains the primary panel and Sol uses Astra/Terra.
It is not part of the immutable primary packet or a new collection. Its C−A
bounds follow directly: Luna [−100, −16.67], Sol [−100, −50] pp.

An independent recomputation verified 4,945 receipt-listed files, 1,098 obligation
cells and 2,547 literal evidence quotes. There were no truncated captures.
780 completed usage events report 11,815,852 input tokens (7,664,256 cached),
258,909 output tokens and 70,759 reasoning-output tokens as separate reported
fields; these should not be added without a provider accounting definition.
Four timeout calls have no completed usage event. Subscription usage is not an
API-equivalent dollar cost.

Final receipt SHA-256:
`5c72ebe1ab3cce7a09b804514680e3dc82c96b2a5cdb481a57b0cc928e8a7561`.
The frozen collector was commit ab822f0; later analysis additions do not alter it.

## Scope and limitations

The task explicitly requests criteria without invented obligations. A C response
can obey its shortened prompt and still lose coverage against the complete source.
This measures propagation and recovery of missing obligations under this task
instruction, not agent disobedience, executable defects or natural smell prevalence.
B is an authored rewrite, not an independent natural requirement. The source
selection is purposive and English-only. Projects and full source documents had
prior exposure; a bounded audit excluded known selected-intent reuse but does not
establish pristine held-out status or exclude model pretraining. CaSS requirements
are retrospective documentation derived from code, initially auto-generated and
later reviewed upstream; this is not human validation of our study.

Labels remain `llm_panel`, with `human_approvals=0` and
`confirmatory_eligible=false`. Repetitions, obligations and judge votes are not
independent source cases. This pilot does not confirm H1/H2 and does not train or
evaluate an H2 detector. Historical null results and immutable packets are retained.

## Reproducibility

- [Frozen design and acceptance contract](../plans/2026-09-21-criteria-expansion.md)
- [Source selection, provenance and transformations](criteria-expansion-source-review.md)
- [Finalized analysis and obligation-level votes](../../data/criteria-expansion/results-20260921.json)
- [Public corpus](../../data/criteria-expansion/corpus.json)
- [Integration PR 66](https://github.com/danteacosta/agent-smell-degradation-harness/pull/66)

Frozen-input receipt SHA-256:
`4be7a581f939c4d10938438270ec2f3106bfde2f6d5c773b03c5552229786df3`.
Precollection implementation commit: `ab822f0`.

Software verification: 49 focused tests; 1,642 portable tests and nine subtests;
12 skips and four macOS-incompatible resource checks reserved for Linux CI.
Linux CI passed 1,655 tests, three skips, nine subtests, eight separate container
boundary tests and the behavioral smoke. Wheel/sdist builds passed in isolated
staging. Independent assistant source, scientific and implementation review found
no remaining P1/P2 issue before collection; this is not expert human approval.

Delivery update: the proposal, experiment report and both native slide decks include the finalized missingness and contrasts. PowerPoint and PDF exports are retained in the private delivery packet. The post-freeze overlap diagnostic passed 50 focused tests in this final delivery session.
