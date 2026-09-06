# Prepare and launch the source-based pilot

Read the [frozen-design candidate protocol](source-based-pilot-protocol.md) first.
The current command prepares private data offline. It **cannot launch** the pilot
and must not be described as an already validated 24-intent runner.

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

1. Choose the repetition/budget option. The current US$1 authorization remains
   in force. Five repetitions reserve roughly US$6.38 before final token-fit
   validation; one reserves roughly US$1.54. Do not purchase credits or increase
   a cap without the user's explicit decision.
2. Record an authorization addendum naming an exploratory, LLM-judged pilot,
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
4. Implement/validate the selected 24-intent runtime without weakening the old
   12-intent gates. Required acceptance evidence: exact call-plan counts,
   shared cost ledger, no retries with ambiguous cost, checkpoint completeness,
   correct private joins, v2 parsing, duplicate selection before labels,
   self/cross accounting, no-compaction and stage timestamps before T4.
5. Freeze final corpus, configurations and admission decisions. Measure actual
   request/schema token fit without truncating source conditions. Check keys by
   presence only; check account funding separately. Never print credentials.
6. Execute the initial source-control/natural-transfer block, apply the protocol's
   continue/adjust/stop rule, and only then continue prospective generation.
   Preserve costs from stopped blocks in the single pilot total.

No paid launch command is provided yet because the expanded runtime and final
budget choice are unresolved. Do not substitute `eval.exploratory_prepilot`
with a 24-record file or pass the new schema to the old intake.

## Outputs to preserve and publish

Keep source and license/notice snapshots, source/transformation audit, references,
selection manifests, old labels, new raw responses, returned model identities,
all configuration hashes, per-call usage/cost and unresolved reservations in
approved private storage. Preserve incomplete trajectories and zero-cost local
T3 events explicitly. Publish only reviewed aggregate counts, limitations and
protocol status; no source excerpts, private identities or private run hashes.

Drive synchronization and a final paid execution are not performed by this
preparation command. Update research artifacts only with the actual state:
candidate package prepared; corpus admission and pilot launch pending.
