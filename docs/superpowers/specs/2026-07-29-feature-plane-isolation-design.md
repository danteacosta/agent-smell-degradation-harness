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

- `feature_plane/` owns pre-final, deployable feature extraction. Its public input is an explicit `FeatureEpisodeInput` model containing only `intent_id`, `task_family`, `variant`, `smell`, and `requirement_text`, plus a provenance path. It cannot accept the source episode dictionary, which may carry terminal fields. The extractor loads the trace and filters it to Tier A itself before any feature family runs. It produces static-smell, operational, and semantic-provenance feature families using only event shape: presence, count, payload field count, and comparator presence.
- `label_plane/` owns terminal evaluation. It exposes `score_artifact(...)` and `score_test_gen_mutation(...)` as its public API and delegates initially to the existing implementations. Evaluation callers migrate to these imports; `feature_plane` must never import them.

`observability.features.extract_tier_a_features` remains as a compatibility wrapper during the migration and delegates to `feature_plane`. It builds `FeatureEpisodeInput` only from the allowlisted fields and must not retain oracle-loading code. It must ignore an episode's artifact, oracle, label, and mutation fields. `baselines.features` delegates its static, operational, and provenance-semantic families to the same feature-plane API; its intentionally retrospective `output_only` family remains separate and clearly labelled as a non-deployable upper bound.

## Data flow

`allowlisted requirement input + raw trace -> feature_plane (own Tier A filter) -> H2 detector / deployable baseline / wedge Tier-A risk`

`artifact + oracle specification -> label_plane -> evaluation labels`

There is no path from the feature plane to either the artifact or the label plane.

## Feature contract

The semantic-provenance family replaces oracle-dependent `constraint_match`, `payload_matches_artifact`, and `is_weak_comparator` with:

- `constraint_event_present`
- `constraint_field_count`
- `constraint_has_comparator`
- `semantic_event_count`

These are observable before final-artifact evaluation and do not encode a hidden expected answer. Existing static-smell and operational features retain their current behavior.

H2, deployable-baseline scoring, and wedge Tier-A risk migrate from the removed fields to a neutral completeness score based on absent constraint extraction and its observable shape. Their terminal oracle/mutation decision paths remain label-plane consumers and are not used to construct Tier-A features.

## Tests

Add behavior tests proving Tier B data is ignored by the extractor itself and semantic features are invariant when only an artifact, oracle, label, or mutation score differs. Add a source/data-access test that rejects prohibited imports, `oracle_spec` references, and terminal-field access in `feature_plane`; add the required `test_feature_plane_cannot_import_label_plane`. Add compatibility-wrapper and H2 integration tests for the neutral feature contract.

The static feature family is limited to `smell` and `requirement_text`; the operational family is limited to Tier A latency and event count. These sources are explicitly non-terminal and must be tested as such.

## Non-goals

This change does not make `constraint_extract` a true T1 checkpoint; the runner currently records it after generation. Checkpoint timing is the next independent P0 change. This change also does not alter task adapters, providers, datasets, or mitigation.
