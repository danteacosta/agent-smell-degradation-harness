# Requirements-smell experiment hardening

## 2026-09-03 private pre-pilot gate execution

Plan:

- [x] Search the workspace and connected Google Drive for the 16 private candidates and reference-constraint input.
- [x] Audit the existing 12-pair/6-project material against `prepilot-corpus/v4` without promoting it.
- [x] Verify the immutable ARTA provenance and distinguish repository-code licensing from third-party dataset rights.
- [x] Receive or place the private candidate JSON/JSONL and reference-constraint files under an approved private path.
- [x] Run the v4 intake validator and retain only a redacted candidate manifest with 12 intents across 6 projects.
- [x] Freeze the validated manifest and run the private preflight; execute the exploratory pre-pilot only if it returns ready.

Verification checkpoint:

- Private intake produced 16 `prepilot-corpus/v4` candidate records and a frozen 12-record subset spanning 6 projects; raw source text remains outside the repository.
- The exact private input and the 12-record `prepilot-reference-constraints/v1` file are retained under `/private/tmp/prepilot-corpus-20260903/`.
- The v4 validator accepted the selected records against the redacted canonical manifest, including immutable source references, rights review, near-clone screening, manipulation checks, and hashes.
- The earlier exploratory run completed with 1,296 reconciled provider calls, 288 judged occurrences, and 4 uncertainty outcomes at a confirmed cost of US$0.187950, but its T1/T2 evidence was substantively vacuous; it is diagnostic only and does not support H1/H2.

## 2026-09-03 substantive-evidence correction

- [x] Add a fail-closed substantive-completeness gate for T1 and T2 before T4.
- [x] Require judge consensus on both the outcome label and per-constraint status.
- [x] Shorten T1/T2/artifact prompts and require explicit valid evidence types.
- [x] Recalculate the corrected exploratory budget envelope: US$0.988200 reserved under the US$1.00 cap.
- [x] Run the low-cost native smoke: 4/4 RF-04 episodes passed across OpenAI and DeepSeek.
- [x] Record the corrected prompt hash `60077136a90e5be355bda5f1049ab39b3152381b27344f8f8833a3a5ef6f3330`.
- [x] Record the corrected exploratory configuration hash `160423c8ef1beb6c343bc5f51ab5550f9e40f7aeda0aec7049c5cabc27b2e150`.
- [x] Compact the T2 planning context after observed provider usage exceeded the frozen input/output bound; record prompt hash `85859c0a8ff5f7ab784bab4e4188aa1de7ec4bd84f3e0547927e266c569e2326` and configuration hash `fecd185cd77c0ac12b6372a3ae301fd531e112e1497cf417ec5a86ca12eeafb0`.
- [ ] Run and review one corrected 120-episode exploratory report after fresh authorization for the external run.
- [ ] Promote no `clean`/`uncertain` count to H1/H2 until substantive completeness and independent label conditions are verified.

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
- [x] Add staged panel execution metadata (`prepilot`, `pilot`, `full_panel`), exact task-count gates, explicit model snapshots, strict unknown-field validation, and atomic idempotent resume.
- [x] Add automatic measured-cost budget stopping with fail-closed behavior when usage cannot be measured.
- [x] Preserve panel agreement, model disagreement, and separate human/model disagreement metrics without using panel consensus as ground truth.
- [x] Add a private four-stratum control-matrix contract: clear clean, surface-only, real defect, and lexically discreet defect.
- [x] Add the versioned context-management contract, no-compaction primary condition, secondary stress matrix, and leakage-safe metrics.
- [x] Add the article-informed typed hard-lane proxy as a non-confirmatory secondary mechanism.
- [x] Add hash-bound atomic-obligation observations without raw obligation text or terminal evidence.
- [x] Add the complete clean/smelly × no-compaction/compaction interaction estimator.
- [ ] Provide credentials through the approved secret mechanism.
- [ ] Select at least two real provider/model configurations and record prompt/config versions.
- [ ] Qualify the real runtime context-management hook and verify pre-final event emission on both provider configurations.
- [ ] Run the separate clean/smelly × no-compaction/compaction-stress interaction check; keep it outside the 120-episode primary count.
- [ ] Qualify the typed hard-lane proxy against the same budget and provider configuration as the uniform stress cell; report it as a mechanism ablation.
- [ ] Run independent repetitions with measured latency, cost, token/error rates, and Linux/CI sandboxing.
- [ ] Expand the corpus with reviewed natural variants, difficult clean cases, more projects/domains, and project-held-out splits.
- [ ] Run the intervention comparison: agent without verifier, with alert, and with alert plus revision opportunity.
- [ ] Define hidden-test pass rate, introduced defects, false alerts, review time, cost/tokens, clarification count, and post-alert correction rate.

## 2026-08-27 staged panel hardening checkpoint

- Runtime configuration is now strict: unknown fields and fractional task counts fail closed.
- `prepilot` permits one judge and remains a 120-episode path-validation design; `pilot` and `full_panel` require explicit model snapshots.
- `full_panel` requires expected per-judge and total task counts, and the CLI requires `--full-run --confirm-full-run`.
- The example full-panel configuration intentionally leaves pricing and snapshot values to the private operator configuration; no provider or model is hardcoded.
- The four condition names are metadata only. A full run with `require_negative_controls=true` requires a private, balanced matrix and refuses incomplete conditions before any adapter call.
- Panel disagreement is descriptive triage/robustness evidence. Human adjudication remains a separate source of labels.

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


## 2026-09-01 pre-pilot unlock checkpoint

- [x] Merge the context-management/atomic-obligation implementation into \`main\`.
- [x] Add measured OpenAI-compatible adapters for OpenAI and DeepSeek.
- [x] Propagate per-stage usage, cost status, response identity, and configuration
      identity without exporting credentials or raw prompts.
- [x] Add the two-slot native-provider smoke and fail-closed primary
      \`no_compaction\` checks.
- [x] Add private corpus intake that emits a hash-only, rights-aware manifest.
- [x] Add outcome-blinded annotation packets with deterministic pre-label 20%
      duplicate selection.
- [x] Add an advisor approval memo with explicit budget, ethics, corpus, and
      adjudication decisions.
- [ ] Run the real-provider smoke in the private environment with both keys,
      immutable model versions, and frozen prices.
- [ ] Resolve at least 12 licensed, independently auditable intents across at
      least 6 projects; the current checked-in count is 7/12.
- [ ] Name two annotators and an independent adjudicator; complete rehearsal,
      missing-label export, alpha, and bootstrap interval.
- [ ] Obtain advisor/institution approval and record the provider and
      annotation-hour caps.
