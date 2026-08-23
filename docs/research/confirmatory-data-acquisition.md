# Confirmatory data-acquisition gate

The repository is protocol-ready but the checked-in dataset is not
confirmatory evidence.

## Current blocked state

- seven local source records;
- empty project identifiers;
- no external provenance/licensing records for the source intents;
- no live/runtime-native ARP 3.0 T1-T3 trace corpus;
- no frozen human/adjudicated primary labels.

The manifest must remain blocked until these facts change. The offline
pre-pilot may use oracle validation as a development diagnostic, but its H2
output is explicitly marked non-confirmatory and cannot support the thesis
claim.

## Collection acceptance criteria

Before changing the manifest to confirmed:

1. freeze an outcome-blind `h2-precision-plan/v2`, then collect at least its
   required design; the simulation must evaluate only the frozen test partition
   and resample `project_id`. The unconditional floor is 60 independent intents
   across 12 projects with at least 6 test projects/24 test intents; the current
   conservative candidate is 220 intents/36 projects with 11 test projects and
   remains unfrozen pending the pre-pilot variance update;
2. record source URL/license, project ID, defect family, canonical hash, and
   near-clone result for each source intent;
3. run at least two real provider/model configurations through one instrumented
   execution per episode, emitting native ARP 3.0 `agent-smell-degradation/v1`
   T1 interpretation, T2 plan, and T3 execution events with monotonic runtime
   timestamps; `runtime_native` means externally materialized bounded events,
   not chain-of-thought. Retrospective prompted snapshots and replay are ineligible;
4. freeze request/response/configuration hashes, cost, latency, model version,
   trace hash, and checkpoint cutoff for every episode;
5. complete blinded human labels, double coding, adjudication, missing-label
   export, Krippendorff alpha, and bootstrap CI;
6. validate the T0-T3/T4 temporal boundary and label-plane isolation for every
   episode, then export an `h2-features/v3` manifest whose raw T1/T2/T3 features
   are recomputed from the hash-bound traces; fit all family/checkpoint models
   on train only and export the confirmatory H2 report before inspecting the
   held-out outcomes. The fixed models are B0=static+operational and
   B1/B2/B3=B0 plus cumulative provenance through T1/T2/T3; precomputed scores
   and in-sample family selection are ineligible. The primary H2 interval
   resamples test projects, and leave-one-project-out stability is reported.

No record may be padded by renaming, paraphrasing without a declared
exception, or duplicating a project/intention.
