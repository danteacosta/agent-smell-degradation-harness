# Provenance, Handoff, and Product-Memory Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add auditable episode handoffs and deterministic semantic lint while preserving the thesis estimand and defining a separate product candidate-memory contract.

**Architecture:** ASD owns provenance and episode handoff artifacts with explicit pre-final/post-evaluation planes. RAG owns product candidate memory and post-run lint. Only stable identity/provenance fields are shared conceptually; no labels or raw product memory cross the boundary.

**Tech Stack:** Python 3.11+, dataclasses, JSONL/JSON, pytest.

---

### Task 1: ASD handoff and provenance contract (`/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product`)

**Files:**
- Create: `observability/handoff.py`
- Modify: `observability/tracing.py`
- Test: `tests/test_handoff.py`

- [ ] Write failing tests for source references, pre-final field isolation, and deterministic JSON output.
- [ ] Run `pytest tests/test_handoff.py -q` and confirm the new API is missing.
- [ ] Implement `SourceRef`, `EpisodeHandoff`, `build_handoff`, `write_handoff`, and recorder support for source references.
- [ ] Run the focused tests, then the ASD suite.

### Task 2: ASD semantic lint and thesis boundary documentation (`/Users/dantecosta/Projects/agent-smell-degradation-harness/.worktrees/thesis-product`)

**Files:**
- Create: `observability/semantic_lint.py`
- Create: `tests/test_semantic_lint.py`
- Modify: `docs/thesis/preregistration.md`
- Modify: `docs/thesis/data_dictionary.md`

- [ ] Write failing tests for missing source references, label fields in `pre_final`, and secret-like keys.
- [ ] Implement deterministic structured findings and strict-mode validation.
- [ ] Document that handoff/lint are QC artifacts excluded from H1/H2 primary features and labels.
- [ ] Run the ASD suite.

### Task 3: RAG candidate memory and post-run lint (`/Users/dantecosta/Projects/rag-reliability-harness/.worktrees/product-layer`)

**Files:**
- Create: `product_memory/__init__.py`
- Create: `product_memory/candidates.py`
- Create: `observability/semantic_lint.py`
- Create: `tests/test_candidate_memory.py`
- Create: `tests/test_semantic_lint.py`
- Modify: `docs/product/README.md`

- [ ] Write failing tests for provenance-required candidates, review gating, and structured lint findings.
- [ ] Implement append-only candidate JSONL storage and deterministic lint.
- [ ] Document that product memory is separate from the RAG corpus store and thesis label plane.
- [ ] Run the RAG suite.

### Task 4: Verify and record thesis changes (ASD worktree plus connected Google Doc)

**Files:**
- Modify: Google thesis document through the connected Google Docs workflow.

- [ ] Update the methodology/data-governance section with the audit-artifact boundary.
- [ ] Re-read the document and confirm H2 split, margin, and pre-pilot wording are unchanged.
- [ ] Run both repository suites and inspect the final diff.
