# Confirmatory Data Dictionary

| Field | Plane | Meaning | Allowed in deployable features |
|---|---|---|---|
| `source_intent_id` | dataset | independent source requirement identity | no |
| `project_id` | dataset | project holdout group | no |
| `defect_family` | dataset | controlled smell/degradation family | no |
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
