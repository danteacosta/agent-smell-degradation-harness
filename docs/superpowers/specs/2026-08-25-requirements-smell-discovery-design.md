# Requirements-smell discovery and executable evidence

Date: 2026-08-25
Status: approved by user; design review completed; implementation in progress

## Objective

Turn the advisor's request into a reproducible discovery process that makes the
effect of requirement smells observable:

1. identify the requirement-smell families supported by the literature;
2. assemble at least ten real-source requirement cases;
3. create clean and controlled-smelly variants without changing the intended
   feature except for one test-relevant condition;
4. generate acceptance criteria and a small executable implementation for each
   variant;
5. show when the smelly variant produces a semantically incomplete or buggy
   behavior; and
6. preserve the corpus, prompts, generated artifacts, test results and
   provenance under a tracked repository directory.

The discovery output is not presented as confirmatory thesis evidence until the
existing provider, annotation, licensing, split and preregistration gates pass.

## Evidence model

The literature is organized into two layers rather than treating every quality
attribute as an executable smell:

- broad quality dimensions: ambiguity, completeness, consistency, correctness,
  complexity, traceability, reusability, understandability, redundancy,
  verifiability, relevancy and undefined requirements;
- operational indicators: subjective language, ambiguous adverbs/adjectives,
  loopholes, open-ended/non-verifiable terms, superlatives, comparatives,
  negative statements, vague pronouns, uncertain verbs, polysemy, non-atomic
  requirements, incomplete conditions, incomplete system responses, passive
  voice, imprecise verbs and coordination ambiguity.

The primary treatment is a single missing or weakened test-relevant condition.
Other families are included only when the pair can retain the same intent and
an independent behavioral oracle can be written.

The literature discovery protocol records the search date, sources searched,
search strings, inclusion criteria (requirements-smell taxonomies, empirical
evaluations, or LLM/software-engineering studies that manipulate or measure
requirement quality), exclusion criteria (code-only smells, opinion pieces and
duplicate versions), and the normalized category mapping. Overlapping labels
are retained as aliases rather than silently collapsed.

## Corpus

The first discovery corpus contains twelve source intents, exceeding the
advisor's ten-case minimum. They are selected from six public projects exposed
by the ARTA requirements dataset: NFR, CCTNS, ERTMS, EIRENE/FUN, GAMMA-J and
Peering. The checked-in case records retain source identifier, project,
provenance URL, source hash, original excerpt, domain, lifecycle role, smell
family, evidence span, clean reconstruction, smelly mutation, and licensing
notes.

The pair semantics are explicit:

- `clean_requirement` states the condition that the oracle will test;
- `smelly_requirement` removes or weakens exactly one condition;
- `removed_condition` names the lost semantic obligation;
- `natural_variant` says whether the source itself supplied the variant;
- `contamination_notes` records that a clean counterpart may be a controlled
  reconstruction rather than an originally published sentence.

The twelve discovery cases are:

| Case | Project/source | Main smell | Executable behavior |
| --- | --- | --- | --- |
| ARTA-NFR-001 | NFR requirement 1 | vague threshold / numerical precision | refresh exactly every 60 seconds |
| ARTA-NFR-002 | NFR requirement 6 | vague authorization | deny users without the required role |
| ARTA-CCTNS-001 | CCTNS requirement 4 | incomplete condition | send an alert only after opt-in |
| ARTA-CCTNS-002 | CCTNS requirement 8 | incomplete response / completeness | preserve audit immutability and required fields |
| ARTA-ERTMS-001 | ERTMS requirement 3 | incomplete condition | block only unauthorized RBC movement |
| ARTA-ERTMS-002 | ERTMS requirement 16 | conditional ambiguity | apply brake only when required acknowledgement is missing |
| ARTA-FUN-001 | EIRENE/FUN requirement 12 | loophole / missing permission condition | only the call initiator may speak |
| ARTA-FUN-002 | EIRENE/FUN requirement 18 | cardinality ambiguity | reject more than six parties |
| ARTA-GAMMA-001 | GAMMA-J requirement 11 | vague threshold | deploy in less than one minute |
| ARTA-GAMMA-002 | GAMMA-J requirement 12 | cardinality/quantitative omission | enforce the 1000-user capacity |
| ARTA-PEERING-001 | Peering requirement 7 | incomplete system response | malicious requests are rejected, not merely noticed |
| ARTA-PEERING-002 | Peering requirement 9 | vague completeness | cover both anticipated and unanticipated traffic |

