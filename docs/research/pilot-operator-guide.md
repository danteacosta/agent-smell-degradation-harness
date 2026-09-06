# Prepare and launch the source-based pilot

Read the [frozen-design candidate protocol](source-based-pilot-protocol.md) first.
The preparer creates inputs offline. The separate `eval.pilot_runtime` now
provides gated screening, diagnostics, generation and judging under the user's
US$7 total authorization. Prospective collection is intended for 7–13 September.

## What is prepared

The private package has 24 source-pinned candidates and references, six control
seeds / 30 cases, 18 selected natural text clusters with historical labels kept
separate, 30 screening packets, request-only JSONL, prices, hashes, budget options
and a redacted readiness report. A new output directory is required; existing
evidence cannot be overwritten. Output inside any Git checkout is rejected.

Use the project Python environment from the repository root:

```sh
python -m eval.pilot_preparation \
  --candidates /approved-private/pilot-inputs/candidates.json \
  --control-seeds /approved-private/pilot-inputs/control-seeds.json \
  --natural-pool /approved-private/pilot-inputs/natural-pool.json \
  --prices /approved-private/pilot-inputs/prices.json \
  --output /approved-private/pilot-preparation-new
```

Input files are private JSON arrays. The example paths are placeholders. This
command reads no keys, instantiates no API client and makes zero provider calls.
Its successful exit means preparation succeeded, not that readiness is go.
Run `verify_preparation(Path(...))` from `eval.pilot_preparation` to check the
bundle's file inventory/hashes. Preserve an external copy of the manifest hash:
self-consistency is not cryptographic proof against rewriting the entire bundle.

## Actions needed before the target week

1. Preserve the user's 6 September authorization: five repetitions, US$7 total,
   expanded LLM-only exploratory scope. The current complete reservation is
   US$6.482882 including contingency. Do not purchase credits or increase a cap.
2. Keep an authorization addendum naming an exploratory, LLM-judged pilot,
   24 intents / at least six project IDs, chosen repetitions, two providers,
   all screening/transfer/control calls, cap, privacy/retention policy, operator
   and applicable advisor/institutional decision. This is not a request for
   human annotation. The previous 120-episode pre-pilot approval alone is not
   documented approval for the expanded study.
3. Resolve the one near-clone flag and source-license notices, then run the
   frozen independent LLM screening packets within the same approved budget.
   Reject/quarantine disputed pairs; do not replace them based on judge scores.
   If fewer than 24 survive, admit replacements and issue a new pre-collection
   manifest. Keep CASS's AI-assisted source authorship and source-family
   dependencies visible.
4. Re-run the 24-intent offline runtime tests after implementation changes,
   without weakening the old 12-intent gates. Acceptance evidence: exact counts,
   shared cost ledger, no retries with ambiguous cost, checkpoint completeness,
   correct private joins, v2 parsing, duplicate selection before labels,
   self/cross accounting, no-compaction and stage timestamps before T4.
5. Freeze final corpus, configurations and admission decisions. Measure actual
   request/schema token fit without truncating source conditions. Check keys by
   presence only; check account funding separately. Never print credentials.
6. Execute the initial source-control/natural-transfer block, apply the protocol's
   continue/adjust/stop rule, and only then continue prospective generation.
   Preserve costs from stopped blocks in the single pilot total.

Do not substitute `eval.exploratory_prepilot` with a 24-record file or pass the
new schema to the old intake. Use the same run directory for every phase:

```sh
python -m eval.pilot_runtime create --run /approved-private/pilot-run \
  --package /approved-private/pilot-preparation \
  --config tasks/exploratory_llm_judged_prepilot.example.json \
  --authorization /approved-private/pilot-authorization.json
python -m eval.pilot_runtime preflight --run /approved-private/pilot-run
python -m eval.pilot_runtime screening --run /approved-private/pilot-run \
  --env-file /approved-private/provider.env
# Resolve and preserve admission.json before proceeding.
python -m eval.pilot_runtime diagnostics --run /approved-private/pilot-run \
  --env-file /approved-private/provider.env
# Only a passed diagnostic gate permits the following prospective phases.
python -m eval.pilot_runtime generation --run /approved-private/pilot-run \
  --env-file /approved-private/provider.env
python -m eval.pilot_runtime judging --run /approved-private/pilot-run \
  --env-file /approved-private/provider.env
```

Authorization schema: `pilot-authorization/v1`, integer
`approved_cap_microusd: 7000000`, integer `repetitions: 5`, boolean
`exploratory_llm_scope_confirmed: true`, and a nonempty `source` attestation.
It does not contain secrets. The provider example supplies only its `providers`
array; its historical US$1 pre-pilot fields do not override the new authorization.

Admission schema: `pilot-admission/v1`, the exact `package_sha256`, `review_scope`
equal to `AI-assisted exploratory; not independent human validation`, and exactly
24 `records`. Each needs `intent_id`, `decision: admit_exploratory`, and specific
`rights_evidence`, `source_revision_evidence`, `independence_disposition`,
`manipulation_disposition`, `review_evidence`. Preserve
`control_oracle_dispositions` for the six seeds too. These fields document an
operator's evidence review; strings alone cannot prove rights or correctness.
Do not fill them with generic approval assertions or promote model consensus
to human validation. Unresolved material objections prevent admission.

Preflight is read-only, including journal verification. The diagnostic gate is
recomputed from paid raw responses; editing a report's decision cannot unlock
generation. Calls have no hidden SDK or application retries. Missing journals,
changed code/configuration, ambiguous charges and partial trajectories require
reconciliation; never reset the directory or replay a trajectory with new times.

## Outputs to preserve and publish

Keep source and license/notice snapshots, source/transformation audit, references,
selection manifests, old labels, new raw responses, returned model identities,
all configuration hashes, per-call usage/cost and unresolved reservations in
approved private storage. Preserve incomplete trajectories and zero-cost local
T3 events explicitly. Publish only reviewed aggregate counts, limitations and
protocol status; no source excerpts, private identities or private run hashes.

The CLI does not synchronize Drive. Update research artifacts only with actual
collected results and outstanding gates, keeping simulation separate from live
provider evidence. The public protocol is not a private evidence repository.
