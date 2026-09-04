# Pre-pilot Gate Audit — Design

**Date:** 2026-09-02
**Status:** Ready for human review
**Goal:** Provide one offline, redacted audit command that explains which
pre-pilot prerequisites are present, missing, or blocked without changing the
launch plan, admitting corpus records, or calling an external provider.

## Context and boundary

`main` already has separate contracts for private corpus intake, native
provider smoke, blinded annotation preparation, and the fail-closed launch
readiness decision. Operators currently need to reconcile several commands and
private artifacts manually. This audit is a read-only aggregator; those
existing commands remain authoritative.

The audit must never read or print raw requirements, labels, prompts,
responses, credentials, or terminal artifacts; infer human/legal decisions;
mutate a plan or manifest; make network/provider requests; or promote a
candidate manifest to an admitted one. A raw private corpus remains input to
the separate intake command, never to this audit.

## Chosen approach

Three options were considered:

1. Documentation-only: smallest, but leaves manual reconciliation.
2. Extend `eval.prepilot_readiness`: centralizes more code, but couples
   decision policy to filesystem discovery.
3. A separate audit aggregator: preserves the existing policy owner while
   giving operators one structured status report.

Option 3 is the selected design because it reduces command/evidence coupling
without introducing multiple algorithms or changing scientific gates. No
Strategy pattern is needed; there is one audit policy.

## Canonical API and inputs

Create `eval/prepilot_gate_audit.py` with one public function:

```text
audit_pre_pilot_gate(
    repository_root,
    launch_plan_path=None,
    candidate_manifest_path=None,
    frozen_manifest_path=None,
    smoke_config_path=None,
    smoke_report_path=None,
    annotation_selection_path=None,
    approval_record_path=None,
    reproducibility_manifest_path=None,
) -> dict
```

Create `scripts/audit_prepilot_gate.py` exposing exactly the same inputs as
`--repository`, `--launch-plan`, `--candidate-manifest`, `--frozen-manifest`,
`--smoke-config`, `--smoke-report`, `--annotation-selection`,
`--approval-record`, `--reproducibility-manifest`, and `--output`.

`repository_root` is required by the API and defaults to the repository root
in the CLI. `launch_plan_path` defaults to
`data/prepilot/launch-plan.candidate.json`, `frozen_manifest_path` defaults to
`data/prepilot/corpus-manifest.json`, and `smoke_config_path` defaults to
`tasks/native_provider_smoke.example.json`. All other paths are optional; an
omitted or nonexistent optional path is a `missing` result, not an exception.
Relative paths resolve against `repository_root`. Repository artifact paths
must stay inside that root. Private evidence may be outside it, but reports
use stable labels rather than absolute paths. `--output`, when supplied, must
be outside the repository.

There is deliberately no runtime-config or environment-marker input.
Credential presence is not a readiness fact and must not be inspected by this
command.

## Fixed gate matrix

The nine rows below, in this order, are the complete gate set. All nine must
be `pass` for the overall decision to be `go`.

| ID | Input/source | `pass` criterion | Otherwise |
| --- | --- | --- | --- |
| `launch_plan` | Launch plan + `evaluate_launch_plan` | Valid plan and evaluator decision is `go` | Missing file: `missing`; evaluator blockers: `blocked` |
| `corpus_candidate` | Optional candidate `prepilot-corpus/v3` metadata | Valid redacted metadata with at least 16 records across at least 6 projects and `selection_audit.outcome_blind=true` | Missing: `missing`; malformed: `blocked` |
| `corpus_frozen` | Frozen `prepilot-corpus/v3` metadata | `status=frozen`, exactly 12 unique records, at least 6 projects, required hashes/rights/manipulation booleans, and `raw_text_exported=false` | Missing: `missing`; candidate/incomplete: `blocked` |
| `provider_smoke_config` | Secret-free `native-provider-smoke/v1` config | Existing config passes `load_smoke_config`, has exactly two slots, and kinds are exactly `openai` and `deepseek` | Missing: `missing`; invalid/secret-bearing: `blocked` |
| `provider_qualification` | Private `native-provider-smoke/v1` report | `status=pass`, `provider_count=2`, `budget_ready=true`, valid configuration hash, matching config-template hash, and both provider rows pass with measured cost | Missing: `missing`; smoke-only/failure: `blocked` |
| `annotation_packet` | Optional `annotation-selection/v1` metadata | Selection method is `seeded_item_id_sampling_before_labels`, item count and duplicate count are positive, fraction is `0.2`, hash is valid, and no label/outcome field exists | Missing: `missing`; malformed/label-bearing: `blocked` |
| `budget_approval` | Launch-plan budget fields | Measured provider estimate is positive, contingency is non-negative, approved cap is positive and covers projected cost, annotation hours are positive, and denominator is 720 requests | Any absent/zero/inconsistent value: `blocked` |
| `advisor_ethics` | Optional `prepilot-human-approval/v1` record | `scope_approved=true`, ethics decision is `approved`, `not_required`, or `completed`, and `advisor_id`/`decided_at` are present | Missing or pending: `missing`/`blocked` |
| `reproducibility` | Optional `prepilot-reproducibility/v1` record | Valid corpus/configuration hashes match frozen-manifest and smoke-report hashes, immutable model versions are true, source revision and redacted report reference exist | Missing: `missing`; mismatch/incomplete: `blocked` |

