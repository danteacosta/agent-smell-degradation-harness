# Requirements-smell discovery implementation plan

This plan implements the approved design in
`docs/superpowers/specs/2026-08-25-requirements-smell-discovery-design.md`.

## Acceptance tests

1. Given the twelve discovery case records, when the corpus loader runs, then
   every case has source provenance, a clean/smelly pair, one named removed
   condition, and both task-family contracts.
2. Given a clean discovery case, when the deterministic offline provider runs,
   then the generated implementation passes every hidden behavioral test.
3. Given a smelly discovery case and the deterministic smell-blind provider,
   when the generated implementation runs, then the test exercising the
   removed condition fails and the report identifies the failure.
4. Given an unsafe or malformed code artifact, when the behavioral adapter sees
   it, then it rejects the artifact without executing it.
5. Given a discovery run, when artifact materialization completes, then the
   tracked bundle contains the case manifest, run manifest, generated clean and
   smelly source files, hidden-test reports and aggregate comparison.
6. Given one offline discovery run, when the episode manifest is checked, then
   it contains exactly 48 episodes: 12 cases × 2 variants × 2 task families.

## Implementation steps

### 1. Literature and corpus records

- Add a versioned research catalog under `docs/research/` with the smell-family
  mapping, source links, evidence type, limitations and the twelve selected
  cases.
- Add the twelve case pair JSON files under `data/pairs/discovery/` and a
  corpus manifest under `data/confirmatory/` or `data/discovery/` without
  promoting them to confirmatory status.
- Preserve original excerpts, source URLs, SHA-256 hashes, project IDs and
  explicit notes about controlled reconstruction and licensing.

### 2. Safe behavioral code execution

- Add `eval/codegen_sandbox.py` with AST allowlisting, a small function-entry
  contract, no imports or I/O, subprocess isolation, CPU/memory/process/output
  limits, timeout and structured pass/fail results. Fail closed when required
  isolation is unavailable.
- Add a separate `BehavioralCodeGenerationAdapter` with task family
  `behavior_codegen`; preserve the historical exact-field `codegen` path for
  existing fixtures.
- Update pair validation to distinguish provider-visible oracle fields from
  private evaluator metadata and validate the new behavioral contract.
- Update `StubAgent` so deterministic clean artifacts use the clean behavioral
  artifact and smell-blind artifacts use each case's controlled defective
  implementation, without leaking private hidden tests into provider outputs.

### 3. Discovery runner and artifact exporter

- Add a dedicated `eval.discovery` command that loads only discovery pairs,
  runs acceptance criteria and behavioral code generation for clean/smelly variants, and
  supports deterministic offline mode first.
- Add `artifacts/experiments/README.md` and a tracked corpus manifest.
- Materialize per-episode implementation files, hidden-test JSON reports,
  stdout/stderr, a clean-versus-smelly diff and a compact aggregate report.
- Keep ordinary large `runs/` output ignored; the discovery command writes a
  deliberate compact bundle under the tracked artifact directory.

### 4. Tests and documentation

- Add unit tests for AST rejection, timeout, hidden-test pass/fail, oracle
  compatibility and artifact materialization.
- Add an integration test that runs all twelve cases in offline mode.
- Update README and Makefile with a no-credential discovery command and a
  separate live-provider command that clearly labels its evidence status.

### 5. Proposal update

- Re-read the live Google Doc immediately before editing it.
- Add the literature taxonomy, selected-case table, slide-3-style clean/smelly
  example, experiment protocol and noob-friendly explanation.
- Link source labels natively, preserve the existing document structure, and
  state that the local offline run demonstrates the pipeline while provider and
  human-label gates remain open.
- Re-read the edited Google Doc and, if available, export/render the document
  for layout QA.

## Verification commands

```bash
python -m pytest -q
python -m eval.discovery --mode offline --replications 1
python -m eval.discovery --verify-artifacts
```

The live-provider command is prepared but is not part of the default local
verification because it requires credentials and an explicit cost envelope.
