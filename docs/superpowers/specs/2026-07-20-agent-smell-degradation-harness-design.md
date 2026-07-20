# Agent Smell Degradation Harness — Design Spec

**Date:** 2026-07-20  
**Status:** Approved for implementation planning  
**Repo:** `agent-smell-degradation-harness`  
**Sister:** `rag-reliability-harness` (aligned contracts, no shared code)

## 1. Purpose

Build a **complete, tiered research-and-engineering harness** that makes *requirement-smell-induced semantic degradation* in LLM-based software engineering agents measurable, observable, and mitigable — with a public portfolio twin (offline CI gate) and a dissertation path (H1–H5).

This is the empirical substrate for the master's thesis:

> *From Requirement Smells to Runtime Semantic Degradation: A Provenance-Centric Evaluation Framework for LLM-Based Software Engineering Agents*

### Dual Definition of Done

| Audience | Definition of Done |
|----------|-------------------|
| **Public repo (industry/portfolio)** | Offline-first CI gate with three injectable failure modes, `make simulate` / `make gate`, no secrets — same DNA as `rag-reliability-harness`. |
| **Dissertation (academia)** | Reproducible protocol + paired benchmark + results for H1–H5 (including negative/boundary results), packaging C1–C5. |
| **Mitigation (C5)** | Baseline *inside* the protocol (rewrite / clarify), **not** a SaaS product wedge. |

## 2. Goals and Non-Goals

### Goals

- Paired clean/smelly requirement episodes as the unit of analysis.
- Offline stub path for CI; live LLM path for thesis experiments.
- Provenance JSONL independent from semantic labels (anti-circularity).
- Clear Tier 0→3 path covering contributions C1–C5.
- Sister-repo interop via documented contracts (`docs/interop.md`), not a monorepo.

### Non-Goals

- Production AgentOps platform or hosted product.
- Monorepo / shared Python package with `rag-reliability-harness`.
- Claiming mitigation is always beneficial (evaluate trade-offs).
- Traceability as Tier-1 task family (deferred; optional later generalization).

## 3. Architecture (Approach B: Harness-core + thesis overlays)

```
pairs (clean|smelly)
  → agent runner (policy: direct | static_smell | rewrite | clarify)
  → provenance JSONL
  → validators / oracles
  → eval metrics (paired Δ)
  → gates (CI thresholds)
```

**Core** is always present and ships the portfolio twin.  
**Overlays** activate by Tier when the corresponding thesis contribution is under test.

### Sister boundary

Align with `rag-reliability-harness`:

- Layout: `eval/`, `gates/`, `observability/`
- Artifacts: JSONL spans/traces, `thresholds.yaml`, ATDD acceptance tests
- Narrative: injectable failure modes + before/after gate catch rates

Do **not** share runtime code. Document contracts in `docs/interop.md`.

## 4. Components

### Core packages

| Module | Responsibility |
|--------|----------------|
| `pairs/` | Clean/smelly pairs, smell category/type, injection rule, MesaFlow seed |
| `agents/` | Policies + stub and live adapters |
| `observability/` | Provenance recorder (plans, tools, validators, self-checks, cost/latency) |
| `eval/` | Oracles, paired metrics, regression simulation |
| `gates/` | CI gate against `thresholds.yaml` |

### Overlays (tier-gated)

| Overlay | Contribution | When |
|---------|--------------|------|
| `taxonomy/` | C1 | Tier 2 |
| `protocol/` | C3 (docs + stats helpers) | Tier 2–3 |
| `baselines/` | C4 feature families | Tier 2 |
| `mitigation/` | C5 rewrite/clarify | Tier 3 |

### Episode schema (minimum)

```text
episode_id
intent_id
variant: clean | smelly
smell: { category, type, injection_rule } | null
task_family: codegen | test_gen
config: { policy, mode: stub|live, model?, provider? }
artifact
oracle_result
semantic_label          # from oracle/human — NOT from provenance
provenance_path
cost, latency
replication_id
```

**Anti-circularity rule:** compute and persist `semantic_label` / `oracle_result` before extracting provenance features used for characterization or early warning.

## 5. Data flow

### Offline (CI default)

```text
make simulate → inject failure mode → stub runs clean & smelly
  → JSONL provenance → oracle → paired Δ → gates
```

### Live (thesis experiments)

```text
make experiment → live adapter → N replications
  → same schema → export for mixed-effects / paired analysis
```

Provider/API failures are labeled separately from semantic degradation.

## 6. Policies vs failure modes

These are **orthogonal**:

| Concept | What it is | Examples |
|---------|------------|----------|
| **Agent policy** | How the runner *behaves* on a requirement | `direct`, `static_smell`, `rewrite`, `clarify` |
| **Failure mode (FM)** | A *regression injection* used by `make simulate` to verify the gate | FM1–FM3 below |

Default offline happy path uses policy `direct` with stubs that respect clean constraints. Simulate injects FMs **on top of** (or instead of) correct stub behavior — same idea as sister harness regression simulation.

### Offline failure modes (Tier 1)

Mirror the three-mode pattern of the sister harness. Injection interface (Tier 1): CLI flag and/or env var on the simulate entrypoint, e.g. `make simulate MODE=smell-blind` / `AGENT_SIM_MODE=oracle-mismatch`, documented in README to match sister-harness ergonomics.

| ID | Mode | Injected behavior | Gate expectation |
|----|------|-------------------|------------------|
| FM1 | `smell-blind generation` | Stub “succeeds” syntactically under smell; semantic quality drops vs clean pair | Gate fails if degradation undetected |
| FM2 | `oracle-mismatch under ambiguity` | Vague threshold/order/cardinality (MesaFlow-style) yields plausible but wrong artifact | Gate fails on oracle miss, not only crashes |
| FM3 | `provenance-collapse` | Only operational proxies present/used | Gate fails if semantic provenance signals are missing or ignored |

