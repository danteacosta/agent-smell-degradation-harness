# Requirements-semantics alignment design

## Context

The thesis now treats requirements smells as context-dependent risk signals and
requires T1 to preserve the semantics of conditional requirements. The current
harness records constraints, quantities, unresolved references, assumptions,
and contradictions, but it cannot distinguish an antecedent from its
consequent, necessity status, temporal relation, or the explicitly considered
negative case. The confirmatory dataset also lacks metadata for project domain
and lifecycle context.

The change is thesis-specific. The ARP core remains domain-neutral, and the
generic RAG and MergeWave repositories remain unchanged.

## Contract

For every T1 interpretation, the runtime accepts the legacy five fields plus
an additive `conditional_semantics` list. Each item has exactly:

```json
{
  "antecedent": "...",
  "consequent": "...",
  "necessity_status": "sufficient_only|also_necessary|undetermined",
  "temporal_relation": "during|next_state|eventually|irrelevant|undetermined",
  "negative_case": {
    "status": "specified|not_specified|not_applicable",
    "description": "... or null"
  }
}
```

Requirements without a conditional clause use `conditional_semantics: []`.
Legacy traces normalize to that empty list so existing development fixtures
remain replayable. The staged provider runtime requires the field explicitly;
the validator's default remains backward-compatible for existing non-provider
fixtures.

The confirmatory source record additionally carries `project_domain`,
`lifecycle_role`, `lifecycle_phase`, and the source-level
`conditional_semantics` annotation plus the explicit
`conditional-semantics/v1` contract version. These fields are metadata/label-plane
context, not deployable features and never encode terminal outcomes or smell
labels.

The source manifest is versioned as `confirmatory-v2`; the previous v1 contract
does not silently accept the new required fields.

## Design

1. Add one thesis-specific validator in `protocol/conditional_semantics.py`.
   It owns exact-key, type, enum, and negative-case validation and returns a
   normalized JSON-compatible value.
2. Reuse the validator in provider checkpoints, staged runtime, replay schema,
   and observability adapters. This prevents the same semantic contract from
   drifting across execution and replay paths.
3. Add the field to T1 prompts and T1 diagnostics. Diagnostics count conditional
   clauses and missing negative-case specifications, but do not convert those
   annotations into terminal labels.
4. Extend the confirmatory JSON schema and dataset validator with domain and
   lifecycle metadata. Keep these fields outside the feature extractor.
5. Document the context-dependent smell interpretation, conditional semantics,
   and metadata boundary in the thesis scope, preregistration, data dictionary,
   and the thesis-specific ARP profile.

## Compatibility and failure modes

- Existing five-field T1 payloads remain valid in replay and generic runtime
  validation and normalize to `conditional_semantics: []`.
- Confirmatory staged-provider execution fails closed when a provider omits the
  field or returns malformed semantics.
- Unknown keys, terminal/outcome keys, invalid enum values, empty text, and
  inconsistent negative-case descriptions are rejected.
- Domain/lifecycle metadata are required in confirmatory source records but are
  not copied into deployable feature rows.

## Acceptance criteria

- A valid conditional item survives T1 validation, staged execution, and
  replay normalization unchanged.
- A malformed conditional item is rejected consistently by runtime and replay
  validators.
- A legacy fixture still validates and gains `conditional_semantics: []`.
- The provider T1 prompt names the structured field and staged confirmatory
  execution rejects its omission.
- Dataset validation requires project domain and lifecycle metadata and keeps
  those fields in the dataset plane.
- Documentation and the ARP thesis profile describe the same schema and the
  same no-leakage boundary.
- The full test suite passes.
