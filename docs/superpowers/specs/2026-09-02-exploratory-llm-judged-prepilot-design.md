# Exploratory LLM-Judged Pre-Pilot — Design

**Date:** 2026-09-02
**Status:** Approved by researcher; pending written-spec review
**Scope:** A bounded, non-confirmatory exploratory run using the two already qualified provider configurations as cross-judges.

## Research boundary

This design does not turn an LLM judge into a human annotator, does not close
the confirmatory annotation gate, and does not authorize claims about human
inter-rater reliability. The official launch readiness therefore remains
`no_go` and `confirmatory_authorized=false` until the existing corpus, rights,
ethics, annotation, budget, leakage, and reproducibility gates are satisfied.

The new run is named `exploratory_llm_judged_pre_pilot`. Its purpose is to
validate the end-to-end data path, estimate provider behavior and cost, and
produce preliminary machine-judged outcomes that can inform the later human
protocol. The runner accepts only the authoritative frozen manifest produced
by the private intake flow: exactly 12 admitted unique intents across at least
6 projects. If that manifest does not exist, the exploratory runner makes no
provider call; the already-recorded native smoke remains the only technical
rehearsal.

The US$1.00 limit is interpreted as a hard total cap for one complete
exploratory run, including generation, judging, retries, and contingency. A
preflight estimate must be below the cap; the runner must stop before a call
that could exceed the remaining allowance.

## Alternatives and decision

1. **LLM-only exploratory run (selected):** each qualified provider generates
   the fixed 120-episode matrix, and both independently judge every generated
   artifact. It gives cross-provider evidence at bounded cost, but remains
   non-confirmatory.
2. **LLM run plus researcher audit:** add a manual audit of a declared subset.
   This improves error discovery but is still not equivalent to two trained,
   independent human annotators and increases schedule risk.
3. **Human-confirmatory pre-pilot:** complete the original human annotation,
   adjudication, and institutional documentation gates first. This is the
   strongest design for confirmatory claims but is not the goal of tomorrow's
   exploratory run.

## Frozen inputs and blindness

Before any judgment call, freeze and hash:

- the admitted corpus manifest and its provenance/rights decisions;
- the generation configuration, immutable model versions, prompts, and output
  schema;
- the dedicated acceptance-criteria judge rubric and judge prompt;
- a 20% duplicate subset selected deterministically from generated-artifact
  IDs before any judge outcome is observed.

Each judge receives only an opaque task ID, the generated acceptance-criteria
artifact, and the independently constructed reference constraints. The
target defect family is hidden from the judge; it is retained only in the
private join used for later stratification. The payload must also exclude
source labels, `variant`, oracle output, provider/model identity, run outcome,
checkpoint/T4 material, and any field derived from those values. A validation
boundary rejects raw secrets, unapproved raw corpus fields, labels, and
unknown sensitive fields before the provider adapter is called.

The duplicate artifacts are presented as separate blinded tasks with fresh
opaque occurrence IDs. A fresh call is made for each occurrence so the report
can measure intra-judge repeatability; the duplicate subset is not treated as
human inter-rater reliability.

## Run contract and judging schema

The implementation must expose one explicit call plan. The existing study
matrix defines 120 base episodes as 12 intents × 2 variants × 5
replications. Both provider configurations generate that matrix, so the
counts for one complete exploratory run are:

| Unit | Count | Meaning |
| --- | ---: | --- |
| Base episodes | 120 | Frozen study cells before provider assignment |
| Generation artifacts | 240 | 120 episodes for each of the two provider configurations |
| Duplicate base artifacts | 48 | Exactly 20% of the 240 artifacts, selected before judging |
| Judging occurrences per judge | 288 | 240 originals + 48 duplicate occurrences |
| Logical judging calls | 576 | 288 occurrences × 2 judges |
| Logical provider calls | 816 | 240 generation + 576 judging |
| Maximum attempts per logical call | 2 | Initial attempt plus at most one bounded retry |

