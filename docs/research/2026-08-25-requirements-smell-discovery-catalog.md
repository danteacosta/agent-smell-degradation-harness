# Requirements-smell discovery catalog

Date: 2026-08-25
Status: discovery baseline; not confirmatory evidence

## Why this catalog exists

The advisor's request is not only to list smells. It is to show the causal
chain:

```text
real-source requirement
        ↓ one controlled condition removed
clean / smelly pair
        ↓ LLM generates acceptance criteria and code
independent behavioral tests
        ↓
visible semantic loss or preserved behavior
```

The catalog separates three things that are often mixed together:

1. a quality dimension used to describe the problem;
2. a concrete language indicator used to operationalize a smell; and
3. a test-relevant condition whose loss can be demonstrated in an artifact.

## Search and selection protocol

Search date: 2026-08-25.

Sources searched: the supplied papers and preprints, web search results, arXiv,
ScienceDirect landing pages, Zenodo replication packages, and the ARTA public
dataset repository.

Representative search strings:

- `requirements smells taxonomy empirical study`
- `requirements smells LLM prompts code generation`
- `natural language requirements testability smells`
- `requirements ambiguity LLM code generation empirical`
- `requirements quality acceptance criteria generated code`

Included: taxonomies or empirical studies of requirements smells; studies that
measure the effect of requirement quality on an SE task; studies that manipulate
requirements or compare clear and defective variants; public datasets or
replication packages with traceable requirements and tests.

Excluded: code-only smell taxonomies, opinion pieces without an empirical or
taxonomy contribution, duplicate preprint/publisher versions, and datasets with
no usable provenance or no way to identify the requirement record.

Overlapping terms are retained as aliases. For example, “non-verifiable terms”
can include open-ended terms and loopholes in one taxonomy, while another paper
treats them as separate indicators.

## What the literature says

### Broad quality dimensions

