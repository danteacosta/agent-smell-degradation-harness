# Confirmatory observability and product-gate design

**Status:** implementation approved by the explicit P0/P1 request.

## Goal

Make the confirmatory path measure provider-produced pre-final semantic
evidence rather than event presence, bind every confirmatory feature score to
an immutable trace/checkpoint manifest, and expose the same evidence as an
actionable pre-merge gate.

## Scientific contract

- The primary task remains acceptance-criteria/test generation.
- Confirmatory runs require a provider implementing T1 interpretation, T2 plan,
  and T3 execution checkpoints; stub and oracle-derived paths remain
  non-confirmatory.
- The primary label is a frozen human/adjudicated binary label. Oracle verdicts
  are validation evidence only.
- Provenance features are derived from variable provider fields: constraints,
  quantities, unresolved references, assumptions, contradictions, validation
  checks, coverage targets, revisions, validation attempts, errors, and
  retrieval events.
- A confirmatory feature manifest requires schema/version, trace hash,
  checkpoint event IDs and cutoff sequence, and finite scores. Direct
  h2_scores/feature_scores embedded in episodes are rejected.

## Product contract

The product wedge consumes a requirement plus a pre-final trace and emits
approve/warn/block with evidence containing the threatened constraint,
checkpoint, confidence, and recommended review/test action. It emits SARIF
properties for CI and operational utility fields without crossing into thesis
labels.

## Data flow and failure modes

provider -> T1/T2/T3 ARP trace -> feature extractor -> calibrated H2/gate

Missing checkpoints, stale trace hashes, missing human labels, unknown feature
schema, or post-final fields fail closed. Dataset provenance and real provider
collection remain data-acquisition gates; this change does not fabricate
external intents or labels.

## Verification

- Unit tests prove payload-sensitive provenance features and risk scores.
- Contract tests reject unbound score injection and incomplete checkpoint
  bindings.
- H2 tests prove human labels are consumed and test-family metrics are
  reported without using oracle labels.
- Product tests prove actionable evidence appears in JSON/SARIF and utility
  metrics are calculated.

