# Wedge-First Reliability Check — Design

**Date:** 2026-07-22  
**Status:** Approved strategy (wedge-first)  
**Thesis (working title):** Provenance-Based Detection of Requirement-Smell-Induced Semantic Degradation in LLM Coding Agents  
**Product wedge:** Reliability layer for coding agents — not a standalone smell detector.

## Positioning

| Audience | Message |
|----------|---------|
| Thesis | Does **Tier A** provenance detect smell-induced degradation beyond static smell + operational metrics? |
| Product | GitHub/CI check: given spec → agent run, **approve / warn / request clarification** — catches intent loss that naive tests miss. |

Open source = harness + benchmark + **local/CI reliability check**.  
Paid (later) = history, policies, private deploy — moat from workflow + failure data, not AUROC.

## Thesis alignment (narrow)

- Smells in scope: **ambiguity**, **numerical inconsistency**
- Tasks: **codegen**, **test_gen**
- H1: clean/smelly effect exists
- H2: Tier A provenance > static-only and operational-only (group-split by `intent_id`)
- Mitigation = optional stretch

## Temporal cut (leakage control)

| Tier | Role | Examples |
|------|------|----------|
| **A** (features) | Pre-artifact signals only | plan/self-check stubs, constraint_extract *during* generation, operational events **before** independent oracle |
| **B** (label only) | Independent oracle / mutation score | `oracle_passed`, mutation fault-detection rate — **never** in feature set |

## Wedge MVP (this implementation)

1. **Schema:** provenance JSONL tagged `tier: A|B`; feature export excludes Tier B.
2. **Mutation:** smell-relevant mutants for test_gen; score = catch rate on mutants.
3. **RF-11** numerical inconsistency seed (+ keep MesaFlow ambiguity seeds).
4. **CLI + Action:** `python -m wedge.check` → `approve` \| `warn` \| `clarify`; GitHub Action wraps it.
5. **H2 offline script:** group-split AUROC static vs operational vs Tier A (stub/mock data OK).

Decision logic (stub-era wedge):
- `clarify` if static smell detected on input and no clarification/rewrite applied
- `warn` if Tier A risk score high OR mutation/oracle degraded
- `approve` otherwise

Later live: same interface, better features.