[Gentili and Falessi, *Characterizing Requirements Smells*](https://arxiv.org/abs/2404.11106)
reports a practitioner characterization based on ten experienced practitioners
from a safety-critical company. Its mapping-study baseline contains ambiguity,
completeness, consistency, correctness, complexity, traceability, reusability,
understandability, redundancy, verifiability, relevancy and undefined
requirements. Ambiguity, verifiability and consistency were perceived as among
the most severe; perceived frequency and impact varied by smell, role, domain
and lifecycle phase. This supports treating smells as contextual indicators,
not universal causal labels.

### Concrete language indicators

[Femmer et al., *Rapid Quality Assurance with Requirements Smells*](https://arxiv.org/abs/1611.08847)
operationalizes smell locations and detection mechanisms through Smella. The
studied indicators include subjective language, ambiguous adverbs/adjectives,
loopholes, open-ended/non-verifiable terms, superlatives, comparatives,
negative statements and vague pronouns. The study used three industrial and one
university context and reported substantial variation in detection performance,
which is a reason to keep an independent behavioral oracle in this project.

[Zakeri-Nasrabadi and Parsa, *Natural Language Requirements Testability Measurement Based on Requirement Smells*](https://arxiv.org/abs/2403.17479)
uses the ARTA dataset and a nine-smell set: subjective language, ambiguous
adverb/adjective, non-verifiable terms, superlatives, comparatives, negative
statement, vague pronouns, uncertain verbs and polysemy. It is especially
relevant here because it connects the smell to testability rather than treating
the smell label as the final outcome.

[Veizaga, Shin and Briand, *Automated Smell Detection and Recommendation in Natural Language Requirements*](https://arxiv.org/abs/2305.07097)
studies a financial industrial case with 2,725 annotated requirements from 13
systems. Its Paska/Rimay vocabulary adds non-atomic requirements, incomplete
requirements, incorrect order, coordination ambiguity, not-a-requirement,
incomplete condition, incomplete system response, passive voice and imprecise
verbs. These categories are useful for the code-generation extension because
they point directly to missing behavior or test cases.

### Conditions and downstream LLM tasks

[Fischbach et al., *How Do Practitioners Interpret Conditionals in Requirements?*](https://arxiv.org/abs/2109.02063)
reports a study with 104 requirements-engineering practitioners interpreting
twelve conditional requirements. Participants disagreed about necessity,
sufficiency and temporal ordering. This is the strongest basis for the slide-3
manipulation: remove one condition while preserving the surface intention, then
check whether the downstream artifact silently broadens behavior.

[Vogelsang et al., *On the Impact of Requirements Smells in Prompts: The Case of Automated Traceability*](https://arxiv.org/abs/2501.04810)
compares clear and smelly prompts for automated traceability using two LLMs. The
reported effects were task- and metric-dependent: a small significant effect
appeared for whether a requirement was implemented, while identifying exact
implementation lines did not show the same effect. That result motivates
measuring both acceptance criteria and executable behavior instead of assuming
one metric is enough.

[Villamizar et al., *Replication Package: On the Impact of Requirement Smells in LLM-Based Code Generation*](https://zenodo.org/records/17441075)
directly supports the new code-generation track. The package reuses a
requirements-smell benchmark and evaluates test-suite-based functional
correctness of generated code for four game applications. Its description
reports that higher smell density was generally associated with lower functional
correctness, while the effect of individual smell categories varied by model
and application. We use this as a methodological precedent, not as evidence
about the ARTA cases.

[Mu et al., *ClarifyGPT: Empowering LLM-based Code Generation with Intention Clarification*](https://arxiv.org/abs/2310.10996)
is relevant to the discovery workflow because it detects ambiguity, asks
targeted questions and then regenerates code. It supports a later clarification
extension, but the current discovery keeps the first comparison direct so that
the effect of the smell is not confounded by an intervention.

## Normalized smell map

| Operational family used here | Literature aliases | Discovery treatment |
| --- | --- | --- |
| Missing/incomplete condition | incomplete condition, incomplete requirement, loophole | remove one permission, trigger or negative case |
| Vague threshold/cardinality | ambiguous adverb/adjective, non-verifiable term, comparative, superlative | replace exact number with vague phrase |
| Authorization/response loss | incomplete system response, loophole, negative statement | retain request but remove deny/reject/permission behavior |
| Conditional interpretation | conditional ambiguity, vague temporal relation | remove necessity/failure branch while preserving main action |
| Completeness/coverage loss | completeness, non-atomicity, open-ended term | remove one required category or response |
| Lexical ambiguity | vague pronoun, subjective language, polysemy, imprecise verb | reserve for later cases when an independent oracle remains stable |

The discovery's primary causal contrast is the first five rows. Lexical cases are
kept in the catalog but are not forced into the first executable corpus if a
clean oracle cannot be written without changing the intended feature.

## Real-source discovery corpus

The twelve cases are sourced from the public [ARTA repository](https://github.com/m-zakeri/ARTA/)
and its [Zenodo dataset record](https://zenodo.org/records/4266727). The source
projects are NFR, CCTNS, ERTMS, EIRENE/FUN, GAMMA-J and Peering. The source text
provides ecological provenance; clean counterparts and smelly variants are
controlled reconstructions. The case manifest records source file, record ID,
dataset revision, source hash and licensing status.

| Case group | Source record | Condition demonstrated |
| --- | --- | --- |
| NFR-001 | requirement 1 | refresh interval of exactly 60 seconds |
| NFR-002 | requirement 6 | access only for authorized users |
| CCTNS-001 | requirement 4 | opt-in alert condition |
| CCTNS-002 | requirement 8 | immutable audit trail and required fields |
| ERTMS-001 | requirement 3 | RBC authorization before movement |
| ERTMS-002 | requirement 16 | brake only when acknowledgement is missing |
| FUN-001 | requirement 12 | only call initiator may speak |
| FUN-002 | requirement 18 | maximum of six parties |
| GAMMA-001 | requirement 11 | deployment under one minute |
| GAMMA-002 | requirement 12 | capacity of 1,000 concurrent customers |
| Peering-001 | requirement 7 | malicious request rejection |
| Peering-002 | requirement 9 | anticipated and unanticipated traffic |

The minimum discovery output is 48 episodes: twelve cases × two variants × two
task families. It is a pipeline demonstration and corpus audit, not a
confirmatory estimate. Confirmatory use still requires the project's existing
provider qualification, double annotation, license review, split freeze and
preregistration gates.

## Slide-3-style example

```text
Clean requirement:
The link expires in 15 minutes and can be used only once.

Smelly requirement:
The link expires in 15 minutes.

Clean implementation:
  reject if expired OR already_used

Smelly implementation:
  reject if expired

Hidden test:
  use the same link twice

Observed result:
  clean -> rejected on second use
  smelly -> accepted on second use
```

The second implementation can be syntactically valid and can pass visible
happy-path tests. The defect is semantic incompleteness: a test-relevant
condition disappeared.

## Second phase: measuring verifier effectiveness

The first phase answers “can a requirement smell be connected to a visible
behavioral difference?” It does not answer “can the reliability agent catch the
problem before the artifact is delivered?” The second phase makes that a
separate evaluation:

```text
T0--T3 observable prefix
  -> verifier risk score and approve/warn/block decision
  -> artifact + independent hidden behavior tests
  -> post-decision label joined for evaluation only
```

The verifier is evaluated as a binary alerting system: `warn` or `block` is an
alert, and `approve` is no alert. A smelly episode that fails the target hidden
condition is a positive label; a clean episode that passes is a negative label.
Unsafe or unknown execution states are ineligible, not silently treated as
passes. This keeps the causal order visible: the decision exists before the
oracle result.

The tracked implementation is a transparent discovery rule pack, not a trained
classifier. Its text signals operationalize the literature's recurring
dimensions: vague/non-verifiable language, missing condition branches,
unbounded thresholds/cardinality, missing system responses, permission loss,
and incomplete completeness scope. Its provenance signals reuse the deployable
T1/T2/T3 feature boundary for contradictions, unresolved references and
pre-final execution errors. The rule pack is intentionally inspectable so that
the advisor can see why each warning happened; a later study can replace it
with a learned or LLM-based verifier after train/calibration/test splits are
frozen.

The efficacy report records more than “how many it got right”:

| Question | Metric |
| --- | --- |
| Did it catch degraded behavior? | recall / warning coverage |
| Did it avoid annoying clean cases? | clean false-alert rate and specificity |
| Are alerts trustworthy? | precision and F1 |
| Does the smell move the score in the expected direction? | clean-versus-smelly paired discrimination and mean score delta |
| Did it warn early enough to be useful? | first-signal checkpoint and lead time before artifact completion |
| Can it run economically? | verifier runtime, provider latency/cost and alerts per detected failure |
| Does it work across contexts? | project, smell-family, task-family and checkpoint strata |
| Can another researcher audit it? | portable trace coverage, leakage rejections and stable decision hashes |

For this discovery pilot, `promising` is a development status only: no leakage,
all eligible labels, recall at least 0.80, clean false-alert rate at most 0.20,
and paired discrimination at least 0.80. Failure of a criterion produces an
`inconclusive` or `fail` report and identifies the next gap; it does not become
a claim about the population of requirements.

The current v6 offline bundle reports 24 eligible behavior episodes: 10 true
positives, 2 misses, 12 true negatives and 0 false positives (recall 0.833,
precision 1.000, F1 0.909, clean false-alert rate 0.000, paired
discrimination 0.833). The two misses are `incomplete_condition` in ERTMS and
`vague_completeness` in Peering, which is useful discovery evidence: a lexical
and rule-based verifier does not recover every omitted condition. The result is
therefore “promising for this controlled pilot,” while the live-provider and
grouped holdout study remains necessary for an efficiency claim.

The corresponding artifacts are tracked under
`artifacts/experiments/runs/discovery-20260826-v6/`: portable
`observable-traces/`, generated code, hidden-test reports, source comparisons,
`verification/decisions.jsonl`, `verification/labels.jsonl`,
`verification/metrics.json` and a short README. Decisions contain opaque
episode references and no variant/smell/oracle fields. Labels are written only
after the decisions and are used for evaluation metrics, not for scoring.

This phase also clarifies the role of the auxiliary repositories. The primary
harness owns the detector, corpus, behavior oracle and metrics. The
[`agent-reliability-protocol`](https://github.com/danteacosta/agent-reliability-protocol)
repository supplies lifecycle identity, checkpoint ordering, timestamps and
the evidence boundary. The protocol is not changed to carry the experiment's
terminal labels; it remains a reusable interchange contract.
