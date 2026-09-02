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
protocol. If the intake does not admit exactly 12 unique intents across at
least 6 projects, a reduced execution is a technical rehearsal only and must
not be reported as the pre-pilot.

The US$1.00 limit is interpreted as a hard total cap for one complete
exploratory run, including generation, judging, retries, and contingency. A
preflight estimate must be below the cap; the runner must stop before a call
that could exceed the remaining allowance.

## Alternatives and decision

1. **LLM-only exploratory run (selected):** both qualified providers generate
   outputs and both independently judge every eligible output. It is feasible
   immediately after corpus admission and gives cross-provider evidence at low
   cost, but remains non-confirmatory.
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
- the annotation rubric and judge prompt;
- a 20% duplicate subset selected deterministically from item IDs before any
  outcome is observed.

Each judge receives only the generated artifact and the allowed task/reference
constraints. The payload must exclude source labels, `variant`, defect family,
oracle output, provider/model identity, run outcome, checkpoint/T4 material,
and any field derived from those values. A validation boundary rejects raw
secrets, raw corpus exports, labels, and unknown sensitive fields before the
provider adapter is called.

The duplicate items are presented as separate blinded tasks. A fresh call is
made for each occurrence so the report can measure intra-judge repeatability;
the duplicate subset is not treated as human inter-rater reliability.

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

The run fails closed on missing rights, incomplete manifest, non-immutable
configuration, prompt/schema drift, blind-payload violations, malformed judge
JSON, missing usage, budget exhaustion, or any provider response that cannot
be safely classified. Retries are bounded and included in the cap. A provider
failure is reported per item/provider; it cannot be silently replaced by the
other judge.

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
- add an explicit exploratory mode and its scope approval;
- record the two qualified provider configurations and the US$1.00 total cap;
- record that judge outputs are machine-generated exploratory labels, that
  disagreements resolve to `uncertain`, and that no human adjudication was
  performed;
- link the private run report and redacted reproducibility metadata after the
  run.

The readiness report must show the exploratory result separately from the
official `decision`. A successful exploratory run cannot make the official
decision `go`.

## ATDD/BDD acceptance criteria

1. **Corpus gate:** Given fewer than 12 admitted unique intents or incomplete
   rights/provenance, when execution is requested, then no provider call is
   made and the run is classified as blocked or technical rehearsal.
2. **Blindness:** Given a payload containing provider identity, hidden labels,
   T4 data, or raw secrets, when it reaches the judge boundary, then it is
   rejected without network activity or value leakage.
3. **Cross-judging:** Given an eligible artifact, when both providers judge
   it, then the report records both independent outcomes and their metadata,
   without exposing the provider identity to either judge.
4. **Conservative disagreement:** Given different valid labels, when the
   outcome is consolidated, then the result is `uncertain` and no forced
   adjudication is recorded.
5. **Duplicate repeatability:** Given the frozen 20% duplicate subset, when
   judging completes, then duplicate occurrences are identifiable only in
   private metadata and intra-judge agreement is reported separately.
6. **Budget:** Given a projected or accumulated cost at the US$1.00 cap, when
   another call could exceed the remaining amount, then the runner stops and
   records a budget-exhausted result.
7. **Claim boundary:** Given a successful machine-judged run, when readiness
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
