# Context-management control for the pre-pilot

Decision date: 2026-09-01  
Scope: non-confirmatory pre-pilot and later confirmatory protocol  
Status: implemented in the staged runtime; real-provider qualification remains blocked

## Why this belongs in related work

Long-context models do not use all positions equally. Liu et al. show a
position-dependent retrieval/use pattern in which relevant information can be
underused when it appears in the middle of a long context. This makes context
length and information position a plausible operational mechanism for apparent
constraint loss, even when the input requirement itself is unchanged.

Prompt compression is also an established systems intervention. LLMLingua
treats compression as a budgeted transformation whose semantic impact must be
measured, rather than assuming that fewer tokens are free. LongBench provides a
multi-task evaluation setting that includes code completion and supports the
broader concern that long-context behavior must be tested across task types.

A recent arXiv preprint, The Compaction Cliff in Long-Running AI Agent Memory,
reports substantial survival loss for safety rules after repeated compaction and
proposes type-aware memory triage. Its reported 53% after one compaction and 10%
after five compactions are treated here as emerging motivation, not as
established thesis evidence: the exact figures were not independently verified
against a peer-reviewed final paper as of this decision date. The linked
industry article is useful as a practitioner signal but is not used as
quantitative evidence.

This literature supports a threat/mechanism control. It does not justify
replacing the thesis's requirement-mutation estimand with a general claim about
memory systems.

## Experimental decision

The primary pre-pilot remains:

- 12 independent intents;
- clean and controlled missing-condition variants;
- five replications per variant;
- 120 episodes total;
- no_compaction as the context-management condition.

The secondary protocol crosses:

| Requirement factor | Context factor |
| --- | --- |
| clean | no_compaction |
| smelly | no_compaction |
| clean | compaction_stress_test |
| smelly | compaction_stress_test |

The secondary matrix is a protocol/stress and interaction check. It is not
added to the 120 primary episodes, is not treated as confirmatory H1/H2
evidence, and cannot be used to silently change the primary estimand. A future
study may preregister a context-factor interaction once a real provider hook,
budget, and power analysis are available.

## Instrumentation contract

The runtime emits prompt-free context events inside the canonical pre-final
tool.completed payload. Each event contains exactly:

- schema_version;
- event_id;
- stage;
- operation;
- trigger;
- started_at and ended_at;
- context_size_before and context_size_after;
- context_size_unit;
- checkpoint_id;
- checkpoint_sha256.

The current measured unit is utf8_bytes; it is deliberately not a token
estimate. Provider-reported input/output token usage remains a separate
qualification field. checkpoint_sha256 binds the event to the
provider-visible context while the context itself is never persisted in this
event.

The primary identity manager emits operation=none, equal before/after sizes,
and trigger=policy_disabled. The deterministic compactor is test-only: it
uses a fixed byte budget and a fixed prefix/suffix transformation. It is not a
claim about any production provider's /compact, summarizer, eviction policy,
or memory implementation.

T1 and T2 events are copied into the T3 execution payload and therefore remain
available to the pre-final feature boundary. The terminal artifact request is
summarized only in provider metadata and is excluded from T1/T2/T3 features.
No event stores a raw prompt, artifact, oracle, label, variant, private
reasoning, or terminal outcome.

The derived operational features are:

- context_management_event_count;
- compaction_count;
- context_size_before_bytes;
- context_size_after_bytes;
- context_size_reduction_bytes.

They are zero/empty for legacy traces that predate the contract. The raw
feature version is pre-final/v4; the structural manifest remains
h2-features/v3.

## Threat to validity

### Context-management-induced constraint loss

An unobserved compaction, truncation, eviction, or retrieval transformation can
remove or weaken a constraint independently of the controlled requirement
mutation. If such events are mixed across conditions, an observed degradation
cannot be attributed cleanly to the missing-condition manipulation.

The primary condition therefore disables compaction and reports any nonzero
event as a protocol violation or separate operational failure. The secondary
matrix makes the mechanism explicit for stress testing. Telemetry improves
auditability but cannot prove that a constraint was semantically preserved;
terminal artifact evaluation and independent labels remain necessary.

## Pre-pilot unblock sequence

1. Run the offline context matrix and strict checkpoint/feature tests.
2. Qualify the hook on two real runtime-native provider configurations.
3. Verify T1/T2/T3 ordering, context event hashes, measured sizes, token usage,
   failure behavior, and cost export before artifact generation.
4. Keep the launch plan no_go until corpus licensing, provider qualification,
   annotation, budget, reproducibility, and advisor authorization also pass.
5. Run the 120 primary episodes only under no_compaction; report the secondary
   matrix separately.

## Evidence register

| Source | Use in this decision | Evidence level | Credibility (0–10) |
| --- | --- | --- | --- |
| [Liu et al., TACL 2024 — Lost in the Middle](https://aclanthology.org/2024.tacl-1.9/) | Position-dependent long-context use motivates a context threat | Peer-reviewed journal | 9/10 |
| [Jiang et al., EMNLP 2023 — LLMLingua](https://aclanthology.org/2023.emnlp-main.825/) | Compression is a semantic/budgeted intervention, not only a token optimization | Peer-reviewed conference | 8/10 |
| [Bai et al., ACL 2024 — LongBench](https://aclanthology.org/2024.acl-long.172/) | Long-context evaluation across tasks, including code completion | Peer-reviewed conference | 8/10 |
| [Zerhoudi, Mitrović and Granitzer, arXiv 2026 — The Compaction Cliff](https://arxiv.org/abs/2608.22752) | Emerging agent-memory mechanism and stress-test motivation | Preprint; final peer-review status not independently verified | 6/10 |
| [Tech Leads Club practitioner note](https://www.techleads.club/c/blog/o-custo-de-compactar-contexto) | Practitioner signal that prompted this control review | Secondary blog | 2/10 |

## Product implication

The product wedge should expose context-management state as a provenance and
risk dimension of a requirement-integrity check. It should warn when a runtime
cannot attest to context transformations, but it must not claim that a
compaction event caused a terminal defect without an independent artifact
evaluation. This preserves a useful operational feature while keeping the
thesis causal claim narrow.
