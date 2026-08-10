# Moat foundation design

**Status:** approved scope after user review; contract tightened by spec review

## Goal

Turn the three-repository prototype into a credible pre-data/pre-customer
foundation: legally reusable, reproducible from a public replay bundle, and
able to demonstrate constraint-loss detection through a standard CI artifact.

## Scope

This first implementation cycle covers the smallest end-to-end proof:

1. Explicit licensing and release hygiene for ASD, RAG, and ARP (`main`):
   Apache-2.0 for the two harnesses, preserving ARP's already-published MIT
   license at immutable v2.0.6, with `LICENSE`, `NOTICE`, `CONTRIBUTING.md`,
   and `SECURITY.md` in each repository.
2. A versioned ASD replay bundle containing requirements, typed pre-final
   traces, expected constraint evidence, and a deterministic report.
3. A benchmark runner with controlled semantic mutations and generic baselines
   so the README can show a reproducible comparison without claiming external
   validity.
4. A GitHub Action/CLI path that emits approve/warn/block JSON and SARIF from a
   replay trace.
5. Cross-links and a ten-minute quickstart that make the differentiation
   explicit: the stack consumes observability traces and adds constraint-level
   preservation evidence.

Adapters for OTLP/OpenInference vendors are a follow-up cycle. This cycle
defines the boundary they must implement rather than adding vendor-specific
SDK dependencies.

## Contract

Given a requirement and a pre-final trace, the public replay command must:

- validate the typed T1/T2/T3 checkpoint envelope;
- compute constraint-level evidence without reading terminal labels or final
  artifacts;
- emit a `constraint-replay/v1` JSON report and SARIF 2.1.0 properties;
- return `0` for `approve`, `10` for `warn`, `20` for `block`, and `30` for
  invalid contracts;
- include a replay version, ARP wire schema (`2.0.5`), ARP package version
  (`2.0.6`), trace hash, and report hash in the report.

The exact entry point is:

```text
python -m replay --fixture clean --json out/report.json --sarif out/report.sarif
```

The clean fixture deterministically maps to `approve`; the controlled
constraint-loss fixture deterministically maps to `block`. `warn` is reserved
for a valid but below-threshold signal in the benchmark and must never be
silently substituted for invalid input.

The JSON report contains `schema_version`, `replay_version`, `decision`,
`exit_code`, `trace_sha256`, `report_sha256`, `features`, `baselines`, and
`semantic_evidence`. Each evidence item has `constraint`, `checkpoint`,
`confidence` in `[0,1]`, and `recommended_action` from `review|clarify|block`.

The bundle layout is fixed:

```text
replay/fixtures/manifest.json       # deployable case IDs, versions, trace hashes
replay/fixtures/traces/*.jsonl      # only T1/T2/T3 ARP events
replay/fixtures/expected.json       # test-only expected decisions/evidence
```

Each trace must contain exactly one ordered T1 interpretation, T2 plan, and
T3 tool/execution checkpoint with an allowlisted `attributes` payload. The
manifest hashes raw trace bytes with SHA-256. Replay and ARP versions are
checked before feature extraction. The expected sidecar is never loaded by
the gate and may contain mutation labels only for tests.

The benchmark has at least four fixed cases: clean, controlled constraint
loss, negative-control loss in a non-relevant field, and an operational-only
latency change. It reports output-only and operational baselines, false alerts,
and fixture-ID-independent results. All fixtures are explicitly non-
confirmatory thesis evidence.

## Data flow

```text
replay fixture -> ARP/pre-final trace validator -> deployable feature extractor
               -> baseline comparison -> product gate -> JSON + SARIF
```

The replay bundle is synthetic/public and contains no private customer data.
It is a demonstration artifact, not a substitute for the confirmatory dataset.

## Failure behavior

- Missing or malformed checkpoints fail closed with a machine-readable
  `invalid-contract` report and exit code `30`.
- Trace hash or replay version mismatch fails closed.
- Malformed provider evidence fails closed; only untrusted optional SARIF
  extensions are filtered before serialization, never used for the decision.
- Terminal labels, oracle verdicts, and final artifacts are rejected from the
  deployable feature path.
- The GitHub Action does not require API keys.
- Changing expected labels or mutation metadata cannot change a gate decision.

## Acceptance tests

1. Python 3.11+ can install with the declared package commands (network may be
   used once for dependencies) and then run the replay command offline, without
   provider credentials, in under ten minutes on a clean checkout.
2. The clean fixture emits `approve`; the controlled loss fixture emits
   `block` with constraint, checkpoint, confidence, and action.
3. Replaying the same bundle twice yields the same canonical report hash.
4. Mutating trace bytes, checkpoint order/schema, replay version, or ARP
   compatibility fails closed with exit code `30`.
5. Changing expected sidecar labels and fixture IDs leaves the deployable
   decision unchanged.
6. The action uploads valid SARIF with `if: always()` and stable exit codes;
   forked pull requests require no secrets.
7. All three `main` branches have explicit licenses (Apache-2.0 for the
   harnesses, MIT for ARP v2.0.6), `NOTICE`, contribution/security guidance,
   dependency/fixture attribution, and release links before tagging.

## Non-goals

- No claim of statistical generalization.
- No customer data ingestion.
- No dashboard or hosted service.
- No automatic durable memory or RAG expansion.
- No vendor SDK dependency until the replay contract is stable.
- No claim that public fixture performance estimates thesis effect sizes.