The private join uses independent identifiers: `episode_id` identifies a study
cell, `artifact_id` identifies one provider output, `base_task_id` identifies a
judging input, and `occurrence_id` identifies an original or duplicate
presentation. Judge payloads contain only a freshly generated opaque
`occurrence_id`; the private join maps it back to artifact, episode, source
intent, variant, replication, and provider after judging. No identifier may
encode a hidden label, provider, variant, or defect family.

This run uses a dedicated rubric schema named
`acceptance-criteria-llm-judge/v1`; it does not reuse the existing
`requirements-smell-llm-panel` contract, whose `target_family` field and
`clean/smelly` labels describe a different secondary natural-language-smell
instrument. The dedicated rubric freezes:

- allowed labels: `clean`, `minor`, `moderate`, `severe`, `not_visible`;
- visible input fields: `occurrence_id`, `generated_acceptance_criteria`, and
  `reference_constraints` containing stable constraint IDs and their text;
- forbidden input fields: source labels, target defect family, provider/model
  identity, variant, oracle output, detector output, checkpoint/T4 fields, and
  raw secret fields;
- required response fields: `label`, `confidence`, `evidence_span`,
  `rationale`, and one `constraint_assessment` for each supplied constraint;
- `not_visible` for insufficient context or a technically unclassifiable
  artifact, never an imputed clean/smelly result.

The rubric must define the severity anchors before the first call: `clean`
means all supplied constraints are adequately operationalized; `minor`,
`moderate`, and `severe` mean increasing material omissions or incorrect
conditions; `not_visible` means the evidence cannot support a severity label.
The target defect family is not repeated in the prompt and cannot be inferred
from a gold label. The judge evaluates coverage and operationalization of the
visible reference constraints, while the private analysis retains the
predefined experimental condition for stratification only.

## Generation and judging flow

The existing runtime-native generation path remains the source of provider
evidence. The canonical configurations are OpenAI `gpt-5.6-luna` and
DeepSeek `deepseek-v4-pro` with their recorded immutable version identifiers.
The judge matrix is cross-provider: each eligible generated artifact is sent
to both judge configurations, with provider/model metadata removed from the
judge payload. Raw responses stay in private evidence storage; the public
report contains only structured labels, agreement, uncertainty, hashes,
usage, latency, cost, and error categories.

The primary exploratory outcome is conservative:

- exact agreement between both judges → `consensus` with the shared label;
- any disagreement, invalid response, or unresolvable retry → `uncertain`;
- no majority vote or hidden adjudication is applied with only two judges.

This is an Adapter boundary around the existing provider clients, not a new
provider abstraction: the adapter normalizes a frozen judge request into the
existing runtime-native client contract and validates the structured response.
No Strategy or Factory pattern is justified unless a second, materially
different judging policy is later added.

## Failure, privacy, and cost controls

There are two distinct failure classes. Preflight failures — missing or
non-authoritative corpus admission, incomplete rights, non-immutable
configuration, prompt/schema drift, blind-payload violations, or a worst-case
cost estimate above the cap — stop before the first provider call. Runtime
item failures — transport failure, rate limit, malformed judge JSON, or a
response that remains unclassifiable after the bounded retry — become an
item-level `uncertain` record with an explicit error class; they do not get
silently replaced by the other judge. A provider failure is reported per
item/provider.

Missing usage, missing price, or any ledger discrepancy is different: because
the charge cannot be reconciled safely, the runner stops all subsequent calls
and marks the run `cost_unverified`. It never guesses a cost or continues
against an unknown remaining budget.

The private cost ledger is the single authority for generation, judging,
duplicates, retries, and contingency. Before each attempt it reserves a
conservative upper bound computed from the configured input-token bound,
maximum output tokens, immutable prices, and the remaining attempt count. A
preflight calculation must show that all 816 logical calls at two attempts
each fit below the US$1.00 cap. After each response the actual usage and cost
are reconciled; reservations are not allowed to release money back into a
later call if that would violate the worst-case guarantee. The cap is total,
not per provider or per item.

