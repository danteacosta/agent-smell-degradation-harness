# ARP compatibility matrix

The thesis wire contract is `ARP schema 2.0.5`. The Python package version is an implementation dependency and must not silently change the wire contract.

| Consumer | Wire schema | Package/runtime | Status |
|---|---|---|---|
| agent-smell-degradation-harness | 2.0.5 | `agent-reliability-protocol` 2.0.6 | supported by fixture tests |
| rag-reliability-harness | 2.0.5 | `agent-reliability-protocol` 2.0.6 | supported by fixture tests |

Any other package version is unsupported for confirmatory runs until a new matrix row, fixture set, and freeze hash are committed. Confirmatory traces must report both `schema_version` and package version.
