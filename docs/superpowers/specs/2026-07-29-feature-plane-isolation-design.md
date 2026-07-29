# Feature-plane Isolation Design

## Goal

Eliminate oracle and terminal-artifact leakage from pre-final feature extraction so that H2 features are derived only from requirement input and pre-final provenance events.

## Acceptance contract

- Given an episode and its pre-final trace, extracting features must not read an oracle specification, oracle result, terminal label, or artifact.
- Given Tier B events in a trace, extracting features must ignore them completely.
- Given the repository, the feature-plane package must not import `label_plane`, `eval.oracles`, or `pairs.loader`, and it must not mention `oracle_spec` in production code.
- Given an artifact and oracle specification, label calculation remains available only through the label plane.

## Design

Introduce two top-level ownership boundaries:

- `feature_plane/` owns pre-final, deployable feature extraction. Its extractor accepts the episode's input-facing fields and filtered provenance events. It produces static-smell, operational, and semantic-provenance feature families using only event shape: presence, count, payload field count, and comparator presence.
- `label_plane/` owns terminal evaluation. Existing oracle and mutation scoring remain in their current implementation locations for this focused change, but are exposed from this boundary so later migrations have an explicit destination.

`observability.features.extract_tier_a_features` remains as a compatibility wrapper during the migration and delegates to `feature_plane`. It must not retain oracle-loading code.

## Data flow

`requirement input + Tier A events -> feature_plane -> H2 detector`

`artifact + oracle specification -> label_plane -> evaluation labels`

There is no path from the feature plane to either the artifact or the label plane.

## Feature contract

The semantic-provenance family replaces oracle-dependent `constraint_match`, `payload_matches_artifact`, and `is_weak_comparator` with:

- `constraint_event_present`
- `constraint_field_count`
- `constraint_has_comparator`
- `semantic_event_count`

These are observable before final-artifact evaluation and do not encode a hidden expected answer. Existing static-smell and operational features retain their current behavior.

## Tests

Add behavior tests proving Tier B data is ignored and semantic features are invariant when only an artifact or oracle differs. Add an architectural test that rejects prohibited imports and `oracle_spec` references in `feature_plane`. Update H2 expectations to the neutral feature contract.

## Non-goals

This change does not make `constraint_extract` a true T1 checkpoint; the runner currently records it after generation. Checkpoint timing is the next independent P0 change. This change also does not alter task adapters, providers, datasets, or mitigation.
