# Research-stack measurement and implementation audit

This audit concerns four linked research repositories, not every unrelated local
project. Fixes improve instrument reliability; none is new evidence for H1/H2.
Original checkouts and frozen experimental packets were preserved.

## Integrated fixes

| Repository | Observed problem | Correction and verification |
|---|---|---|
| MergeWave | Additional changes to already-dirty files escaped path-set comparison; path parsing lost exact identities and conflated literal POSIX backslashes with separators. | Content/index/mode snapshots and NUL-delimited Git paths, with ambiguous backslashes rejected. PR24:123 local tests, four green CI checks; merge9fa862d. This remains an observational verifier, not a filesystem sandbox. |
| ARP | Malformed event identities/checkpoints reached set operations after validation and raised TypeError. | Validate collection and identity shapes before dependent operations. PR20:132 local tests, three green CI checks; mergef6ecaf8. |
| RAG harness | Recall used a denominator capped at k; repeated IDs inflated recall and binary nDCG, including values above1. | Versioned retrieval-set-v2: full unique relevant-set recall, one credit per document at its original rank. Cross-contract gate comparisons fail explicitly. PR16:196 CI tests including PostgreSQL, gate and loop pass; mergeb84955c. |

Sources: [MergeWave24](https://github.com/danteacosta/MergeWave/pull/24),
[ARP20](https://github.com/danteacosta/agent-reliability-protocol/pull/20),
[RAG16](https://github.com/danteacosta/rag-reliability-harness/pull/16).
Every merge used the exact reviewed head after green CI; merged trees matched.

## Scientific consequences

Legacy RAG outputs are not silently reinterpreted under the new definition.
The original CI baseline remains unchanged; a separate40-item deterministic
re-evaluation supplies the new baseline, source/input hashes and full per-item
rankings. Its aggregate gate values are unchanged because this fixture has
one relevant ID per retrieval query. That equality is not a retrieval improvement.
Historical threshold calibration is not relabeled or claimed newly validated.
Existing scientific results need separate recomputation from original rankings
where available; aggregates alone cannot recover corrected scores.

The browser successor independently reproduced two oracle mistakes before any
model generation: invisible labels passed and harmless outer-item formatting
failed. The corrected common interface fixes one visible label per list item;
exact label text preserves the trim test. Nine real browser controls cover both
focus implementations, focus omission, missing clearing, controller spoofing,
outer formatting, hidden labels, missing trimming and a missing-label interface.
Interface and infrastructure errors remain distinct from requirement failures.
These controls qualify a measurement instrument; they do not establish an LLM
effect. See [successor protocol](../plans/2026-09-22-criteria-code-chain.md).

## Writing and interpretation

Current summaries must distinguish completed exploratory work from historical
blocked checkpoints. LLM-panel agreement is not human validation. Behavioral
counterexamples concern the tested source obligation under the specified runtime;
they do not establish a general effect of smells. H2 still requires its frozen
B3-versus-B0 pre-final contrast on independent projects. The source-to-criteria
and criteria-to-code route comparison changes information and representation,
so it is not a causal mediation estimate.
