# Source-based exploratory pilot

Preparation date: 6 September 2026. Target execution window: 7–13 September.
Status: expanded exploratory scope and a **US$7 total cap** authorized by the
user on 6 September; screening/admission and the diagnostic gate still control
prospective dispatch. Five repetitions are selected. This records the user's
attestation, not an advisor signature, ethics exemption or confirmatory approval.

This pilot asks whether the corrected evaluator transfers from short constructed
examples to source-derived requirements and preserved natural artifacts. It does
not confirm H1/H2 or equate LLM agreement with human validity. Do not repeat toy
controls until a perfect score is obtained.

## Corpus and independence

The private package contains 24 candidates: the 12 previously selected exploratory
intents and 12 additional, distinct source locators. Distribution: CASS 7,
StrictDoc 7, RISC-V BRS 3, RISC-V Nexus Trace 2, SHARCS LevelCrossing 2 and
SHARCS Tokeneer 3. They are candidates, not 24 newly admitted intents.

New candidates retain the pinned source, license/provenance, exact source text,
single deletion and offset, clean/defective hashes, reference and explicit
obligation inventory. No paraphrase is counted as an additional intent. The
two Nexus records previously shared a section-level locator; the pilot records
now also identify their separate lines in the pinned source.

All 276 candidate pairs were screened for textual similarity. One existing BRS
pair exceeds the predeclared 0.65 screen. The requirements name different SBI
extensions and different triggering hardware conditions, but share a template.
Keep that relationship visible for independent review and clustered analysis;
do not interpret a lexical threshold as proof of semantic independence.

Six project IDs are not necessarily six independent source families: the two
SHARCS case studies share a collection and the RISC-V specifications are related.
Report source-family and project membership. Fourteen candidates come from two
projects, a substantial coverage limitation. CASS's source document discloses
AI-assisted initial authorship and subsequent maintainer review; it must not be
described as exclusively human-authored natural data.

Admission requires source-license/notice verification, an independence decision,
and source-faithfulness/manipulation screening. Preparation never manufactures
those decisions. The old 12-intent manifest remains unchanged. Pilot candidates
and references use separate `pilot-candidates/v1` and
`pilot-reference-constraints/v1` preparation schemas, not the pre-pilot's fixed
12-record contracts. Final admission/freeze is a separate gate.

## Blocks and counting units

1. **Admission and oracle screening:** 24 paired candidate packets and six
   source-control packets, independently reviewed by both LLM providers: 60
   calls. These are review-plane checks, not human reviews or outcome labels.
   Packets omit historical labels and intended clean/defective names. The
   operator must resolve source/rights/independence questions from evidence;
   agreement alone cannot grant rights or certify independence.
2. **Natural transfer:** 18 unique text–reference–generator clusters from the
   preserved corrected pre-pilot, three per project, drawn from 94 clusters.
   Re-evaluate once with v2 on each provider: 36 calls. Retain every historical
   response and occurrence ID in a separate sidecar. No regeneration occurs.
3. **Source-based controls:** six source seeds, five variants each, once per
   provider: 60 calls. These six seeds come from CASS and StrictDoc, not all six
   projects. This block tests a narrower source subset than the natural sample.
4. **Prospective generation:** after admission and the initial decision gate,
   24 intents × two variants × R repetitions = 48R base episodes. Each has two
   generator trajectories. Each trajectory has T1, T2, a local pre-final T3
   lineage check, and terminal artifact generation. There are three paid
   generation calls, not a paid T3 masquerading as the terminal stage.
   Each terminal artifact is judged by both providers with v2. Select
   `ceil(0.20 × trajectories)` duplicate artifacts outcome-blind before labels;
   both providers judge each duplicate. Freeze selection seed and private joins.

Natural sampling round-robins fixed strata within each project: text length
<100 / 100–299 / ≥300 characters and reference obligation count 1 / 2–3 / ≥4.
Hash-ranked ties are deterministic. Select before any new v2 responses.
Identical texts are clustered; therefore this sample estimates neither
episode-weighted prevalence nor population-wide accuracy. Repetitions and
variants are not independent source intents.

## Behavioral controls

Each seed has a complete expanded-context version, a version deleting one target
clause, a concise complete version, a complete version with clauses distributed
through the context, and a genuinely partial-artifact excerpt. Expanded versions
are roughly 1,300–1,700 characters; the omission changes length by under 10%.
This tests longer context than the original short recuts, not full-document or
extreme long-context performance. Context is taken from the pinned sources,
not repeated generic filler. References contain multiple obligations.

Expected statuses are covered / omitted / covered / covered / uncertain.
The partial excerpt is an auxiliary visibility diagnostic; it is never a primary
missing-condition treatment. Source-faithfulness and ambiguity oracles are
operator-constructed and remain pending independent screening. A hidden target
restatement or a disputed expected response blocks that seed before collection.
Do not call these labels human ground truth.

Only the blinded request is rendered into the fixed evidence-v2 prompt. Source
IDs, intended operations, expected responses, old labels and review packets stay
outside the outcome-judge payload and the pre-final feature plane. The current
v2 gives one coverage verdict and a short excerpt for a composite reference;
an excerpt match checks quotation grounding, not entailment of every clause.

## Initial continue / adjust / stop rule

Freeze the package, review decisions, prompt/schema/configuration, token bounds,
prices, ordering and these rules before collection. These are practical
exploratory thresholds chosen for this pilot, not literature-derived validity
cutoffs or statistical power guarantees.

