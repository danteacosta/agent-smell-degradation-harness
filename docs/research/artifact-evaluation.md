# Artifact-evaluation checklist

The public artifact is considered research-ready only when the following evidence is present:

- a confirmed freeze manifest with SHA-256 hashes for protocol, precision plan, runtime producer, feature schema, annotation rubric, split algorithm, and analysis;
- a dataset manifest with source provenance, licensing, project IDs, independent intent hashes, and no near-clone padding;
- live-provider run manifests with provider, model/version, configuration hash, latency, cost, request/response hashes, and mode separation;
- T1/T2/T3 checkpoint traces externally materialized by the instrumented runtime and timestamped before T4, plus proof that no retrospective snapshot or chain-of-thought entered the feature plane;
- blinded human annotations, a 20% duplicate subset, missing-label export, adjudication records, Krippendorff alpha, and bootstrap CI;
- a feature manifest bound to trace hashes and a confirmatory H2 report containing fixed B0–B3 models, primary B3−B0 delta, cluster bootstrap interval, and claim decision;
- negative-control and ablation results showing that shuffled or terminal-leaking evidence cannot pass the feature boundary;
- clean-environment replay instructions with the exact ARP compatibility matrix;
- a product smoke bundle containing a pre-merge JSON/SARIF decision, reviewed candidate-memory record, semantic-QA findings, and operational ROI fields.

The current seven-source local seed, synthetic agreement demo, stub runs, and product demo fixtures remain explicitly non-confirmatory.
