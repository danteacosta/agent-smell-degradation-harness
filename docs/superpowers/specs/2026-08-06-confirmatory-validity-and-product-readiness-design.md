# Confirmatory Validity and Product Readiness

## Goal

Make the thesis and sister product defensible under a stress test: real agent checkpoints, non-degenerate provenance features, independent primary labels, fail-closed H2 analysis, explicit sample-size boundaries, reproducible artifacts, and a demonstrable product gate.

## Scientific contract

The primary scientific claim is narrowed to the incremental value of pre-final provenance for detecting constraint-preservation failures in acceptance-criteria/test generation. H1 measures paired impact of controlled requirement defects. H2 compares provenance against deployable text/static and operational baselines on unseen intent/project groups. Traceability remains external validation; clarification remains conditional.

The primary outcome is a frozen binary label: material constraint-preservation failure (severity 2–3) versus no material failure (severity 0–1) in the generated acceptance criteria. Ordinal severity is secondary. Executability, coverage, traceability, and verifiability are secondary outcomes. Human/adjudicated labels are the primary H2 labels; executable oracle results remain independent validation evidence.

The confirmatory gate requires a freeze commit containing the preregistration, ARP compatibility matrix, feature schema, annotation rubric, and analysis code before any provider run; a frozen data manifest; a real provider run; genuine T1–T3 provider-produced checkpoints with provider request/response hashes and timestamps before T4; human double annotation of a preselected 20% duplicate subset; a valid train/calibration/test split; explicit baseline PR-AUCs selected on train only; `delta_pr_auc = PR-AUC(provenance) - PR-AUC(best deployable baseline)`; a source-intent-cluster bootstrap interval with degenerate resamples retained and reported; and a deterministic claim decision. The checked-in seven-source seed remains pilot-only.

The minimum confirmatory design is 24 independent source intents across at least 6 projects, with at least 4 intents per project and at least 8 intents in each train/calibration/test partition after project holdout. If a frozen power/precision simulation shows a larger design is needed, the larger design governs. A 12-intent/3-project run is a structured pilot and cannot support a project-generalization claim.

## Architecture

### ASD research harness

- `agents/live.py` or an injected provider adapter emits structured interpretation, plan, and execution summaries. A confirmatory provider must implement `observe_checkpoints()` and include provider/model/version/configuration identifiers, request and response hashes, source event IDs, and timestamps earlier than artifact completion. The runner records these outputs without copying `variant`, `smell`, oracle, or terminal artifact metadata into the deployable feature plane.
- A versioned pre-final feature schema extracts variable signals: constraint count/types, quantities, unresolved references, assumptions, contradictions, revisions, validation coverage, and operational telemetry.
- A frozen annotation manifest supplies primary labels by episode, with blinded duplicate coding, missing-label policy, adjudication, and provenance hashes. H2 refuses oracle-derived labels unless explicitly running a non-confirmatory demo.
- H2 accepts only a versioned feature manifest and trace hashes. Direct score injection is rejected in confirmatory mode. The binary label mapping, train-only baseline selection, source-intent cluster unit, bootstrap seed/draw count, degenerate-resample policy, and claim rule are frozen. The report compares every family and baseline, computes the primary delta and cluster bootstrap interval, and emits a claim decision.
- Data and sample-size validation distinguishes pilot/descriptive evidence from confirmatory evidence. Project-level generalization is only claimed when the pre-registered project count and precision simulation pass.

### RAG product layer

- The product remains separate from thesis labels and estimands.
- Candidate memory ingestion consumes session handoffs with required source references, confidence, category, retention metadata, and reviewer status.
- Semantic QA runs against a typed rule registry and is asynchronous at the integration boundary; the gate remains deterministic and never silently changes a claim.
- Product evaluation reports retrieval relevance, false-alert rate, review latency, memory acceptance/rejection, and operational ROI. Persistence is append-only but validates records, enforces payload limits/retention metadata, supports deletion/access audit, and supports safe concurrent writers through a repository-owned lock/transaction boundary. A stale or unavailable semantic-lint worker is explicit `unknown`/fail-closed state, never silent success; rule versions and ordering are deterministic.
- The wire schema is ARP `2.0.5`; the Python package compatibility matrix explicitly documents tested package versions (including `2.0.6`) and is enforced by fixtures in both repositories.

## Failure modes and invariants

- Missing project/source provenance, missing human label, invalid trace hash, missing provider metadata, or non-real T1–T3 checkpoints fail closed for confirmatory analysis.
- Confirmatory execution fails unless the provider run manifest hashes exactly match the freeze commit; no provider execution or analysis is allowed before that freeze.
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
