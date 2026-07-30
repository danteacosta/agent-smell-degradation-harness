# Reliability Protocol Delivery Design

## Objective

Deliver the acceptance criteria in the reliability decision across three repositories: the scientific agent-smell harness, the operational RAG harness, and a neutral shared protocol published only after two compatible consumer releases.

## Dependency and release policy

The protocol has no imports from either harness and contains no domain-specific fields. Both harnesses depend only upward on the protocol. Before extraction, each keeps a byte-equivalent experimental contract in `protocol_next/`.

A release is stable only when its schemas, contract suite, and both consumer suites pass. Version `0.1.0` is the first extracted contract. Version `0.1.1` adds only compatible optional fields or behavior and is consumed and validated by both harnesses.

## Delivery phases

1. Agent-smell P0: real T1–T3 checkpoints, pre-final feature/terminal label boundary, provider adapters, task adapters, complete episode identity, dataset/label-plane structure, group splits, and a reproducible 120-episode pre-pilot.
2. Shared experimental envelope: matching identity, manifest, lifecycle event, evidence, decision, redaction, JSONL, and contract checks in both `protocol_next/` directories.
3. RAG P0: structured decision/evidence/owners, run provenance and lifecycle events, generator/retrieval adapters, threshold provenance, replay, and unified CLI.
4. Extraction: create `agent-reliability-protocol` 0.1.0; migrate both harnesses; add 0.1.1 compatibility release and revalidate.
5. Publication: run all applicable test/contract checks, review dependency neutrality and public docs, commit, push, and publish GitHub repositories/releases.

## Acceptance evidence

- Agent-smell: all ten gates including a 12 × 2 × 5 reproducible pre-pilot run, no label leakage, and real checkpoint order.
- RAG: secret-free closed loop, replay-by-manifest, adapters, threshold provenance, structured evidence-backed owners, and three reproducible regression scenarios.
- Protocol: all ARP-01 through ARP-12, JSON Schema fixtures/round trips/backward compatibility, redaction, exporters, CLI contract test, neutral-domain architecture test, plus two compatible validated releases.

