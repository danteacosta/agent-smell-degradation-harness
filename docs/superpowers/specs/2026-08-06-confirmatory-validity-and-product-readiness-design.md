# Confirmatory Validity and Product Readiness

## Goal

Make the thesis and sister product defensible under a stress test: real agent checkpoints, non-degenerate provenance features, independent primary labels, fail-closed H2 analysis, explicit sample-size boundaries, reproducible artifacts, and a demonstrable product gate.

## Scientific contract

The primary scientific claim is narrowed to the incremental value of pre-final provenance for detecting constraint-preservation failures in acceptance-criteria/test generation. H1 measures paired impact of controlled requirement defects. H2 compares provenance against deployable text/static and operational baselines on unseen intent/project groups. Traceability remains external validation; clarification remains conditional.

The primary outcome is binary/ordinal preservation of requirement constraints in the generated acceptance criteria. Executability, coverage, traceability, and verifiability are secondary outcomes. Human/adjudicated labels are the primary H2 labels; executable oracle results remain independent validation evidence.

The confirmatory gate requires a frozen data manifest, real provider run, genuine T1–T3 provider-produced checkpoints, human double annotation, a valid train/calibration/test split, explicit baseline PR-AUCs, `delta_pr_auc`, a cluster bootstrap interval, and a deterministic claim decision. The checked-in seven-source seed remains pilot-only.

## Architecture

### ASD research harness

- `agents/live.py` or an injected provider adapter emits structured interpretation, plan, and execution summaries. The runner records these outputs without copying `variant`, `smell`, oracle, or terminal artifact metadata into the deployable feature plane.
- A versioned pre-final feature schema extracts variable signals: constraint count/types, quantities, unresolved references, assumptions, contradictions, revisions, validation coverage, and operational telemetry.
- A frozen annotation manifest supplies primary labels by episode, with blinded duplicate coding, missing-label policy, adjudication, and provenance hashes. H2 refuses oracle-derived labels unless explicitly running a non-confirmatory demo.
- H2 accepts only a versioned feature manifest and trace hashes. Direct score injection is rejected in confirmatory mode. The report compares each family and baseline, computes the primary delta and cluster bootstrap interval, and emits a claim decision.
- Data and sample-size validation distinguishes pilot/descriptive evidence from confirmatory evidence. Project-level generalization is only claimed when the pre-registered project count and precision simulation pass.

### RAG product layer

- The product remains separate from thesis labels and estimands.
- Candidate memory ingestion consumes session handoffs with required source references, confidence, category, retention metadata, and reviewer status.
- Semantic QA runs against a typed rule registry and is asynchronous at the integration boundary; the gate remains deterministic and never silently changes a claim.
- Product evaluation reports retrieval relevance, false-alert rate, review latency, memory acceptance/rejection, and operational ROI. Persistence is append-only but validates records and supports safe concurrent writers through a repository-owned lock/transaction boundary.
- ARP version is aligned across repositories or an explicit compatibility matrix is shipped and tested.

## Failure modes and invariants

- Missing project/source provenance, missing human label, invalid trace hash, missing provider metadata, or non-real T1–T3 checkpoints fail closed for confirmatory analysis.
- Any terminal key or condition metadata in pre-final attributes is rejected.
- Feature rows must be non-constant on the pilot validation set where variation is expected; otherwise the family is marked non-informative rather than presented as evidence.
- All reports include dataset/code/environment/provider/feature/split hashes.
- Stub, replay, mock, and live results are never pooled.

## Verification strategy

- TDD tests cover provider checkpoint capture, terminal-field rejection, feature non-degeneracy, annotation label selection, score-manifest binding, H2 delta/CI/claim logic, sample-size gates, and product memory/lint persistence behavior.
- Clean-environment tests run both repositories with the pinned ARP version and no `PYTHONPATH` overlay.
- A confirmatory dry run must fail closed on the current seed and pass schema validation only for a complete external manifest.
- A product smoke run must produce a pre-merge JSON/SARIF decision, a reviewed memory candidate, semantic findings, and an ROI summary from a fixture session.

## Explicit non-goals

- No new broad requirements-smell taxonomy.
- No raw-transcript vector database.
- No claim that the product replaces tests, review, or terminal validation.
- No requirement that the optional journey graph or clarification intervention be completed for the master's core claim.
