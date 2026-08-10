# Moat foundation design

**Status:** approved scope after user review

## Goal

Turn the three-repository prototype into a credible pre-data/pre-customer
foundation: legally reusable, reproducible from a public replay bundle, and
able to demonstrate constraint-loss detection through a standard CI artifact.

## Scope

This first implementation cycle covers the smallest end-to-end proof:

1. Apache-2.0 licensing and release hygiene for ASD, RAG, and ARP.
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
- emit a deterministic decision and SARIF properties;
- return a non-zero exit code for `warn`/`block` and zero for `approve`;
- include a replay/benchmark version and provenance hash in the report.

The benchmark must include at least one clean case, one controlled
constraint-loss case, one generic output-only baseline, and one operational
baseline. It must state that fixtures are not confirmatory thesis evidence.

## Data flow

```text
replay fixture -> ARP/pre-final trace validator -> deployable feature extractor
               -> baseline comparison -> product gate -> JSON + SARIF
```

The replay bundle is synthetic/public and contains no private customer data.
It is a demonstration artifact, not a substitute for the confirmatory dataset.

## Failure behavior

- Missing or malformed checkpoints fail closed with a machine-readable error.
- Trace hash or replay version mismatch fails closed.
- Malformed semantic evidence is dropped from SARIF rather than crashing the
  report; an empty evidence list remains explicit.
- Terminal labels, oracle verdicts, and final artifacts are rejected from the
  deployable feature path.
- The GitHub Action does not require API keys.

## Acceptance tests

1. A clean clone can install and run the replay command without credentials.
2. The clean fixture emits `approve`; the controlled loss fixture emits
   `warn` or `block` with constraint, checkpoint, confidence, and action.
3. Replaying the same bundle twice yields the same report hash.
4. Mutating the trace, checkpoint schema, or replay version fails closed.
5. The action uploads valid SARIF and uses stable exit codes.
6. All three repositories have an explicit open-source license and linked
   contribution/security guidance before a release is tagged.

## Non-goals

- No claim of statistical generalization.
- No customer data ingestion.
- No dashboard or hosted service.
- No automatic durable memory or RAG expansion.
- No vendor SDK dependency until the replay contract is stable.
