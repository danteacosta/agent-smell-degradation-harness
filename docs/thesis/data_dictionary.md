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
| `atomic_obligations` | T1/pre-final | bounded provider observation of constraint index, atom type and status; raw obligation text is excluded | no |
| `atomic_obligation_observations` | T3/pre-final | hash-bound T1-to-T3 observations assigned to the article-inspired constraint hard lane | no |
| `context_management` | T3/operational | prompt-free transformation events and numeric summaries for the explicit context condition | no |
| `context_interaction` | secondary analysis | post-collection 2x2 difference-in-differences report; never a primary H1/H2 feature | no |
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


Atomic obligations are an additive mechanism observation. The provider reports
only a one-based constraint index, one of the bounded atom types
(actor/action/object/condition/threshold/scope/temporal/exception/modality), and
a status (present/absent/uncertain). The runtime binds these observations to
constraint hashes and planned-check lineage at T3. The
preservation_class=constraint_hard_lane value records the article-inspired
preservation policy; it is not an oracle verdict and does not change the smell
taxonomy.

The secondary context interaction is computed only after terminal outcomes are
available. Its estimand is (clean minus smelly) under
compaction_stress_test minus (clean minus smelly) under no_compaction. It is
reported as protocol/mechanism evidence, outside the 120 primary episodes and
outside the primary H1/H2 estimands.