The candidate row is allowed to pass as an inventory fact while the frozen row
remains blocked. This distinction is required: a 16-record pool is not a
12-record admitted corpus, and a candidate manifest cannot make the audit
green.

## Evidence schemas and cross-artifact rules

The audit reads only these metadata fields:

- Candidate/frozen corpus: `schema_version`, `status`, `record_count`,
  `project_count`, `raw_text_exported`, `selection_audit`, `records`, and each
  record's IDs, URLs, hashes, rights booleans, manipulation booleans, and
  review statuses. Frozen records must have unique `source_intent_id` and
  `project_id`, three 64-hex hashes, all four rights assertions, and all five
  manipulation assertions.
- Smoke config: the existing loader validates syntax; the audit additionally
  checks the exact two provider kinds without constructing an adapter.
- Smoke report: `schema_version`, `status`, `provider_count`,
  `budget_ready`, `configuration_sha256`, `config_template_sha256`, and
  provider `kind`, `status`, `successful_episode_count`, and `cost_status`.
  The configuration-template hash equals the canonical JSON SHA-256 of the
  supplied smoke config. Both provider kinds must be distinct and exactly
  `openai`/`deepseek`.
- Annotation selection: the fields produced by
  `label_plane.annotation_protocol._selection_manifest`, with no labels,
  outcomes, variants, oracle fields, or provider identity.
- Approval: `schema_version`, `scope_approved`,
  `ethics_privacy_decision`, `advisor_id`, and `decided_at`.
- Reproducibility: `schema_version`, `corpus_manifest_sha256`,
  `configuration_sha256`, `model_versions_immutable`, `source_revision`, and
  `redacted_report_reference`. The corpus hash equals the SHA-256 of the
  supplied frozen manifest; the configuration hash equals the smoke report's
  configuration hash.

Every metadata loader rejects a nested key containing `api_key`, `apikey`,
`authorization`, `password`, `secret`, or `token`, and rejects raw fields named
`source_text`, `canonical_text`, `clean_requirement`, `defective_requirement`,
`prompt`, `response`, `label`, `oracle`, or `artifact`. Rejected values never
appear in errors or reports.

## Report and error contract

The output schema is `prepilot-gate-audit/v1`:

```json
{
  "schema_version": "prepilot-gate-audit/v1",
  "decision": "no_go",
  "source_revision": "<git revision or null>",
  "gates": [
    {
      "id": "corpus_frozen",
      "status": "missing",
      "evidence": {"kind": "repository_artifact", "label": "frozen corpus manifest"},
      "blockers": ["frozen corpus manifest is absent"],
      "next_action_ids": ["validate_private_corpus_intake"]
    }
  ],
  "summary": {"pass": 0, "blocked": 7, "missing": 2}
}
```

Gate IDs and order are stable. A passing row has empty `blockers` and
`next_action_ids`. The deterministic action mapping is:

- `launch_plan` and `budget_approval` → `run_prepilot_readiness`;
- `corpus_candidate`/`corpus_frozen` → `validate_private_corpus_intake`, then
  `obtain_independent_review` when admission is incomplete;
- `provider_smoke_config`, `provider_qualification`, and `reproducibility` →
  `run_native_provider_smoke_after_approval`;
- `annotation_packet` → `prepare_blinded_packet`, then
  `obtain_independent_review`;
- `advisor_ethics` → `record_budget_and_human_approval`.

The audit reports IDs only; it never emits or executes shell commands. The
CLI returns 0 when a report is generated, including `no_go`, and returns 2 for
malformed/unsafe input or an output path inside the repository. The API raises
`PrepilotGateAuditError` for those same malformed/unsafe cases and writes
nothing.

## Acceptance scenarios

### Scenario 1 — clean main with no private artifacts

Given the launch plan exists but frozen corpus, smoke report, annotation
selection, approval, and reproducibility evidence are absent, when the audit
runs, then it returns a redacted `no_go` report with the nine ordered rows and
safe next-action IDs.

### Scenario 2 — candidate pool is ready but not admitted

Given candidate metadata reports 16 records across six projects and
`candidate_not_admitted`, when the audit runs, then `corpus_candidate` may be
`pass`, `corpus_frozen` is `blocked`, and the overall decision is `no_go`.

### Scenario 3 — all prerequisites are explicit

Given a synthetic valid launch plan whose existing evaluator returns `go`, a
frozen 12-record corpus, matching passing smoke config/report, valid annotation
selection, approval, budget, and reproducibility metadata, when the audit runs,
then it returns `decision: "go"` with nine `pass` rows.

### Scenario 4 — malformed or sensitive metadata

Given JSON contains a secret-like or raw-text field, invalid schema, or an
output path inside the repository, when the audit runs, then it fails closed,
writes no report, and does not echo the sensitive value.

### Scenario 5 — no provider work

Given provider credentials may exist in the environment, when the audit runs,
then it does not load them, instantiate an adapter, or perform a network call.

## Testing strategy

Add focused tests at the public audit boundary for all five scenarios,
including a complete synthetic `go` fixture and cross-artifact hash mismatch.
Run the existing readiness, corpus-intake, smoke, annotation, and full offline
suites. No live provider or browser test is in scope.
