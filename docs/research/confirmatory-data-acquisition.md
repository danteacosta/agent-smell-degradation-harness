# Confirmatory data-acquisition gate

The repository is protocol-ready but the checked-in dataset is not
confirmatory evidence.

## Current blocked state

- seven local source records;
- empty project identifiers;
- no external provenance/licensing records for the source intents;
- no live-provider T1-T3 trace corpus;
- no frozen human/adjudicated primary labels.

The manifest must remain blocked until these facts change. The offline
pre-pilot may use oracle validation as a development diagnostic, but its H2
output is explicitly marked non-confirmatory and cannot support the thesis
claim.

## Collection acceptance criteria

Before changing the manifest to confirmed:

1. collect at least 24 independent source intents across at least 6 projects;
2. record source URL/license, project ID, defect family, canonical hash, and
   near-clone result for each source intent;
3. run at least two real provider/model configurations with provider-produced
   T1 interpretation, T2 plan, and T3 execution events;
4. freeze request/response/configuration hashes, cost, latency, model version,
   trace hash, and checkpoint cutoff for every episode;
5. complete blinded human labels, double coding, adjudication, missing-label
   export, Krippendorff alpha, and bootstrap CI;
6. export a feature manifest and confirmatory H2 report before inspecting the
   terminal outcomes.

No record may be padded by renaming, paraphrasing without a declared
exception, or duplicating a project/intention.