These are discovery cases, not claims that the source projects originally
contained the exact paired mutation. The source supplies ecological provenance;
the controlled pair supplies the causal contrast.

For every case, the source record also stores the dataset commit, source file,
record identifier, collection date, license/redistribution status, and a
source-text hash. If the source license is insufficient for redistribution, the
case is marked conditional and the repository stores only the minimum excerpt
needed for the local run plus the provenance metadata.

## Tasks and outputs

Each pair is evaluated through two task families:

1. acceptance-criteria generation, the primary task already supported by the
   harness;
2. behavioral code generation, an opt-in executable task that asks for one
   small Python function named `evaluate`.

The behavioral task is named `behavior_codegen` so the new executable contract
cannot silently change the historical JSON-only `codegen` benchmark. Its
contract defines the language, function signature, literal input format,
allowed output types, hidden-test schema and evaluator version. The oracle is
frozen before generation, kept outside the provider-visible pair and hashed.

The behavioral code-generation adapter will:

- parse the provider's JSON artifact;
- validate a restricted Python AST and reject imports, filesystem access,
  process creation, network access, dynamic evaluation, attributes and
  unapproved calls;
- execute only the candidate function against hidden, case-specific inputs in
  a subprocess with CPU, address-space, process-count, output-size and wall
  time limits, an empty environment and an isolated temporary directory;
- fail closed as `unsafe_not_run` when the host cannot provide the required
  limits, rather than treating an unisolated execution as evidence; and
- write the generated source, test report, stdout/stderr and a human-readable
  clean-versus-smelly comparison.

The clean artifact must satisfy the behavioral oracle. The smelly artifact is
allowed to fail the hidden test that exercises the removed condition. A failed
hidden test is the visual/behavioral equivalent of the advisor's slide: the
output can look valid while silently accepting an invalid case.

Execution states are recorded separately: `passed`, `failed_target_condition`,
`failed_unrelated_condition`, `invalid`, `unsafe_not_run`, `timeout` and
`crash`. Discovery metrics include target-condition failure rate, unrelated
failure rate, clean-versus-smelly degradation and silent-omission rate.

## Artifact layout

The repository will track small, reviewable discovery artifacts under:

```text
artifacts/experiments/
├── corpus/                 # case records and corpus manifest
├── runs/                   # compact run manifests and aggregate reports
├── generated-code/        # per-case clean/smelly source files
├── test-reports/          # hidden-test results and visible diffs
└── README.md
```

Large or provider-sensitive raw traces remain ignored under `runs/` unless a
run is deliberately promoted to a reproducibility bundle. No API keys or
unreviewed private prompts are committed. A promoted bundle includes the corpus
hash, source revision, environment summary, configuration hash and checksums
for every generated artifact.

## Acceptance criteria

Given one of the twelve source cases, when the local discovery command runs,
then it produces both variants, acceptance criteria and code artifacts, and a
machine-readable report identifying whether the hidden behavior tests passed.

Given a clean pair, when the deterministic offline provider is used, then the
clean implementation passes all hidden tests.

Given a smelly pair, when the deterministic smell-blind provider is used, then
the test exercising the removed condition fails and the report names that
condition.

Given a malformed or unsafe generated program, when it reaches the code
adapter, then it is rejected without execution and the episode is labeled
invalid rather than silently scored as correct.

Given all twelve discovery cases, when the offline command runs once, then it
produces 48 episodes: 12 cases × 2 variants × 2 task families.

Given the proposal update, when it describes the experiment, then it clearly
separates literature evidence, real-source provenance, controlled mutation,
offline demonstration and future live-provider/annotation evidence.

## Design choices

The existing `codegen` task contract remains compatible with the synthetic
fixtures. The executable behavior path uses the separate `behavior_codegen`
task family and is activated only for discovery case records that carry an
execution oracle. This avoids changing the historical benchmark while adding
the discovery capability requested by the advisor.

No new design pattern is introduced. The existing task-adapter boundary is the
extension point: it isolates the behavioral evaluator from acceptance-criteria
scoring and keeps the provider interface unchanged.
