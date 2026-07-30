# Three-Repository Reliability Delivery Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Deliver the agent-smell scientific harness, RAG operational harness, and a neutral protocol with two compatible published releases.

**Architecture:** Work in dependency order: prove agent-smell's scientific boundary, converge temporary local contracts, mature RAG, then extract a dependency-free protocol. Each release is gated by consumer contract suites and neutral-domain tests.

**Tech Stack:** Python 3.11+, pytest, JSON Schema, JSONL, OpenTelemetry/OpenInference adapters, GitHub.

---

## Phase 1 — Agent-smell P0 gates

1. Replace pseudo-checkpoints with ordered T0–T4 lifecycle events, including an interpretation event before artifact completion.
2. Introduce provider adapters (OpenAI, replay, mock, stub) and ensure the live experiment path actually constructs the live provider.
3. Replace fixed task families with AcceptanceCriteria, Traceability, and optional CodeGeneration adapters.
4. Create replication-safe identity at episode construction; migrate outputs to protocol-shaped runs.
5. Complete independent label-plane layout and V4 benchmark metadata/dataset card.
6. Add group-safe evaluation, estimands, boundary-map output, and reproducible 120-episode pre-pilot.
7. Update README and relocate mitigation from the critical pipeline.

## Phase 2 — Experimental shared contract

1. Add identical neutral `protocol_next/` identity, manifest, event, evidence, decision, redaction, schema, exporter, and contract-check APIs to each harness.
2. Prove equivalent envelope and at least 80% common manifest fields through cross-repository fixtures.
3. Keep each harness's domain science/operations outside this directory.

## Phase 3 — RAG P0 gates

1. Add full manifest and lifecycle event emission.
2. Replace booleans/string reasons with structured GateDecision, evidence, and ownership.
3. Formalize generator and retrieval adapters.
4. Add threshold provenance, replay by manifest, and unified check CLI.
5. Preserve secret-free closed-loop and regression simulations.

## Phase 4 — Protocol extraction and publication

1. Create `agent-reliability-protocol` v0.1.0 with ARP-01 through ARP-12.
2. Migrate both harnesses to consume it; run contract, schema, and full consumer verification.
3. Release compatible v0.1.1; update both consumers and repeat verification.
4. Review acceptance matrix, commit, push branches, create GitHub repositories/releases, and publish documentation.

