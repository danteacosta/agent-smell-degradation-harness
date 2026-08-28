# Requirements-smell experiment hardening

## Progress

- [x] Write and review the hardening specification.
- [x] Write and review the implementation plan.
- [x] Add a failing regression test for the `shall`/`all` completeness bug.
- [x] Fix the detector with word-bounded matching.
- [x] Normalize generated source and comparison diffs to LF with one final newline.
- [x] Add Wilson 95% intervals and interval-support status.
- [x] Deduplicate repeated behavior rows by intent, variant, and task family.
- [x] Validate replication IDs and report missing, duplicate, and unstable repetitions.
- [x] Record non-secret prompt and configuration identities.
- [x] Isolate discovery temporary traces per artifact bundle so reruns do not reuse stale files.
- [x] Run and verify `discovery-20260826-v7`.

## v7 verification checkpoint

Bundle: `artifacts/experiments/runs/discovery-20260826-v7/`

- Mode: offline deterministic stub (`stub-smell-blind`)
- Repetitions: 5 deterministic pipeline repeats; no independent-model claim
- Total decisions: 240
- Behavior decisions: 120
- `test_gen` decisions excluded from binary efficacy: 120
- Raw eligible behavior rows: 120
- Unique eligible behavior cases: 24
- Unique smelly/clean pairs: 12
- Recall: 0.9167; Wilson 95% interval [0.6461, 0.9851]
- Precision: 1.0000; Wilson 95% interval [0.7412, 1.0000]
- Specificity: 1.0000; Wilson 95% interval [0.7575, 1.0000]
- False-alert rate: 0.0000; Wilson 95% interval [0.0000, 0.2425]
- Paired discrimination: 0.9167; Wilson 95% interval [0.6461, 0.9851]
- Repetition stability: all five repetitions agree
- Interval support status: inconclusive because the unique-case sample is small

## Commands run

```text
.venv/bin/python -m pytest -q tests/test_discovery_verifier.py tests/test_discovery.py tests/test_live_agent.py tests/test_episode_identity.py tests/test_provider_run_manifest.py
.venv/bin/python -m eval.discovery --mode offline --replications 5 --run-id discovery-20260826-v7
.venv/bin/python -m eval.discovery --verify-artifacts --bundle-dir artifacts/experiments/runs/discovery-20260826-v7
```

The focused suite passed with 35 tests. The complete workstation suite was
also attempted; its remaining failures are environment-specific Python 3.14
sandbox/ARP compatibility issues, not failures of the hardened discovery
tests. The supported Python 3.11/3.12 CI gates remain the authoritative full
suite check.

## Remaining work for the real-model phase

- [x] Provide a provider-agnostic panel runner with secret-free configuration and smoke/full-run guards.
- [ ] Provide credentials through the approved secret mechanism.
- [ ] Select at least two real provider/model configurations and record prompt/config versions.
- [ ] Run independent repetitions with measured latency, cost, token/error rates, and Linux/CI sandboxing.
- [ ] Expand the corpus with reviewed natural variants, difficult clean cases, more projects/domains, and project-held-out splits.
- [ ] Run the intervention comparison: agent without verifier, with alert, and with alert plus revision opportunity.
- [ ] Define hidden-test pass rate, introduced defects, false alerts, review time, cost/tokens, clarification count, and post-alert correction rate.

## v8 natural source-label screening checkpoint

- [x] Add a strict private-corpus acquisition step for the ARTA workbook with source row/hash provenance.
- [x] Select 12 single-marker positives and 12 no-marker clean controls for each of six supported families.
- [x] Run the text-only frozen baseline on a project-disjoint split and record per-family test denominators and naive Wilson intervals.
- [x] Generate a controlled paraphrase probe excluded from primary metrics.
- [x] Record v7 no-alert/alert/revision-ceiling conditions as simulation-only.
- [x] Redact source requirement text from tracked v8 artifacts.
- [x] Add a contextual linguistic comparator alongside the fixed lexical lower bound.
- [x] Generate a redacted, per-case error audit with explicit expert-review status.
- [x] Catalog literature on linguistic patterns, embeddings, controlled language,
      context-sensitive ambiguity and hybrid AI/traditional QA.

Bundle: `artifacts/experiments/runs/discovery-20260826-v8-screening/`

- Status: `blocked_until_external_validation`
- Estimand: `agreement_with_arta_source_labels` (descriptive screening only)
- Cases: 144 across 6 projects; 12 positive and 12 clean controls per supported family
- Real models: 0/2; both slots remain `not_run`
- Expert annotation: pending; ARTA markers are not independent labels

The v8 run is executable only with a local private source because ARTA text
redistribution/derivative-use permission is not established. GitHub tracks the
selection hashes, code, split, metrics and redacted cases, not source excerpts.

The contextual comparator is still a diagnostic heuristic. It is not a
provider-backed semantic adjudicator and its agreement with ARTA markers is not
expert-validated evidence. See
`docs/research/2026-08-26-context-aware-requirements-smell-detection.md` and
the bundle's `error-analysis.json` for the proposed escalation from lexical
triage to contextual review and hidden behavioral validation.