- **Continue:** accounting and schema are complete; both judges identify at least
  5/6 omission cases; each has at most 1/18 false omission verdicts on the three
  complete variants per seed. Continue only if the corpus and budget gates pass.
- **Adjust:** one judge misses these criteria, or the partial-excerpt diagnostic
  yields fewer than 5/6 abstentions on either judge. This additional operational
  threshold is fixed before these responses are collected. Preserve all outcomes, pause prospective
  generation and document a restricted interpretation or a versioned redesign.
  Do not optimize on these six seeds and then call them a fresh test set.
- **Stop:** any ambiguous charge, unverified usage, budget reservation failure,
  unexpected model identity, incomplete checkpoint, leakage, or unresolved
  source/manipulation issue. Never silently drop a failed or uncertain episode.

Abstentions and malformed/missing judgments remain separate denominators; they
do not count as correct omission detections or correct complete-case judgments.
Report partial-excerpt abstention as a diagnostic, not as a pooled accuracy gain.
No rule above authorizes a confirmatory conclusion.

## Analysis fixed before collection

For controls, report planned/completed/invalid/abstained counts and the full
coverage confusion table separately by provider and operation. Report omission
sensitivity, false alarms, concise-versus-expanded and collected-versus-distributed
decision changes by source seed. Six seeds are the independent construction
units; thirty variants are not thirty independent requirements.

For natural artifacts, show paired old-to-v2 transition tables, grounded-excerpt
failures, self-versus-cross relations, project/length/obligation strata and all
uncertainties. Multiple old responses in a text cluster remain visible; no
majority vote creates a gold label. Report descriptive counts without claiming
an accuracy or correctness improvement on unlabeled natural data.

For prospective trajectories, preserve ordinal machine labels separately from
coverage status. Comparisons by clean/defective input and provider are
exploratory associations. Do not retrofit the old 279 clean / 9 uncertain
distribution or select the better judge after observing these outcomes.

Follow the [temporal protocol](temporal-warning-protocol.md) for T1, T1+T2 and
T1–T3 plus same-content/no-lineage ablation. Freeze alerts before attaching any
terminal label. Record stage availability, first alert, lead time to T4,
missing checkpoints, observation cost and instrumentation latency. Natural
terminal correctness remains unknown: set it to null for validity-sensitive
false-alert/detection rates. Machine-labeled diagnostic rates, if reported,
must be separate and explicitly machine-referenced. Executable contracts verify
only their formal specifications, not the natural-language mapping.

The initial pilot alert policy is deliberately limited: T1 flags explicit
uncertainty; T2 checks lexical coverage of the already interpreted constraints;
T3 rechecks the same plan with local lineage diagnostics. It never sees the
reference or terminal judgment. T3 does not add an independent observation of
implementation behavior. Consequently these alerts can describe availability,
lead time and cost, but cannot by themselves establish a provenance advantage.
The same-content/no-lineage comparison remains required before making that
stronger claim; this runner does not implement a learned B0/B3 comparison.

## Budget and launch boundary

All blocks share one US$7 pilot budget. Screening is included; splitting the
plan into commands does not create new allowances. The current envelope is
US$6.482882, including 25% contingency, no cache discount and one attempt per
call. It is a reservation, not measured spend or evidence of account funding.
Output limits are 384/256/256 tokens for T1/T2/artifact, 96 for judging and 192
for screening. Known prompt inputs use UTF-8 bytes plus 64 framing tokens;
dynamic interpretation/plan contexts are bounded at 1,500/1,024 UTF-8 bytes.
The artifact's escaped JSON value in the judge prompt is bounded at 768 bytes.
This is a conservative planning proxy, not a vendor-certified tokenizer bound.
Oversized contexts or incomplete responses stop the run; they are not truncated.
Pilot templates request full clauses/all explicit obligations and remove the
historical 2–4-word artifact restriction. Historical templates remain unchanged.

The following earlier preparation estimates are retained as history, not the
current authorization or runtime envelope:

| Repetitions | Base episodes | Trajectories | All planned calls | Planning envelope |
| --- | ---: | ---: | ---: | ---: |
| 1 | 48 | 96 | 676 | US$1.539338 |
| 2 | 96 | 192 | 1,194 | US$2.747412 |
| 5 | 240 | 480 | 2,748 | US$6.371633 |

The preparer intentionally still emits its historical US$1 `no_go`. The separate
`eval.pilot_runtime` and `eval.pilot_ledger` implement the expanded authorization
without weakening the 12-intent pre-pilot contracts. A 480-trajectory offline
rehearsal exercises all 2,748 planned calls, duplicate selection, blinding,
native stage ordering and shared accounting. Simulation validates machinery,
not provider behavior, corpus admission or semantic validity.
The runtime freezes source/package hashes, SDK/Python identity, model endpoints,
prices and prompts. Every paid response is preserved before usage validation;
an interrupted or unverified call retains its reservation and blocks retries.
Changed bounds or additional calls require an explicit revision that carries
forward prior spend; creating another directory is not a new authorization.

## Evidence basis and roadmap

[CheckList](https://aclanthology.org/2020.acl-main.442/) motivates separating
minimum-functionality, invariance and directional tests rather than relying on
aggregate accuracy. It does not validate our source transformations or thresholds.
The inference that a matched source-based control is useful here is our design
decision, not an empirical result of that paper on this thesis.

Future work remains a small independent human calibration study with a random
audit sample separate from difficult-case review, followed by diagnostic-product
utility and investigation-time evaluation. These do not silently become entry
requirements for this exploratory LLM-only pilot; H1/H2's independent-label
requirements remain unchanged.
