# ARP compatibility matrix

Confirmatory collection emits native `ARP 3.0.0` with profile `agent-smell-degradation/v1`. Historical replay fixtures retain the `2.0.5` wire and are read through ARP 3.0's explicit compatibility surface.

| Consumer | Wire schema | Package/runtime | Status |
|---|---|---|---|
| agent-smell-degradation-harness confirmatory producer | 3.0.0 | ARP commit `95c93db4` | native profile validation |
| agent-smell-degradation-harness replay | 2.0.5 | ARP commit `95c93db4` | compatibility-only, non-confirmatory |
| rag-reliability-harness | 2.0.5 | migration pending | product/replay evidence only |

Any other package version is unsupported for confirmatory runs until a new matrix row, fixture set, and freeze hash are committed. Confirmatory traces must report both `schema_version` and package version.
