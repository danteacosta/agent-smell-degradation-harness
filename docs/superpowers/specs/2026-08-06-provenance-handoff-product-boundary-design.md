# Provenance, Handoff, and Product-Memory Boundary

## Goal

Add a small, auditable handoff and semantic-quality layer without allowing product memory or post-evaluation labels to contaminate the confirmatory experiment.

## Architecture

The ASD harness keeps one stable identity/provenance contract (`run_id`, `episode_id`, event sequence, parent event, source references, and artifact hashes). An episode handoff is an append-only JSON artifact with an explicit plane: `pre_final` may contain only information available before the final evaluation, while `post_eval` may contain labels, outcomes, and adjudication notes. A semantic linter reports policy violations but never changes the H1/H2 estimand.

The product/RAG layer owns candidate memory and post-run semantic lint. Candidate memories are explicit records with provenance, confidence, and review status; they are not written into the thesis event stream or the corpus vector store.

## Contracts

- `SourceRef`: source kind, stable identifier, and optional content/artifact hash.
- `EpisodeHandoff`: identity, plane, decision, next step, risks, new facts, and source references.
- Lint findings are structured (`code`, `severity`, `message`, `source`) and deterministic.
- Product candidate memory requires provenance and a review status; `accepted` requires a reviewer.

## Data-flow and failure policy

Missing provenance, cross-plane fields, or secret-like keys are lint findings and fail strict validation in tests. Optional observability sinks remain best effort and must not break the application path. No raw transcript vectorization or automatic durable-memory write is introduced.

## Thesis impact

The preregistration changes only to state that handoff/lint artifacts are auditability and quality-control artifacts, excluded from primary H2 features and labels. The deterministic grouped train/calibration/test split and frozen `Delta PR-AUC >= 0.05` margin remain unchanged.

