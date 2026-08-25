# Confirmatory Data Dictionary

| Field | Plane | Meaning | Allowed in deployable features |
|---|---|---|---|
| `source_intent_id` | dataset | independent source requirement identity | no |
| `project_id` | dataset | project holdout group | no |
| `project_domain` | dataset | project/product domain used for heterogeneity and external-validity checks | no |
| `lifecycle_role` | dataset | role of the requirement in the lifecycle | no |
| `lifecycle_phase` | dataset | lifecycle phase in which the source requirement is situated | no |
| `defect_family` | dataset | controlled smell/degradation family | no |
| `conditional_semantics` | dataset/T1 | bounded annotation of antecedent, consequent, necessity, temporal relation, and negative case | no |
| `conditional_semantics_schema` | dataset/T1 | explicit version of the bounded conditional-semantics contract | no |
| `variant` | design | clean or natural smelly variant | no |
| `replication_id` | design | repeated measurement index | no |
| `requirement_text` | input | provider-visible requirement text | yes |
| `task_family` | input | task family requested | yes |
| `artifact` | terminal | generated terminal output | no |
| `oracle_passed` | label | executable outcome | no |
| `semantic_label` | label | adjudicated terminal label | no |
| `traceability_links` | label/evidence | hashed claim-to-artifact links | no |
| `episode_handoff` | audit/QC | versioned pre-final or post-evaluation sidecar with source references | no |
| `semantic_lint_findings` | audit/QC | deterministic provenance and plane-boundary findings | no |
| `source_refs` | provenance | source kind, identifier, optional content hash and event sequence | no |
| `features` | derived pre-final | numeric static, operational, and provenance families recomputed at T3 | yes |
| `checkpoint_features.T1/T2/T3` | derived pre-final | numeric provenance family recomputed at each frozen cutoff | yes |

The `h2-features/v3` manifest records provenance and hashes for every row and
forbids precomputed scores. Validation recomputes every declared feature from
the bound trace and verifies the T1/T2/T3 event IDs and cutoff sequences. The
feature plane may consume only input fields and provider-produced T0–T3
attributes before the terminal cutoff.

Handoff and lint artifacts are retained for reproducibility and failure diagnosis, but are excluded from H1/H2 feature extraction and from primary labels. Product candidate memory is maintained outside the thesis dataset and is never joined into confirmatory rows.

`conditional_semantics` is an explicit list. Each item contains `antecedent`,
`consequent`, `necessity_status` (`sufficient_only`, `also_necessary`, or
`undetermined`), `temporal_relation`, and `negative_case` (`specified`,
`not_specified`, or `not_applicable`). The empty list means that no conditional
clause was identified. These annotations are interpretation evidence, not
terminal labels, smell outcomes, or oracle data. Project-domain and lifecycle
fields are context metadata for planned heterogeneity analyses; they are never
copied into `features`.

The source manifest is versioned as `confirmatory-v2` because these required
metadata fields are not backward-compatible with the previous source contract.
The current development seed is still blocked from confirmatory claims by its
missing external provenance and project assignments.
