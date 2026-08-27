# Agent Smell Degradation Harness

**Product wedge:** a reliability layer / CI check for coding agents — given a spec and agent run, emit **approve / warn / block** before intent loss reaches production. The product surface is deliberately separate from the confirmatory thesis protocol.

**Research questions:** RQ1 measures degradation induced by defective requirements; RQ2 tests whether pre-final, oracle-free observability improves deployable warning. RQ3 evaluates clarification only when that optional extension is enabled.

Design for this wedge: [wedge-first reliability check spec](docs/superpowers/specs/2026-07-22-wedge-first-reliability-check-design.md)

Offline twin of [`rag-reliability-harness`](https://github.com/danteacosta/rag-reliability-harness) for measuring requirement-smell-induced semantic degradation in LLM agent episodes.

Evaluation task coverage is configured through domain adapters: acceptance-criteria generation is the primary task, traceability is a completed-episode validator, and code generation remains an optional adapter. The default configuration preserves the existing `codegen` and `test_gen` benchmark coverage.

[![eval-gate](.github/workflows/eval.yml/badge.svg)](.github/workflows/eval.yml)

## Wedge check (local / CI)

```bash
python -m wedge --fixture demo-clean     # approve
python -m wedge --fixture demo-smelly    # clarify (smell + direct policy)
python -m wedge --fixture demo-degraded  # warn (terminal-label regression)
make wedge-check
```

Consumer wiring guide: [docs/wedge.md](docs/wedge.md)

## Constraint replay gate (pre-merge)

The canonical pre-merge path is the offline replay gate. It consumes an ARP
2.0.5 legacy replay trace (read through the ARP 3.0 compatibility surface) and adds constraint-level preservation
evidence; it does not replace tracing systems such as OpenTelemetry, Phoenix,
or Langfuse. The checked-in fixtures are synthetic and non-confirmatory.

```bash
python -m replay --fixture clean --json out/report.json --sarif out/report.sarif
# arbitrary public bundle:
python -m replay --bundle path/to/bundle --json out/report.json --sarif out/report.sarif
```

The command runs without provider credentials after one dependency install and
returns `0/10/20/30` for approve/warn/block/invalid-contract. JSON and SARIF
are deterministic, and the GitHub Action uploads both as artifacts so fork
pull requests remain reviewable. See the [ARP contract](https://github.com/danteacosta/agent-reliability-protocol),
the sister [RAG reliability harness](https://github.com/danteacosta/rag-reliability-harness),
and [the thesis/product boundary](docs/thesis-product-boundary.md).

The demo workflow keeps Code Scanning upload disabled because its synthetic
block is intentionally an alert. A real installation can set the repository
variable `REPLAY_UPLOAD_SARIF=true` after replacing the fixtures with its own
policy-approved bundle; fork pull requests continue using the artifact
fallback.

## Confirmatory trace boundary

Confirmatory collection emits native ARP 3.0 records under
`agent-smell-degradation/v1`. It accepts only a single instrumented runtime
execution that returns T1 interpretation, T2 plan, T3 execution checkpoints,
and the resulting artifact together. Prompted checkpoint summaries, stubs,
mocks, and replay remain non-confirmatory. T4 artifact/evaluation data is
stored only in the label-plane profile extension and is excluded by the
deployable feature loader.

## Flow

```mermaid
flowchart LR
  pairs["pairs (clean | smelly)"]
  agent["provider adapter (stub/replay/live)"]
  prov["provenance JSONL"]
  oracle["oracles / validators"]
  eval["eval metrics (paired Δ)"]
  gate["gates (CI thresholds)"]
  wedge["wedge check (approve|warn|clarify)"]

  pairs --> agent --> prov --> oracle --> eval --> gate
  prov --> wedge
  oracle --> eval
```

## Failure modes

| Mode | What breaks | Reproduce |
|------|-------------|-----------|
| **smell-blind** (FM1) | Agent ignores smell signals; paired degradation rises | `python -m eval.simulate_regressions --mode smell-blind` |
| **oracle-mismatch** (FM2) | Validators disagree with semantic oracle | `python -m eval.simulate_regressions --mode oracle-mismatch` |
| **provenance-collapse** (FM3) | Semantic provenance skipped; observability blind spot | `python -m eval.simulate_regressions --mode provenance-collapse` |

Each mode is injectable for ATDD: pre-harness baseline catch rate 0.0 → post-harness 1.0.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -c constraints.txt -e ".[dev]"
make all
```

The Make targets use the active project interpreter. In automation, the
equivalent explicit form is `PYTHON=.venv/bin/python make all`; no globally
installed `pytest` executable is required.

After dependencies are acquired and cached (or supplied in `./wheelhouse`),
replay can execute offline with `pip install --no-index --find-links
./wheelhouse -c constraints.txt -e .`. The constraints pin the ARP release and
test/runtime packages; because ARP is a direct VCS dependency, a clean machine
still needs a one-time acquisition/build step before offline installation.

`make all` runs `test` → `eval` → `simulate` → `gate` in order (see [interop contracts](docs/interop.md)).

Optional: pass a single failure mode to simulate:

```bash
make simulate MODE=smell-blind
```

## Data note

Requirement pairs are seeded from **MesaFlow** as a local, curated starting set. MesaFlow is a development seed — not a peer-reviewed claim of external validity for thesis or production use.

## V4 scientific contract

Acceptance-criteria generation is the primary workload; traceability is an external completed-episode validation; code generation is optional. The feature plane consumes only pre-final evidence, while the independent label plane owns terminal evaluation. The principal scientific output is an observability boundary map across workload, defect family, checkpoint, model and deployment metrics—not a new requirement-smell taxonomy.

The reproducible pre-pilot uses 12 intents × clean/smelly variants × 5 replications and writes manifests, episodes, events, artifacts, labels, features and analysis. Run it with `make prepilot`.

Before spending provider or annotation budget, run `python -m eval.prepilot_readiness`. The fail-closed [pre-pilot launch pack](docs/research/prepilot-launch-pack.md) binds the 120-episode design to two qualified runtime-native provider/model configurations, a licensed and manipulation-checked corpus, blinded double annotation, leakage and reproducibility gates, advisor authorization, and an approved cost envelope. The checked-in candidate intentionally returns `no_go`; passing this gate authorizes only the non-confirmatory pre-pilot.

The license-first [pre-pilot corpus screening](docs/research/prepilot-corpus-screening.md) records admitted, conditional, secondary, and rejected source families. In particular, public availability is not treated as redistribution or derivative-use permission, and project diversity cannot be manufactured from documents, modules, or paraphrases.

The acceptance boundary, estimands, leakage rules, split invariants, and product policy are documented in [Thesis and Product Boundary](docs/thesis-product-boundary.md). Confirmatory H2 uses an `h2-features/v3` raw-feature manifest, recomputes its contents from hash-bound T1/T2/T3 traces, fits fixed nested B0–B3 models with one estimator, calibrates only on calibration, and evaluates B3−B0 once on test. No family is selected by training PR-AUC. A pre-pilot manifest must contain 12 independent source intents; 24 intents/6 projects is a pilot floor, while confirmation requires a frozen split-aware precision plan, at least 60 intents/12 projects as an unconditional floor, and at least 6 projects/24 intents in the untouched test partition. The current conservative design candidate is 220 intents/36 projects and remains explicitly unfrozen.

The current orientation and related-work review is versioned in [2026-08-10 orientation review](docs/research/2026-08-10-orientation-review.md). It records the novelty boundary, EASY alignment, direct comparison with prefix monitors, and the evidence still required before a confirmatory claim.

The master's scope, academic contribution, non-claims, and chapter boundary are
frozen in [Master's Thesis Scope](docs/thesis/masters-scope.md). H1/H2 remain
planned conditional claims until the external data, provider, annotation,
preregistration, and shadow-pilot gates pass.

## Requirements-smell discovery

The discovery track makes the advisor's clean-versus-smelly comparison
executable. It uses 12 source-traceable ARTA requirements from six projects,
creates a controlled pair for each one, generates acceptance criteria and a
small side-effect-free Python function, then runs hidden tests that exercise
the removed condition. The offline run needs no provider credential:

```bash
make discovery
make discovery-verify
make discovery-efficacy
```

The compact, reviewable bundle is stored under
`artifacts/experiments/runs/<run-id>/`. It includes generated clean/smelly
code, hidden-test reports, source diffs, metrics, episode records and corpus
provenance. This is discovery evidence only; live-provider, licensing,
blinded-label and preregistration gates remain separate.

The second phase evaluates the verifier itself. It reads only the portable
`observable-traces/` prefix (T0--T3) and produces `verification/decisions.jsonl`
before joining the post-artifact behavior labels. Its report measures recall,
precision/F1, clean false-alert rate, clean-versus-smelly paired
discrimination, first-signal checkpoint/lead time, runtime/provider cost and
project/smell strata. A `descriptive_only` status means that the frozen
discovery rule pack produced an auditable controlled result; its point
estimates are development diagnostics, not evidence of effectiveness on new
requirements or a universal efficiency claim.
Terminal timestamps used for lead time are materialized separately in
`evaluation-metadata.jsonl` and joined only after the verifier decision. This
keeps timing portable without allowing terminal evaluation data into the
oracle-free observable projection; bundles without the sidecar report lead
time as unavailable.

The original hardened v7 rerun uses five repetitions of the deterministic offline stub.
This produces 240 total decisions: 120 `test_gen` decisions that are
observability-only and 120 raw `behavior_codegen` rows. The primary efficacy
matrix deduplicates those repetitions by `(intent_id, variant, task_family)`,
leaving 24 unique behavior cases. Wilson 95% intervals are reported on those
unique cases (and on the 12 complete clean/smelly pairs); repeated stub rows
are a pipeline-stability check, not independent model evidence. The v7 run is
therefore useful for validating the detector and artifact pipeline, but it does
not establish LLM generalization, production latency/cost, or population-level
precision.

The v10 portability rerun keeps the same frozen corpus, rule pack and
descriptive-only estimand. Its purpose was to remove the machine-specific
provenance-path dependency from terminal timing, not to improve the detector.
The verified bundle is
`artifacts/experiments/runs/discovery-20260827-v10-portable-timestamps/`.
It has five deterministic pipeline repetitions, 240 decisions, 24 unique
behavior cases, and the same `TP=11, FN=1, FP=0, TN=12` matrix. The local
lead-time observation is now portable (`12` observations; mean `0.078 ms`),
but it measures the deterministic offline fixture and must not be presented as
LLM or production latency. The earlier v9 bundle is an intermediate local
diagnostic and is not a published result.

The v8 screening also contains a deliberate detector comparison. The frozen
`natural-lexicon/v1` baseline is a lower bound: it only asks whether a small
fixed vocabulary occurs. The `contextual-linguistic/v1` comparator adds broader
linguistic cues and explainable structure signals for quantities, conditions,
actors, responses and possible pronoun antecedents. Its source-label results
are diagnostic only, but the comparison demonstrates the intended design: the
detector should produce evidence and a review question, not silently convert a
word hit into a semantic verdict. The redacted per-case audit is stored in
`error-analysis.json`; semantic error categories remain pending independent
expert review.

This is consistent with the literature: Smella treats smell detection as a
lightweight supplement to reviews, Paska combines NLP with controlled-language
patterns and recommendations, and recent work on embeddings/LLMs still warns
about label quality, overfitting, domain shift and inconsistent evaluation.
The next detector phase must therefore compare lexical triage, contextual
linguistic features and provider-backed semantic adjudication on new,
project-held-out requirements, then measure whether alerts improve hidden-test
behavior through revision and code generation.

The v8 contextual comparator was assembled retrospectively while investigating
the lexical failures. Its metrics are diagnostic pipeline evidence, not a
blind superiority comparison; the next run must freeze the detector using only
training/calibration projects before evaluating held-out projects.

One detector regression was fixed before v7: the completeness rule now uses
word boundaries, so `all` inside `shall` cannot suppress the
`incomplete_completeness_scope` signal. The ERTMS omission case can still be a
genuine false negative when the omitted supervision scope is absent from the
final requirement text. On macOS, behavior reports use `trusted_fixture`,
which executes checked-in reference functions in the parent process with
restricted builtins; it is not a production subprocess sandbox. Real-model
evaluation remains a separate run requiring two provider/model configurations,
independent repetitions, measured cost/latency/error rates, and Linux/CI
sandbox execution.

The current collection blocker and acceptance checklist are documented in [confirmatory data acquisition](docs/research/confirmatory-data-acquisition.md). The checked-in seven-source seed is development-only. `RuntimeCheckpointAgent.from_provider()` supplies a staged OpenAI/Anthropic-compatible producer whose bounded T1/T2/T3 events precede terminal generation; empirical qualification on two real configurations is still required. `LiveAgent.observe_checkpoints()` remains a nonconfirmatory prompted snapshot, and offline replay remains schema validation rather than thesis evidence.

The append-only version ledger for this research track is [requirements-smell experiment history](docs/research/requirements-smell-experiment-history.md). It records the exact bundle, code milestone, result, interpretation and reason for each change, including invalid or superseded runs. It also defines the local/remote synchronization check used before publication.

The scientific and commercial moat audit is recorded in [2026-08-10 moat stress test](docs/research/2026-08-10-moat-stress-test.md). Its conclusion is intentionally conservative: the stack is protocol-ready with a promising wedge, but the moat is not demonstrated until external data, independent labels, provider diversity, adoption, and ROI evidence exist.

The executable customer-validation sequence and metric schema are in the
[product pilot protocol](docs/product-pilot.md). It starts in shadow mode and
does not treat synthetic replay outcomes as customer evidence.

## Offline overlays

Offline overlays add deployable baselines, analysis reports, and an optional live experiment path without changing the core CI gate.

| Command | Purpose |
|---------|---------|
| `make analysis` | Run happy + smell-blind evals; write `eval/analysis_report.json` with effect/observability flags |
| `make experiment` | Live experiment entrypoint (refuses without credentials; use `--stub-as-live` for offline schema demo) |
| `pip install -e ".[live]"` | Optional OpenAI adapter (`agents/live.py`); raises `NotConfiguredError` without API key |

Analysis and experiment exports are gitignored; `make gate` still reads only `eval/last_run.json` from `make eval`.

## Optional clarification extension

Clarification and rewrite experiments are optional extensions. They do not block the pre-pilot, pilot, defense, or the core CI pipeline; when enabled, their effect is reported as conditional E3 rather than a mandatory thesis claim. The RQ3-admissible policies (`structured_rewrite` and `targeted_clarification`) use only the received requirement plus an independently supplied clarification answer. Development-only oracle upper bounds are reported separately and can never support RQ3.

| Command | Purpose |
|---------|---------|
| `make extension-clarification` | Compare `direct`, two oracle-free RQ3 policies, and two explicitly excluded oracle upper bounds; write `eval/mitigation_report.json` |
| `make extension-dissertation` | Build the optional extension report bundle |

The default runner, pre-pilot and CI use `direct`; clarification experiments opt in explicitly through the extension commands. Independently sourced answers can be passed to `run_eval(..., clarification_answers={intent_id: answer})`. Legacy names `rewrite` and `clarify` fail closed because they do not state whether oracle access is allowed. The trade-off report is conditional E3, not an unconditional mitigation claim. Export guide: [docs/dissertation/README.md](docs/dissertation/README.md).

## Pre-experiment tooling

Offline preflight before live LLM runs (secret-free; default CI unchanged):

| Command | Purpose |
|---------|---------|
| `make dry-run` | Write `runs/<run_id>/manifest.json` and `prompts/*.txt` with no API calls |
| `python -m eval.experiment --mock-live` | Exercise `LiveAgent` + `MockTransport` under `runs/` |
| `python -m eval.thesis_analysis --episodes PATH` | H1 paired-degradation tables and negative-boundary flags |
| `make thesis-analysis` | Analyze `eval/last_run_episodes.jsonl` after `make eval` |
| `python -m eval.h2_detection` | Group-split detector comparison for deployable pre-final signals |

Pair loading validates schema; oracle scoring is tolerant of extra artifact keys. IRR utilities live in `protocol/irr.py` with annotation templates under `data/annotation/`.

## Design & sister harness

- Full design spec: [docs/superpowers/specs/2026-07-20-agent-smell-degradation-harness-design.md](docs/superpowers/specs/2026-07-20-agent-smell-degradation-harness-design.md)
- Wedge-first strategy: [docs/superpowers/specs/2026-07-22-wedge-first-reliability-check-design.md](docs/superpowers/specs/2026-07-22-wedge-first-reliability-check-design.md)
- Sister narrative and shared contracts (no shared code): [docs/interop.md](docs/interop.md) — parallel layout with `rag-reliability-harness` (`eval/`, `gates/`, `observability/`, threshold-driven gates, injectable failure modes, offline-first CI).
