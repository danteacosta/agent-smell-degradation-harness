# Intermediate omission pilot: 12 intents / 4 projects

User approved this design on 2026-09-21: 12 requirements from four projects,
three conditions, two generator configurations and three replications = 216
generation slots. Prior autonomous authorization includes consensus evaluation,
Drive/slides reporting and CI-gated integration. No new human approval is
inferred. This is exploratory H1 preparation, not the confirmatory H1/H2 study.

## Design and acceptance contract

- Select three distinct public, licensed source requirements per project before
  outcomes. Exclude the previously used SRS-163 and SRS-110. Record pinned source,
  license, hash and exact excerpt. Record prior exposure and exclusions.
- A reproduces the complete excerpt; B is an assistant-reviewed meaning-preserving
  rewrite; C removes exactly one contiguous explicit obligation from A. At least
  two non-target obligations remain. All references/obligation rubrics are frozen
  before any generation. No claim of expert semantic validation.
- Fixed generators: gpt-5.6-luna and gpt-5.6-sol; reasoning low. Three replications.
  Randomize all 216 slots with seed 20260921; opaque artifact IDs. Each call uses
  fresh context through the official Codex subscription adapter, no tools or API
  keys. No original reference or omitted target enters the generation prompt.
- Fixed judges: gpt-6-astra, gpt-5.6-sol, gpt-5.6-terra. Each sees only full source,
  obligation rubric and one generated artifact, never condition, generator,
  paired artifact, prior votes, or target-obligation marker. Shared-provider and
  generator/judge overlap are limitations. Freeze per-judge × generator results
  and an Astra/Terra-only agreement sensitivity (two votes, not 3/3 consensus).
  Serialize judge inputs by allowlist; target markers are excluded even if the
  condition can sometimes be inferred semantically. No debate/repair round.
- Three calibration calls on eight authored fixtures precede generation. The
  fixtures cover explicit support, omission, paraphrase, generic text, signed
  negative obligations and their opposite, contradiction, conditional/partial
  coverage and uncertainty-only mention (some fixtures exercise multiple cases). All expected
  obligation labels and literal quotes must pass; otherwise stop without tuning.
- Primary labels require 3/3 agreement on supported/absent/unclear; unresolved
  disagreement and incomplete votes stay unresolved. 2/3 majority is sensitivity.
  Only criteria, not uncertainty questions, establish obligation coverage.
  Labels compare the signed source obligation: preserving a prohibition can be
  supported; imposing its opposite is absent, and contradictory statements are
  unclear. Partial compound-clause coverage is unclear. Preserve explicit
  operative conditions and polarity. Optional implementation preferences and
  illustrative examples need not be repeated for supported coverage. Promoting
  a preference/example into a mandatory implementation/value is an unsupported
  addition, scored separately from operative coverage. Genuine contradictory
  behavior is unclear; only the opposite policy is absent. Targets are source clauses/categories,
  not necessarily single atomic propositions. References to external response
  schemas remain in all applicable variants but are not fetched for scoring.
- Maximum observable CLI invocations 867 = 3 calibration + 216 generation + 648 judge. Bounded four
  concurrent calls; fresh isolated contexts. Exactly one attempt per call slot,
  no orchestrator retry, output repair, replacement, or API fallback. The CLI may
  perform internal transport retries; this is not a bound on remote requests. Invalid output
  remains invalid; provider error stops further dispatch, drains in-flight calls.
  Call result files are immutable; interrupted/ambiguous calls never rerun. A
  started packet is not resumable. Capture stdout/stderr up to the adapter
  limit of 2 MB per stream, with truncation metadata and hashes.
- Privacy: send only verified public source excerpts and authored text. Private
  Drive data, unrelated repository contents and credentials never enter prompts.
  Freeze code/CLI identity and private receipt before calls; fail on drift.

## Estimands and analysis

