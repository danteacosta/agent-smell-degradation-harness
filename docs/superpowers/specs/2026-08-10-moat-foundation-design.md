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

The exact fixture entry point is:

```text
python -m replay --fixture clean --json out/report.json --sarif out/report.sarif
```

Arbitrary bundles use the same contract through:

```text
python -m replay --bundle path/to/bundle --json out/report.json --sarif out/report.sarif
```

`--fixture NAME` resolves only the checked-in synthetic fixture. `--bundle DIR`
requires `manifest.json`, `requirement.json`, and the trace named by the
manifest; an optional `expected.json` is test-only and is never read by the
gate.

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
replay/fixtures/requirement.json    # requirement text and task family
replay/fixtures/traces/*.jsonl      # only T1/T2/T3 ARP events
replay/fixtures/expected.json       # test-only expected decisions/evidence
```

The manifest includes `checkpoint_schema_version: "pre-final/v1"` alongside
`replay_version: "constraint-replay/v1"` and the ARP wire/package versions.

Each trace must contain exactly one ordered T1/T2/T3 event. The canonical event
names and payloads are frozen as follows:

| rank (canonical `checkpoint` value) | `event_type` | required `attributes` |
| --- | --- | --- |
| T1 | `interpretation.completed` | `constraints`, `unresolved_references`, `assumptions`, `contradictions` (arrays of strings), `quantities` (array of `{value, unit}` objects) |
| T2 | `plan.completed` | `validation_checks`, `planned_tools`, `coverage_targets` (arrays of strings) |
| T3 | `tool.completed` | `revisions`, `validation_attempts`, `retrieval_events` (non-negative integer), `errors` (array of strings) |

Every event also has `event_id` (non-empty string), `sequence_number` (1, 2,
3), `checkpoint` equal to its canonical event name, `event_type`, `schema_version`
(`2.0.5`, the ARP wire SemVer), and `attributes`; terminal/oracle/final-artifact
keys are forbidden. The surrounding ARP envelope also requires
`experiment_id`, `run_id`, `episode_id`, `replication_id`, `started_at`,
`ended_at`, `content_reference`, and `parent_event_id`, with one shared
experiment/run/episode, replication `0`, chronological timestamps, and parent
IDs pointing to the preceding event (or `null` for T1). The checkpoint payload
schema is separately frozen as `pre-final/v1` in the manifest and validator;
it is not used as the ARP event `schema_version`. The manifest hashes raw trace
bytes with SHA-256. Replay and ARP versions are checked before feature
extraction. The expected sidecar is never loaded by the gate and may contain
mutation labels only for tests. Retrospective output-only values live under a
namespaced, non-deployable diagnostic sidecar.

The benchmark has five fixed cases: clean (`approve`), controlled constraint
loss (`block`), a valid weak signal (`warn`), negative-control loss in a
non-relevant field (`approve`), and operational-only latency change (`approve`).
The false-alert invariant is zero false alerts over the two negative cases (2
total). It reports output-only and operational baselines, false alerts, and
fixture-ID-independent results. All fixtures are explicitly non-confirmatory
thesis evidence.

Report hashes are SHA-256 over UTF-8 JSON with sorted keys, compact separators,
normalized finite numbers (`-0` becomes `0`), and no trailing newline.
`report_sha256`, paths, timestamps, environment values, and non-deployable
diagnostics are excluded from the hashed projection, so the hash is
non-circular and portable.

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
- The GitHub Action does not require API keys. It requests `security-events:
  write` only for SARIF upload when available and always uploads JSON/SARIF as
  ordinary artifacts, so fork pull requests remain reviewable without secrets.
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
5. Changing expected sidecar labels, mutation metadata, diagnostic output-only
   values, and fixture IDs leaves deployable features/baselines and the
   decision unchanged; only non-deployable case metadata may differ.
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
