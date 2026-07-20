# Sister harness interop

This repo (`agent-smell-degradation-harness`) is a **sister harness** to
[`rag-reliability-harness`](https://github.com/example/rag-reliability-harness).
They share **documented contracts**, not runtime code.

## Boundary

- **No shared Python package** and no monorepo coupling.
- Each repo is independently installable and CI-runnable.
- Cross-repo alignment is maintained by keeping parallel layout and artifact
  shapes stable; changes to contracts are documented here and in the sister repo.

## Shared layout

Both harnesses use the same top-level module names for the evaluation pipeline:

| Module | Role |
|--------|------|
| `eval/` | Oracles, paired metrics, regression simulation, thresholds |
| `gates/` | CI gate runner (`make gate`) |
| `observability/` | Provenance recorder (JSONL spans/traces) |

This repo adds harness-specific packages (`pairs/`, `agents/`, `agent_harness/`)
and tier-gated thesis overlays (`taxonomy/`, `protocol/`, `baselines/`,
`mitigation/`).

## Artifacts

| Artifact | Location | Purpose |
|----------|----------|---------|
| Provenance traces | JSONL under run output dirs | Spans/events for plans, tools, validators, cost/latency |
| Eval metrics | `eval/last_run.json` | Latest paired Δ and oracle results from `make eval` |
| Thresholds | `eval/thresholds.yaml` | Gate limits consumed by `gates/` |
| CI baselines | `eval/baselines/*.json` | Reference metrics for regression checks |

**Gate contract:** `make gate` reads `eval/last_run.json` produced by
`make eval`. `make simulate` injects failure modes for ATDD but must **not**
overwrite `eval/last_run.json` (see Task 9 in the Tier 0–1 plan).

## ATDD

Both harnesses use acceptance-style tests that prove caller-visible behavior:

1. Offline happy path passes without API keys.
2. Injectable failure modes (FM1–FM3 here) fail the gate when injected.
3. `make all` (or CI equivalent) runs test → eval → simulate → gate in order.

Tests live under `tests/`; they assert contracts, not private implementation
details.

## Narrative alignment

Shared story across sister repos:

- Injectable failure modes with measurable before/after gate catch rates.
- Offline-first CI twin suitable for public/portfolio use.
- Threshold-driven gates backed by YAML configuration.

Domain differs: RAG reliability vs. requirement-smell-induced semantic
degradation in agent episodes — but the **harness shape** stays parallel.