Primary endpoint: target obligation supported in generated criteria, source-
relative. Report all 216 planned slots, valid/invalid/not-attempted calls and
unresolved labels. Rates use planned denominators and explicit missingness bounds
(unclear, disagreements and missing may be supported or absent). Show every
intent/model/condition, equal-weight project summaries, C−A and B−A. Negative
C−A means lost coverage; B−A diagnoses sensitivity to the rewrite. Show remaining
obligation coverage separately to reveal non-target changes, and count recovery
of omitted targets, null/reversed effects and disagreement. Replications and
obligations are not independent sample units.

Primary contrasts are computed separately for each generator: mean C minus
mean A, and mean B minus mean A, within intent, then equal-weight across the
12 intents (three/project). Fresh replications have no natural pairing. Pooled
across-generator equal-weight contrasts are secondary. Complete-cell sensitivity
requires all three replications of both compared arms to have resolved binary
coverage; report eligible intent/config counts. Do not select resolved replication
pairs after outcomes or silently convert missing/unclear to absence.

For uncertainty, report every project effect and four leave-one-project-out
contrasts. A seeded project bootstrap (10,000 draws of four projects, retaining
all intents/models/repeats) gives a conditional resampling spread for these four
purposively selected projects, with no nominal population coverage or p-values.
Unknown effects retain bounds; bootstrap endpoints must not erase missingness. Provide worst/best-case paired effect bounds across
all planned observations. Do not pick models, families or exclusions after results.
The generation instruction explicitly asks not to invent obligations. Thus an
omitted-condition output can correctly obey its supplied prompt yet lose coverage
relative to the full source. This experiment measures propagation/recovery of
missing source obligations under that task instruction; it is not proof of model
misbehavior, naturally occurring smell prevalence or a universal defect effect.
No H2 detector training or temporal claim is part of this collection.

## Implementation plan and ownership

- [ ] Source agent: data/criteria-expansion/ public corpus and source-review report.
- [ ] Main: review selection and transformations, freeze protocol and verify
  public-only outbound content; preserve all prior packets.
- [ ] Runner agent: scripts/criteria_expansion.py and tests/test_criteria_expansion.py;
  reuse CodexCLIProvider and criteria_consensus strict JSON/custody utilities.
  Runner owns validation, schedule, calibration, isolated dispatch and analysis.
  No modification of historical scripts or provider adapter needed.
- [ ] Test-first observable contracts: reject invalid corpus/deletion/duplicates;
  216 balanced slots; no target/reference leakage; strict literal citations;
  calibration failure causes zero generations; exact budget, stop/invalid output,
  rerun rejection; correct unresolved bounds and clustered paired calculations.
- [ ] Independent reviewer: protocol/scientific/code review before live freeze.
- [ ] Run focused regressions and baseline adapter tests; compile/static checks.
- [ ] Freeze packet, perform authorized live collection, verify hashes and derive
  report independently. Update Drive and slides with complete results/limits.
- [ ] Full portable tests, Linux CI, review and merge only at verified passing head.

## Verification

Use /private/tmp/masters-next-venv/bin/python -m pytest -q
 tests/test_criteria_expansion.py tests/test_criteria_consensus.py tests/test_codex_cli.py.
Build packages in a staging directory, never during custody tests. Review SOLID,
clean code and provider/privacy boundaries. Retain fresh raw evidence for every
claim. A runtime/provider failure is an outcome to report, not permission to
substitute an easier model or requirement.

## Pre-collection verification record

All 12 final A/B/C transformations and source/license hashes were independently
reviewed by a second assistant before collection. No P1/P2 findings remain after
clarifying optional implementation preferences and negative/compound obligations.
Main freshly ran 49 focused tests successfully. The three planned calibration
batches test category labels and literal citations, not comprehensive correctness
of auxiliary additions. Full portable software regression is running separately;
no generator/judge call has occurred at this checkpoint. Source metadata remains
assistant-reviewed, with zero human approvals.