## 7. Pilot substrate (Tier 1 task families)

1. **Code generation / repair** (primary) — MesaFlow RF-04, RF-07, RF-09, RF-13 seeds.
2. **Test / acceptance-criteria generation** (second) — **same MesaFlow intents**, different artifact type.

Optional later: automated traceability (Vogelsang-aligned generalization).

### Shared intent strategy (codegen + test_gen)

Both Tier 1 families reuse the **same four `intent_id`s**. What changes is `task_family` and the expected artifact:

| `task_family` | Artifact under test | Oracle style |
|---------------|---------------------|--------------|
| `codegen` | Implementation snippet / module behavior | Executable checks (format, sort key, threshold, cardinality) |
| `test_gen` | Generated tests or acceptance criteria for the same intent | Meta-oracle: generated tests must encode the *clean* constraint; fail if they assert a weakened/smelly interpretation |

Example for RF-09: clean codegen must treat delay as `T > 5` minutes; clean `test_gen` must produce a criterion/test that fails when `T ≤ 5` is accepted. A smell-blind stub that emits vague tests (“after significant time”) fails the meta-oracle.

This keeps the paired benchmark coherent (one intent grid × two task families) without inventing a second unrelated corpus in Tier 1.

### MesaFlow seed intents (pilot)

| ID | Clean intent (summary) | Smell risk | Candidate degradation |
|----|------------------------|------------|------------------------|
| RF-04 | Order ID `P-` + exactly 3 digits | Format ambiguity | Unconstrained / wrong ID shape |
| RF-07 | Cards oldest→newest by time | Ordering ambiguity | Sort by wrong key |
| RF-09 | New orders delayed after >5 min | Vague threshold | Wrong / missing T |
| RF-13 | Exactly 5 oldest active orders | Cardinality ambiguity | Arbitrary N |

## 8. Roadmap — clear path to full thesis (C1–C5)

Thesis contribution mapping used below:

| ID | Contribution |
|----|----------------|
| **C1** | Taxonomy: smell categories ↔ degradation modes |
| **C2** | Paired benchmark (`pairs/` + artifacts + labels + traces) |
| **C3** | Evaluation protocol (paired design, replications, reliability, workload characterization) |
| **C4** | Provenance-based observability baseline vs static/output/operational |
| **C5** | Mitigation baseline (rewrite / clarify) inside the protocol |

| Tier | Deliverable | Exit gate | Thesis map |
|------|-------------|-----------|------------|
| **0** | Repo skeleton, episode schema, `docs/interop.md`, 4 MesaFlow pairs × 2 families (schema-ready), empty overlay stubs | Benchmark seed exists | **C2** seed |
| **1** | Stub agents for codegen + test_gen on shared intents; FM1–FM3; `make simulate` / `make gate`; GitHub Actions offline | **Public repo DoD** | **C2** + minimal **C3** |
| **2** | Taxonomy overlay (**C1**); provenance vs static/output/operational baselines (**C4**); `make experiment` live | Effect gate + observability gate | C1, C4, H1–H4 |
| **3** | Mitigation overlay (**C5**); full protocol stats (**C3**); dissertation packaging | Mitigation gate; **dissertation DoD** | C3, C5, H5 |

### Decision gates (from thesis §13)

- **Taxonomy:** reliability &lt; 0.70 after refinement → merge categories or report instability.
- **Benchmark:** cannot independently label ≥2 task families → drop broad observability claims.
- **Effect:** clean/smelly Δ ≈ 0 for all families → report null under tested conditions.
- **Observability:** provenance ≤ operational/static baselines → limit to output evaluation + negative boundaries.
- **Mitigation:** rewrite/clarify no benefit or net-negative cost → report trade-off, do not market as always good.

## 9. Testing strategy (ATDD)

Caller-visible acceptance tests (public repo):

1. Happy-path offline gate passes without API keys.
2. FM1 injection fails the gate.
3. FM2 injection fails the gate.
4. FM3 injection fails the gate.
5. Full suite + CI workflow require no secrets.

Live experiments are out of default CI; covered by documented manual/optional workflow with recorded model IDs and dates.

## 10. Error handling and validity

- Stub path is deterministic and offline-first.
- Live path: bounded retries; record `model_id`, provider, date; do not conflate infra errors with semantic degradation.
- Synthetic smell injection rules must be explicit and reviewable; MesaFlow is a **seed**, not external validity proof.
- Workload identity modeled as random effect when estimating smell impact (analysis layer, Tier 2–3).

## 11. Stack defaults

- Python ≥3.11, package layout similar to sister harness.
- `pytest` for ATDD; optional live deps behind extras (e.g. `[live]`).
- YAML thresholds; JSONL provenance.
- Makefile targets: `test`, `simulate`, `gate`, `experiment` (live).

## 12. Open points deferred to implementation plan

- Exact directory package names (`agent_harness` vs flat modules).
- Oracle implementation details per MesaFlow RF (unit tests vs golden artifacts).
- Which live providers to support first (one is enough for Tier 2).
- Human annotation workflow tooling (can remain manual CSV/JSON until Tier 2).

## 13. Success criteria checklist

**Repo DoD (Tier 1):**

- [ ] Three failure modes documented in README with reproduce commands
- [ ] Offline CI green on happy path; red on each injected mode
- [ ] No secrets required for default CI

**Dissertation DoD (Tier 3):**

- [ ] Paired benchmark + provenance traces exportable
- [ ] Protocol documented with paired design and reliability targets
- [ ] Baselines compared (static smell / output / operational / provenance)
- [ ] Mitigation trade-off evaluated
- [ ] Negative boundaries reported when gates fire
