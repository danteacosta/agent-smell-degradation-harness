# Behavioral expansion: scheduling and analysis contract

The direct-code extension starts only after candidate oracle qualification. This
change prepares the finite schedule and analysis without dispatch or scoring a
single model call. The earlier 52-output TodoMVC focus packet remains separate.

## ATDD contract

- Given qualified candidate IDs and exactly three A/B/C variants per source, make
  three repetitions per arm for two fixed model aliases, with one opaque slot ID
  per planned generation. A deterministic seed orders the schedule; variant
  counts remain balanced within intent/model. Pending/deferred candidates cannot
  be scheduled as qualified.
- Given planned slots and any subset of valid target observations, report all
  planned positions. Errors, invalid artifacts, unattempted calls and incomplete
  oracles are unknown, never target failures or passes.
- Given a model/intent, calculate C−A and B−A target-failure bounds from the
  fixed planned denominator. A/B failures remain visible. Aggregate by equal
  project weight, then equal intent weight within project, with per-model results
  and an equal-intent sensitivity. Bounds describe missingness, not confidence.
- Given duplicate, unexpected or contradictory result rows, fail closed before
  any summary. Do not combine previous focus-pilot rows with this cohort.

BDD examples: Given three C failures and three A passes, C−A is [1,1]. Given one
C failure, one C pass and one missing C, versus three A passes, C−A is [1/3,2/3].
Given an entirely missing C arm, its rate is [0,1]. These examples do not imply
an efficacy finding; they are synthetic verification inputs.

## Design

`plan_slots` reads qualified case IDs, project IDs and frozen variant keys. It
emits metadata only; prompts and hidden oracle content are assembled in a later,
separate collector. `summarize` accepts the immutable schedule and observation
rows keyed by slot ID. It owns denominators and descriptive weighting. No new
adapter or provider abstraction is needed. Validation rejects admitted statuses
that have not passed explicit instrument qualification at the later freeze gate.

Failure mode: a missing row remains unknown; a completed row may carry a Boolean
target result only if the observation category is executable. No retry or replacement
is encoded here. A future collector must bind frozen hashes and once-only calls.

Verification: focused behavior tests, static compile, diff review, then CI on the
same commit. Security review focuses on no outbound calls or exposure of hidden
reference/target fields in schedule metadata. Simplicity review removes any
abstraction not needed by the stated estimands.