API keys are read only from the existing environment and never copied into
the repository, reports, prompts, logs, or Google Drive. Raw requirement text
and provider responses remain private. Drive updates contain methodology,
status, hashes, and redacted evidence references only.

Advisor authorization is recorded as researcher-reported scope approval. The
record must not invent an advisor identity or date. Ethics/privacy status is
recorded separately: advisor permission does not itself prove that an
institutional review was unnecessary, completed, or approved. Rights to
transform and transmit each source remain a corpus gate regardless of who
authorized the experiment.

## Launch-plan representation

Extend the launch metadata without changing the fail-closed confirmatory
evaluator:

- preserve `status: blocked`, `confirmatory_authorized: false`, and the
  original human annotation requirements;
- add an explicit exploratory mode and its scope approval in a separate
  exploratory run block, without changing the meaning of the existing
  confirmatory gates;
- record the two qualified provider configurations and the US$1.00 total cap;
- record that judge outputs are machine-generated exploratory labels, that
  disagreements resolve to `uncertain`, and that no human adjudication was
  performed;
- link the private run report and redacted reproducibility metadata after the
  run.

The authoritative corpus transition is still the private intake output at
`data/prepilot/corpus-manifest.json` with schema `prepilot-corpus/v3` and
`status: frozen`, exactly 12 admitted records, at least 6 projects, complete
rights/provenance, near-clone review, and manipulation checks. A candidate
pool, template, checked-in seed, or readiness report cannot substitute for
that manifest.

The readiness report must show the exploratory result separately from the
official `decision`. A successful exploratory run cannot make the official
decision `go`.

## ATDD/BDD acceptance criteria

1. **Corpus gate:** Given no authoritative frozen manifest with 12 admitted
   unique intents across at least 6 projects or incomplete rights/provenance,
   when exploratory execution is requested, then no provider call is made and
   the run is classified as blocked.
2. **Blindness:** Given a payload containing provider identity, hidden labels,
   T4 data, or raw secrets, when it reaches the judge boundary, then it is
   rejected without network activity or value leakage.
3. **Call-plan completeness:** Given an admitted 12-intent corpus, when the
   run is preflighted, then it declares 240 generation artifacts, 48 frozen
   duplicate artifacts, 576 judging calls, 816 logical provider calls, and a
   two-attempt upper bound before network activity.
4. **Cross-judging:** Given an eligible artifact, when both providers judge
   it, then the report records both independent outcomes and their metadata,
   without exposing the provider identity to either judge.
5. **Conservative disagreement:** Given different valid labels, when the
   outcome is consolidated, then the result is `uncertain` and no forced
   adjudication is recorded.
6. **Duplicate repeatability:** Given the frozen 20% duplicate subset, when
   judging completes, then duplicate occurrences are identifiable only in
   private metadata and intra-judge agreement is reported separately.
7. **Budget:** Given a projected or accumulated cost at the US$1.00 cap, when
   another call could exceed the remaining amount, then the runner stops and
   records a budget-exhausted result.
8. **Cost reconciliation:** Given a response without usage/pricing or a
   ledger mismatch, when the runtime detects it, then it stops subsequent
   calls and records `cost_unverified` without guessing.
9. **Claim boundary:** Given a successful machine-judged run, when readiness
   is evaluated, then the official confirmatory decision remains `no_go` and
   the claim level remains non-confirmatory.

## Verification plan

Add public-boundary tests for preflight blocking, blind-payload rejection,
cross-judge consolidation, invalid JSON, retries, duplicate repeatability,
cost stopping, secret non-disclosure, and preservation of the official
fail-closed readiness result. Run the full offline suite and the existing
native smoke qualification before the live run. The live run itself must
produce a private raw evidence bundle, a redacted report, a configuration
hash, a source revision, and a cost reconciliation.

## Explicit non-goals

- claiming confirmatory results or human annotation reliability;
- marking human annotation, ethics, corpus, or rights gates true without
  evidence;
- copying secrets or raw corpus text to Drive or the repository;
- silently substituting a provider, model alias, prompt, or temperature;
- adding a third LLM or inventing an adjudicator to manufacture agreement.
