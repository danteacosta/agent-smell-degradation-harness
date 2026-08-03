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

The manifest records provenance and hashes for every row. The feature plane may consume only input fields and provider-produced T0–T3 attributes before the terminal cutoff.
