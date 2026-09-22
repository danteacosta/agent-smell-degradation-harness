# Literature matrix

Last updated: 2026-09-21
Canonical policy: deduplicate by DOI, then by normalized title. A source enters this
matrix only after its abstract and the relevant method, results, and limitations
have been read. Product-only sources must not support scientific claims.

| Source | Year / venue / status | Question and data | Method | Main result | Limitations and threats | Thesis relevance | Experiment relevance | Product relevance | Concrete action | Credibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: |
| [Peng et al., *A Data Annotation Requirements Representation and Specification (DARS)*](https://doi.org/10.48550/arXiv.2512.13444) | 2025, arXiv preprint under review | Whether annotation-specific requirements can reduce recurring quality failures; an automotive perception demonstration and analytical mapping to 18 previously identified annotation-error types | Design-science artifact combining a six-field negotiation card with atomic standard, edge-case and exception scenarios; authors map artifact fields to error causes | The authors report at least one proposed mitigation for each error; the card maps to 29/44 root causes and the scenario specification to 18/44 | No observed before/after annotation study; simplified automotive example; researcher-authored mapping may be biased; informal partner feedback; generalization and industrial deployment remain future work | Treat the human-label process itself as a requirements object with explicit traceability, exceptions and governance | Bind roles, rubric and queue hashes, rehearsal, hand-off, feedback and exception behavior before packet distribution | Suggests a future customer-facing review-policy contract, but does not validate product value | Add a fail-closed annotation-study charter; do not treat charter completion as label quality evidence | 6/10: transparent 17-page preprint with explicit artifact and threats, but no peer review or observed effectiveness |
| [Vogelsang et al., *On the Impact of Requirements Smells in Prompts*](https://doi.org/10.1109/ICSE-NIER66352.2025.00016) | 2025, ICSE-NIER, peer-reviewed | Whether requirement smells affect automated requirement-to-code traceability; two LLMs and five simple-game projects | Controlled smelly variants; trace-existence and line-level tracing outcomes | Small significant effect for trace existence, but no significant line-level effect | Short NIER paper; one downstream task; small/simple projects; effects are task- and metric-dependent | Direct evidence that a smell is a risk indicator, not the outcome itself | Keep H1 task-specific and preserve separate outcome dimensions | Supports task-specific diagnostics rather than a universal smell score | Retain missing-condition as the controlled primary family and avoid universal claims | 8/10 |
| [Liu et al., *Lost in the Middle*](https://doi.org/10.1162/tacl_a_00638) | 2024, TACL, peer-reviewed | Whether long-context models use relevant information equally across positions; multi-document QA and key-value retrieval | Controlled placement of relevant information across context positions | Performance is often best near the beginning or end and worse in the middle | Retrieval/QA tasks are not software-engineering agents; does not test compaction | Establishes context position as an alternative mechanism for constraint loss | Fix no-compaction primary condition and record context position/size metadata | Motivates warnings when context state is unknown | Keep as a validity control, not a new causal treatment | 9/10 |
| [Deng et al., *AgentPro: Enhancing LLM Agents with Automated Process Supervision*](https://doi.org/10.18653/v1/2025.emnlp-main.506) | 2025, EMNLP, peer-reviewed | Whether automated step-level supervision improves agents; FEVER, HotpotQA, ALFWorld, and WebShop | MCTS labels intermediate steps by whether a continuation reaches the ground-truth answer; a process reward model guides rejection-sampling training; three seeds | Reported gains include 6.32 percentage points on HotpotQA and improvements on all four benchmarks | Requires expensive full-parameter training and extra inference; domains are not SE; step labels depend on terminal ground truth | Strong comparator for process-level evidence, but not proof that pre-final signals are independently predictive | Treat any outcome-derived process label as label-plane data; never use it as a T1–T3 feature in H2 | Process scoring may become a future remediation component after independent validation | Add an explicit process-supervision circularity boundary; do not add PRM training before the pilot | 8/10 |
| [Rondon et al., *Evaluating Agent-Based Program Repair at Google*](https://doi.org/10.1109/ICSE-SEIP66354.2025.00038) | 2025, ICSE-SEIP, peer-reviewed | Whether an agent can repair enterprise bugs; published program reports 182 bugs, including 82 human- and 100 machine-reported bugs | Passerine agent, 20 trajectory samples per bug, test-based plausibility plus manual semantic-equivalence review | Plausible and semantically equivalent rates differ sharply by bug source; multiple trajectories expose stochastic opportunity | Industrial internal environment limits replication; program-repair outcomes differ from acceptance criteria | Supports external-validity caution and stochastic agent evaluation | Preserve replication IDs, repeated runs, and semantic review beyond terminal pass/fail | Supports cost-aware best-of-N only as a product experiment, not thesis evidence | Keep five repetitions in the pre-pilot and report provider cost per episode | 8/10 |
| [Zerhoudi et al., *The Compaction Cliff in Long-Running AI Agent Memory*](https://arxiv.org/abs/2608.22752) | 2026, arXiv preprint | Whether repeated context compaction preserves constraints in long-running agents | Cross-model compaction experiments and typed-memory mechanisms | Reports steep rule-survival loss under repeated compaction and proposes typed preservation | Not independently peer-reviewed; recent; mechanism and reported magnitudes need replication | Motivates a secondary mechanism, not a replacement hypothesis | Atomic obligations, compaction telemetry, and the separate interaction test | Typed hard lanes may improve a future integrity gate | Retain as secondary stress-test motivation only | 6/10 |
| [Motger et al., *Characterizing Datasets for LLM-based Requirements Engineering*](https://arxiv.org/abs/2510.18787) | 2026, systematic mapping preprint | How public LLM4RE datasets differ in provenance, accessibility, reuse, and RE descriptors; 62 datasets from 45 primary studies | Systematic mapping with a public catalogue and extraction scheme | Licensing, availability, granularity, labels, and domain are necessary selection descriptors; accessibility changes over time | Preprint; scope is public LLM4RE datasets rather than controlled agent episodes; dataset documentation can be incomplete | Supports transparent corpus provenance without changing the causal claim | Require an immutable source revision reference in addition to source URL, rights review, hashes, and project ID | A reusable integrity gate can expose source lineage and reuse constraints | Upgrade corpus intake to require `source_revision_url` and `source_revision_id` | 6/10 |
| [Koo et al., *Benchmarking Cognitive Biases in Large Language Models as Evaluators*](https://doi.org/10.18653/v1/2024.findings-acl.29) | 2024, Findings of ACL, peer-reviewed | Whether LLM evaluators exhibit cognitive biases; preference rankings from 16 LLMs across four size ranges | CoBBLer probes six biases, including egocentric preference for a model's own output, and compares machine with human rankings | Bias indicators appeared in about 40% of model comparisons; average human-machine rank-biased overlap was 44% | Text-quality ranking is not acceptance-criterion coverage; findings do not estimate bias for OpenAI or DeepSeek configurations used here; pairwise ranking differs from the single-artifact rubric | Supports the existing rule that LLM judgments are exploratory label-plane evidence only | Record and stratify every exploratory judgment as self or cross; never pool the two relations silently | Enables bias-aware diagnostics before human review, but cannot replace human annotation | Add fail-visible self/cross relation telemetry to private evidence and redacted reports | 8/10 |
| [Ahmed et al., *Can LLMs Replace Manual Annotation of Software Engineering Artifacts?*](https://doi.org/10.1109/MSR66628.2025.00086) | 2025, MSR, peer-reviewed Distinguished Paper | When LLM ratings can safely replace some human annotation; six LLMs, ten tasks, and five prior SE datasets | Compares human-human, human-model, and model-model agreement; evaluates confidence-based selective delegation | Model-model agreement predicts human-model agreement at task level, but no confidence threshold allowed complete human replacement across the studied tasks | Discrete labels, no free-form annotation, possible repository contamination, and no analysis of model bias or demographics | Supports keeping machine judgments outside confirmatory ground truth | Treat model-model agreement as a feasibility diagnostic; require blinded human calibration before any mixed human-LLM delegation | May reduce future annotation cost only after task-specific calibration | Preserve full human annotation for H1/H2; add a no-delegation boundary until human-model calibration exists | 9/10 |
| [Cho et al., *Metamorphic Testing of Large Language Models for Natural Language Processing*](https://doi.org/10.1109/ICSME64153.2025.00025) | 2025, ICSME research track, peer-reviewed | Whether metamorphic relations expose faulty LLM behavior without a label for every input; published metadata reports 38 relations, four models, and about 550,000 tests | Systematic search for NLP relations; automated source/follow-up execution; accessible author manuscript implements 36 relations on four tasks and manually classifies 967 violations | The manuscript reports an 18% mean violation rate and 62% true positives in the inspected violations; metamorphic and labeled oracles detect complementary failures | Natural-language transformations and semantic comparisons create substantial false positives; no requirements task; input transformation/model dependence; final metadata and accessible manuscript differ in experiment counts | Supports metamorphic checks as an auxiliary oracle, not confirmatory semantic ground truth | Use constructed relations to triage cases for later human review; keep results outside H1/H2 labels and report transformation validity separately | Supports CI regression triage when prompt/model changes increase relation violations | Preserve the annotation-free boundary and prioritize human review of violations rather than treating them as labels | 8/10: peer-reviewed, large study and released artifacts; transfer and manuscript-version mismatch limit certainty |
| [Lee et al., *Are LLM-Judges Robust to Expressions of Uncertainty?*](https://doi.org/10.18653/v1/2025.naacl-long.452) | 2025, NAACL long paper, peer-reviewed | Evaluator robustness; EMBER has 2,000 QA and 823 instruction-following instances | Five judges; marker perturbations, human filtering, accuracy and verdict switches | Judgments change under epistemic markers | English text; QA/instruction following, not requirement semantics | Separate evaluator artifacts from degradation | Add synthetic correctness and invariance controls; do not assume hedges preserve requirements | Uncalibrated judgments need review | Implement isolated judge controls; preserve H1/H2 | 8/10: peer-reviewed, public benchmark and explicit methods; task transfer limited |
| [Van der Meer et al., *Annotator-Centric Active Learning for Subjective NLP Tasks*](https://doi.org/10.18653/v1/2024.emnlp-main.1031) | 2024, EMNLP, peer-reviewed | Whether joint sample/annotator selection can reduce labeling effort while preserving diverse judgments; seven tasks from DICES, MFTC, and MHS | Simulated active learning comparing random/uncertainty sample selection and four annotator-selection strategies across three splits and model initializations | Annotation reductions ranged from negligible to about 60%; the clearest ACAL advantage over ordinary active learning occurred with DICES' large annotator pool, and no strategy dominated all metrics/tasks | Simulated rather than live annotation; subjective social NLP rather than requirements; benefits depend on task disagreement, annotation history, and a sufficiently large diverse annotator pool | Supports preserving annotator variation and avoiding a single aggregated machine label | Freeze a random, project-stratified calibration sample before any signal-enriched queue; do not extrapolate active-learning savings with zero annotators | Supports a later review-prioritization workflow, but not automated semantic approval | Implement disjoint probability-audit and diagnostic-triage queues with private signals and explicit interpretation limits | 8/10: peer-reviewed, detailed methods/data and released software; domain transfer and simulated selection limit direct applicability |

## 2026-09-09 incorporation decision: freeze probability audit before triage

Van der Meer et al. show that targeted selection can save annotations in some
settings, but also that the gains are task- and annotator-pool-dependent. Their
result cannot be used to forecast savings for requirement evaluation with no
available annotators. The transferable design principle is narrower: preserve
an outcome-independent probability sample before selecting difficult cases.

Decision: add a private, hash-bound queue freezer. It allocates at least one
calibration item per project-like stratum, records each selected item's inclusion
probability, and reads machine signals only after the calibration sample is
fixed. The disjoint diagnostic queue is balanced across strata and may use
disagreement, abstention, invalid evidence, metamorphic violations, and incomplete
traces. Signal fields never enter annotator-visible packets. Neither queue
supplies H1/H2 labels or replaces double annotation/adjudication. Search and
reading date: 2026-09-09; abstract, method, datasets, main results, convergence,
limitations, and ethical considerations reviewed.

## 2026-09-10 incorporation decision: specify the annotation hand-off before recruitment

Peng et al. make annotation requirements explicit at two levels: strategic
agreement about objectives, scope, legal constraints, tools, quality assurance
and governance; and atomic scenario rules with a trigger, context, response,
rationale and acceptance criterion. Their evaluation is preliminary. It maps
artifact fields to an automotive error catalogue but does not observe fewer
errors, stronger agreement or lower cost in a deployed annotation study.

Decision: add a fail-closed annotation-study charter that binds the frozen rubric
and private queue manifest, requires two distinct primary annotators and a
separate adjudicator, records rehearsal on excluded material, and specifies
standard, edge-case and exception handling. The candidate remains blocked until
people and governance evidence exist. Passing validates declared process evidence
only; it neither creates H1/H2 labels nor demonstrates reviewer competence.
Search and reading date: 2026-09-10; abstract, related work, artifact fields,
demonstration, error mapping, discussion, threats and limitations reviewed.

## 2026-09-08 incorporation decision: metamorphic triage is not annotation

Cho et al. directly address the oracle problem that currently blocks this project,
but their manual inspection also shows why metamorphic violations cannot become
confirmatory labels. In the accessible manuscript, 38% of inspected violations
were false positives, most often because the input transformation or semantic
output comparison did not preserve the intended relation. Repeated violations do
not solve this: transformation errors were often stable across reruns.

Decision: retain the constructed clean/defective and source-based relations as an
annotation-free diagnostic track. Use violations to prioritize the eventual human
annotation queue and to detect regressions across frozen provider configurations;
do not use them as H1/H2 ground truth, calibration labels, or feature-plane input.
Record transformation validity and output-relation validity separately whenever a
human review becomes available. Search and reading date: 2026-09-08; abstract,
method, results, discussion, flakiness analysis, and threats to validity reviewed.

## 2026-09-07 incorporation decision: artifact-addressed evidence

The [attribution research note](2026-09-07-evidence-attribution.md) records full
metadata, reading scope, limitations, and downstream design. DOI/title checks
found no earlier ALCE or AIS entry in this matrix.

| Source | Contribution | Limit on transfer | Decision | Credibility |
| --- | --- | --- | --- | --- |
| [Gao et al., ALCE, EMNLP 2023](https://doi.org/10.18653/v1/2023.emnlp-main.398) | Separates citation support/relevance from answer correctness | NLI metrics have partial-support limits; requirements are untested | Keep locator integrity separate from semantic validity; do not add an uncalibrated NLI judge | 8/10 |
| [Rashkin et al., AIS, Computational Linguistics 2023](https://doi.org/10.1162/coli_a_00486) | Human attribution framework with explicit interpretation and source-support steps | Ambiguity and imperfect reference data remain; not a requirements calibration | Report unresolved semantics separately; preserve independent-label requirements | 9/10 |
| [W3C Web Annotation Data Model, 2017](https://www.w3.org/TR/annotation-model/#selectors) | Version-sensitive span selection | A locator is not a support judgment | Bind exact UTF-8 ranges to artifact identity; no W3C-conformance claim | Normative standard, not empirical validation |

The [offline design](../superpowers/specs/2026-09-07-evidence-addressing-design.md)
responds to observed quote failures. It does not change old scoring rules,
release the locked evaluation cases, or authorize provider spending.

## 2026-09-07 incorporation decision: uncertainty without invented calibration

| Source | Year / venue / status | Question and data | Method | Main result | Limitations and threats | Thesis relevance | Experiment relevance | Product relevance | Concrete action | Credibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [Sheng et al., *Analyzing Uncertainty of LLM-as-a-Judge: Interval Evaluations with Conformal Prediction*](https://doi.org/10.18653/v1/2025.emnlp-main.569) | 2025, EMNLP, peer-reviewed | Rating uncertainty; SummEval (1,600), DialSumm (1,400), four ROSCOE tasks (~200 each) | Three primary judges; token-logit conformal methods; ordinal adjustment; 50/50 calibration/test splits over 30 seeds | Adjustment generally improves coverage | Requires reference labels and exchangeability; task/domain transfer is limited | No annotation-free calibration claim | Keep missing-data bounds distinct from statistical intervals | Defer calibrated delegation | Document the calibration dependency; implement separate missing-stage accounting, not their algorithm | 8/10: peer-reviewed, explicit methods and appendices; no requirements evaluation |

Search and reading: 2026-09-07; abstract, Sections 3–4, limitations/ethics and
Appendix A.6 reviewed. DOI/title checked against main and the open pilot branch.
The source changes the uncertainty-claim boundary, not H1/H2 or the taxonomy.
Our independent engineering action in [temporal-warning protocol](temporal-warning-protocol.md)
retains partial-observation costs and computes deterministic completion bounds
conditional on supplied labels. It does not create human annotations or correct
systematic errors in machine labels. Existing frozen runs are not re-scored or
re-authorized automatically.

## 2026-09-06 incorporation decision

### Source-based pilot controls

[Ribeiro et al., *Beyond Accuracy: Behavioral Testing of NLP Models with
CheckList*](https://aclanthology.org/2020.acl-main.442/), ACL 2020,
DOI 10.18653/v1/2020.acl-main.442. Read the abstract, test-type method and
task/user-study results. Minimum-functionality, invariance and directional tests
expose failures hidden by aggregate scores in sentiment, duplicate-question
detection and machine comprehension. Those tasks are not requirements evaluation;
the selected capabilities and perturbation validity remain task-dependent.
Credibility: 9/10 for the peer-reviewed, explicit method and multi-task evidence;
transfer to this thesis is a design inference, not demonstrated validity.

Action: [source-based pilot protocol](source-based-pilot-protocol.md), including
matched omission controls, concise/expanded and distributed-condition invariance,
separate partial-visibility diagnostics, source-seed denominators and a frozen
pre-collection decision rule. The paper supplies no numerical acceptance cutoff
for our pilot. Private source text and oracles are not published in this matrix.

### Annotation-free boundary

With zero available human annotators, implement the bounded diagnostic track in
[annotation-free evaluation](annotation-free-evaluation.md). Constructed controls
can falsify simplistic evaluator behavior without certifying natural-language
labels. The primary hypotheses, human-label gate and feature/label separation
remain unchanged. Source search and method/results/limitations review: 2026-09-06.

## 2026-09-02 incorporation decision

AgentPro makes process supervision a closer comparator than generic
observability, but its step labels are generated using reachability of the
terminal ground-truth answer. That is useful for training an agent and
ineligible as deployable early-warning evidence in this thesis. H2 therefore
continues to use only runtime-native, pre-final T1–T3 observations; outcome-
derived process labels remain in the label plane. This strengthens the leakage
boundary without changing H1, H2, the smell taxonomy, or the pre-pilot design.

## 2026-09-03 incorporation decision

Motger et al. treat provenance, accessibility, licensing, granularity, and reuse
as first-class descriptors and warn that availability is time-dependent. The
pre-pilot intake therefore now requires an immutable source revision URL and
revision ID. This is an admission/reproducibility control only: it does not
admit any candidate, change H1/H2, or establish legal rights.


## 2026-09-04 incorporation decision

Koo et al. show that evaluator/generator dependence is a measurable validity
risk rather than a harmless implementation detail. The exploratory pre-pilot
therefore records each successful judge call as either `self` or `cross`,
publishes redacted counts and label distributions by relation, and reports
relation-specific failures. These diagnostics remain non-confirmatory and in
the label plane. They do not alter H1, H2, the smell taxonomy, or the primacy of
blinded human annotation.


## 2026-09-05 incorporation decision

Ahmed et al. provide evidence that agreement between strong models can help
screen whether an annotation task may be suitable for mixed human-LLM work.
They also report that no confidence cutoff supported replacing all humans
across their tasks. Therefore, model-model agreement in this project remains a
non-confirmatory feasibility diagnostic. It cannot establish label quality,
artifact correctness, or annotator reliability. H1/H2 continue to require the
frozen blinded human-annotation protocol; any future delegation to an LLM
requires a separate human-model calibration study defined before labels are
inspected.


## 2026-09-11: executable behavioral evidence

Problem: an incomplete requirement may cause generated code to violate a necessary condition of the intended behavior. This is a testable risk, not a claim that every smell causes a bug. The existing behavioral discovery adapter executes hidden tests and distinguishes target-condition failures, unrelated failures, crashes, timeouts and unexecuted artifacts.

The behavioral extension remains secondary/discovery-only; acceptance criteria remain the registered primary task. Before real-provider collection, freeze the complete intended behavior and the same hidden oracle for both variants, including target and non-target cases. Review oracle adequacy and mutation validity independently. Never derive the oracle solely from the defective prompt or expose it to generation or T1–T3 features. Report failed execution separately from demonstrated behavioral violations; test passage establishes only tested behavior. Preserve every repetition's code, report, identity and hash. Compare paired target-violation frequencies with project-level inference after the analysis is registered. No real-provider result or causal effect is claimed by an offline stub run.

Without annotators, executable fixtures can validate the measurement pipeline and expose concrete counterexamples to specified behavior. They do not establish that the specified oracle is correct, replace human review, or promote synthetic outcomes to H1/H2 evidence. Product use remains advisory: show the condition, failing input, expected/actual output and trace, with no automatic semantic approval.

Source revisited: Mu et al., ClarifyGPT (FSE 2024), DOI https://doi.org/10.1145/3660810; accessible author manuscript https://arxiv.org/html/2310.10996v1 (2023 version). Read method, evaluation and limitations. Ten participants evaluated clarification on two MBPP benchmarks; automated experiments use two models and four benchmarks. The manuscript reports GPT-4 Pass@1 increasing from 70.96% to 80.80% on MBPP-sanitized. Its intervention is clarification, not our controlled missing-condition treatment. Simulated feedback explicitly receives ground-truth tests (Section 5.2); importing that design into oracle-free H2 would leak terminal knowledge. Benchmark simplicity, model dependence and simulated feedback limit transfer. Credibility: 8/10, peer-reviewed publication and transparent author method, but task and version boundaries matter. Thesis: motivate behavioral consequences. Experiment: keep hidden tests outside generation and feature planes. Product: clarification is a separate intervention requiring evaluation. Action: preserve replication-specific evidence before live qualification, without changing H1/H2.

Attribution correction: the disjoint probability-audit and diagnostic queues above are this thesis's sampling decision, not a procedure evaluated by Van der Meer et al. Their study motivates attention to annotation scarcity but does not validate our queue design.

## 2026-09-12 — Oracle validity before execution

Search/read date: 2026-09-12. New entry; deduplicated by title and DOI.

| Source / evidence | Question, data and method | Finding and limitations | Thesis / experiment / product action | Credibility |
| --- | --- | --- | --- | --- |
| Barr, Harman, McMinn, Shahbaz and Yoo, *The Oracle Problem in Software Testing: A Survey*, TSE 41(5), 507–525 (2015), peer-reviewed; [DOI](https://doi.org/10.1109/TSE.2014.2372785), [author manuscript](https://philmcminn.com/publications/barr2015.pdf) | How can tests distinguish intended behavior? Survey repository of 694 publications from 1978–2012; search, classification and trend analysis. Read abstract, definitions, search method, specified-oracle challenges and conclusion. | Distinguishes partial oracles from ground truth; abstraction can omit relevant behavior or admit infeasible behavior. Traditional-testing survey, not an LLM experiment or an effect-size estimate; search coverage and age limit transfer. | Thesis: separate oracle disagreement from source-supported error. Experiment: quarantine unresolved source-contract assumptions. Product: expose oracle uncertainty before calling a behavior faulty. These are our bounded implementation decisions, not evaluated interventions in the survey. | 8/10: peer-reviewed synthesis with explicit method and formal definitions; no direct validation of this task. |

Implementation decision: `eval.discovery --mode live` now fails before corpus loading,
provider initialization or artifact creation. This temporary quarantine covers the
combined ARTA discovery runner, including its acceptance-criteria oracles; it does
not disable other qualified runners or rewrite the confirmatory protocol. There
is no environment/CLI override. Reopening needs a reviewed corpus/oracle revision,
not merely credentials or a passing synthetic control. Offline bundles explicitly
record `blocked_semantic_review` and `fixture_pipeline_check_only`.

The new GAMMA-002 regression reproduces the historical oracle's unsupported
rejection of 1001 users. This is a counterexample to the oracle interpretation,
not evidence that a real model generated a defect. All 12 original pairs and
oracle hashes remain unchanged. Source-specific review decisions remain in
[the existing audit](behavior-oracle-review-20260911.md); no approval is fabricated.

Follow-through: the [revision candidate packet](oracle-revision-candidate-v1.md)
now covers all twelve source-contract decisions. Four executable partial-oracle
candidates retain only selected obligations and mark other points unspecified.
An eight-reference sensitivity comparison loses the historical contrast in
GAMMA-002 and ERTMS-002 while retaining it in NFR-002 and PEERING-001. This is our
constructed-reference result, not a result from Barr et al. or real LLMs. It shows
why an oracle's unsupported negative expectations can determine the apparent
effect. All interpretations remain pending independent review; unknown points
are not correct negatives, and no source-derived performance claim is made.

## 2026-09-13 — Executed statements can lack effective assertions

Search/read date: 2026-09-13; deduplicated by DOI/title. Read abstract, method, results and threats.

| Source / evidence | Question, data and method | Finding and limitations | Thesis / experiment / product action | Credibility |
| --- | --- | --- | --- | --- |
| Maton, Kapfhammer and McMinn, *Where Tests Fall Short: Empirically Analyzing Oracle Gaps in Covered Code*, ESEM 2025, peer-reviewed; [DOI](https://doi.org/10.1109/ESEM64174.2025.00063), [author manuscript](https://philmcminn.com/publications/maton2025.pdf) | Which executed statements lack effective oracle checks? Thirty Java classes from six projects; three oracle-gap approaches, manual classification and PIT mutation analysis. | Coverage can coexist with oracle gaps. Results depend on selected Java classes, implementations and mutants; mutation score is an imperfect proxy for test quality. | Thesis: execution does not establish behavioral correctness. Experiment: review explicit assertions against each scored constraint; keep unspecified points unscored. Product: display the checked obligation and observed mismatch. This is a bounded application, not evidence about LLMs or our mutation's validity. | 8/10: peer-reviewed comparative method and replication artifacts; restricted sample and construct validity limit transfer. |

Action: retain the draft packet's separation of generation and review material, and require reviewers to inspect the actual input/expected-decision mapping. Passing infrastructure controls alone cannot admit these drafts. No additional coverage or mutation framework is needed for the present two Boolean decision abstractions.

## 2026-09-13 — Crash persistence is distinct from process exclusion

Search/read date: 2026-09-13; title deduplicated. Read abstract, method, results and limitations.

| Reference / evidence | Question, sample and method | Result / limitations | Thesis / experiment / product relevance and action | Credibility |
| --- | --- | --- | --- | --- |
| Pillai et al., *All File Systems Are Not Created Equal: On the Complexity of Crafting Crash-Consistent Applications*, OSDI 2014, peer-reviewed; [original paper](https://www.usenix.org/system/files/conference/osdi14/osdi14-paper-pillai.pdf) | How do persistence assumptions affect crash consistency? BOB examines six Linux file systems; ALICE examines eleven applications using workloads, invariant checkers and abstract persistence models. | Sixty crash vulnerabilities; persistence varies with filesystem/configuration. Exploration is incomplete, workloads/checkers are supplied, threaded calls are serialized and file attributes are not handled. Older systems limit transfer. | Thesis: infrastructure evidence only, no H1/H2 support. Experiment: flush the run directory and ancestor chain before runner entry, including preflight recovery; inject flush failures. Product: distinguish writer exclusion from durable recovery. Tests do not qualify actual power-loss behavior; storage qualification remains required. | 8/10: peer-reviewed, explicit method and limitations; workload/model coverage and deployment age constrain applicability. |

## 2026-09-14 — Durable completion is separate from retry

Search/read date: 2026-09-14; title deduplicated. Read abstract, design,
experimental setup, results, discussion and artifact limitations.

| Reference / evidence | Question, sample and method | Result / limitations | Thesis / experiment / product relevance and action | Credibility |
| --- | --- | --- | --- | --- |
| Zhang, Cardoza, Chen, Angel and Liu, *Fault-tolerant and Transactional Stateful Serverless Workflows*, OSDI 2020, peer-reviewed; [paper](https://www.usenix.org/system/files/osdi20-zhang_haoran.pdf), [venue page](https://www.usenix.org/conference/osdi20/presentation/zhang-haoran) | How can stateful serverless workflows tolerate worker crashes and provide transactions? Beldi atomically logs operations and re-executes unfinished functions. The prototype comprises 1,823 lines of Go and evaluates three DeathStarBench-derived applications on AWS Lambda/DynamoDB, including up to 1,000 Lambdas. | Logging plus re-execution provides the evaluated workflow semantics; at saturation the paper reports 2.4--3.3x median and 1.2--1.8x p99 latency increases versus its baseline. Results assume strongly consistent fault-tolerant storage and Beldi's runtime; three applications, cloud-specific deployment and no qualification of our filesystem limit transfer. | Thesis: infrastructure only, no H1/H2 support. Experiment: represent semantic completion separately from provider-call completion; resume only from bound immutable receipts. Product: expose recovery state and unresolved remote ambiguity. Action: add per-judge and consolidated receipts, restore judging without duplicate fixture calls, and retain fail-closed ambiguous-call handling. This is an engineering inference, not adoption of Beldi's distributed guarantee. | 8/10: peer-reviewed top systems venue, explicit protocols, implementation, evaluation and artifact; assumptions and domain differ materially from this single-host harness. |

## 2026-09-14 — Bounded crash testing of persistence points

Search/read date: 2026-09-14; title deduplicated. Read abstract, design,
bug-study construction, evaluation, discussion and limitations.

| Reference / evidence | Question, sample and method | Result / limitations | Thesis / experiment / product relevance and action | Credibility |
| --- | --- | --- | --- | --- |
| Mohan, Martinez, Ponnapalli, Raju and Chidambaram, *Finding Crash-Consistency Bugs with Bounded Black-Box Crash Testing*, OSDI 2018, peer-reviewed; [paper](https://www.usenix.org/system/files/osdi18-mohan.pdf), [venue page](https://www.usenix.org/conference/osdi18/presentation/mohan) | Can bounded black-box testing expose filesystem crash-consistency defects? The authors study 26 reported bugs across three filesystems and seven kernel versions, then combine CrashMonkey record/replay with ACE-generated workloads and persistence-point crashes. | The evaluation reproduced 24 of 26 reported bugs and found ten new bugs. Most studied bugs were reachable with at most three filesystem operations. The bound is empirical rather than exhaustive; resource-exhaustion and long-sequence defects can be missed, and filesystem-level results do not qualify an application runtime or storage deployment. | Thesis: infrastructure evidence only, no H1/H2 support. Experiment: treat report publication as a separate persistence point after provider and judge completion. Product: expose `finalizing` instead of claiming completion before reports exist. Action: inject failure during the final report commit, resume from receipts, and verify zero duplicate fixture calls. This is a bounded engineering application, not a real power-loss test. | 9/10: peer-reviewed top systems venue, explicit bug corpus, method, implementation and evaluation; bounded coverage and domain transfer remain material. |

## 2026-09-15 — Agreement is necessary but does not establish validity

Search/read date: 2026-09-15; deduplicated by DOI/title. Read the abstract,
coefficient assumptions, worked examples, annotation-task review and conclusion.

| Reference / evidence | Question, sample and method | Result / limitations | Thesis / experiment / product relevance and action | Credibility |
| --- | --- | --- | --- | --- |
| Artstein and Poesio, *Inter-Coder Agreement for Computational Linguistics*, Computational Linguistics 34(4), 555–596 (2008), peer-reviewed survey; [DOI](https://doi.org/10.1162/coli.07-034-R2), [ACL Anthology](https://aclanthology.org/J08-4004/) | Which agreement coefficients fit corpus annotation, and what assumptions do they make? Mathematical survey of observed/chance-corrected agreement, including Cohen's kappa, Scott's pi and Krippendorff's alpha, plus prior computational-linguistics annotation studies. | Reliability is a prerequisite for a defensible coding scheme, but agreement cannot establish validity because coders can share the same systematic error. Coefficients differ in chance and coder-bias assumptions; category skew and weighted distances complicate interpretation. This is a methodological survey, not an evaluation of requirements, generated code, or this rubric. | Thesis: keep human-label reliability separate from semantic validity and H1/H2. Experiment: preserve independent responses before adjudication and select/report a coefficient only after matching its assumptions to the frozen scale and missing-data pattern. Product: disagreement may prioritize review but cannot approve semantics. Action: verify exported packets and immutably bind each returned response to its exact form/receipt; do not aggregate or adjudicate in the intake step. | 9/10: peer-reviewed journal survey with explicit mathematics, assumptions and task examples; direct for annotation methodology but indirect for this domain. |

## 2026-09-16 — Generated tests are not a stable cross-variant oracle

Search/read date: 2026-09-16; new source, deduplicated by arXiv identifier.
Read abstract, method, results, discussion, threats and artifact statement.

| Reference / evidence | Question, sample and method | Result / limitations | Thesis / experiment / product relevance and action | Credibility |
| --- | --- | --- | --- | --- |
| Haroon, Khan and Gulzar, *Evaluating LLM-Based Test Generation Under Software Evolution*, arXiv:2603.23443v1 (2026), preprint; [paper](https://arxiv.org/html/2603.23443), [artifact](https://doi.org/10.5281/zenodo.18898624) | Do generated tests adapt to semantic-altering changes and remain stable under semantic-preserving changes? Mutation-driven evaluation of eight models on 22,374 Java/Python program variants; only baselines with fully passing generated suites are retained, then new suites are generated for changed programs. | Baselines average 79.2% line and 76.1% branch coverage. Under semantic-altering changes, test pass rate falls to 66.5%; 23,737 of 23,977 failing tests pass on the original while covering the changed region. Semantic-preserving changes also reduce pass rate to 79% and branch coverage to 69%. The study uses algorithmic, self-contained programs, generated code mutations and coverage/pass metrics; it does not evaluate requirements, repository E2E behavior, developer intent, or our causal treatment. Baseline success filtering, nondeterminism and possible benchmark contamination constrain interpretation. | Thesis: no direct H1/H2 support. Experiment: never regenerate the outcome oracle per clean/smelly arm; generate candidate tests from the complete canonical requirement before assignment, independently review and freeze them, then execute the identical suite on every arm. Add meaning-preserving controls and a mutation-killing admission check. Product: show executed evidence and oracle provenance; LLM judges remain diagnostic. Action: implement `repository-e2e-case/v1` admission and screen four UI/API repositories without admitting them. | 7/10: large, transparent preprint with released artifact and explicit threats, but not peer-reviewed and indirect for requirement-to-code E2E causality. |
| Wang et al., *ReCode: Robustness Evaluation of Code Generation Models*, ACL 2023 long paper, peer-reviewed; [paper](https://aclanthology.org/2023.acl-long.773/), [artifact](https://github.com/amazon-science/recode) | How robust are code generators to natural, semantics-preserving prompt and code transformations? More than 30 transformations over HumanEval, MBPP and derived function-completion tasks; CodeGen, InCoder and GPT-J are evaluated with execution-based robust pass/drop/relative metrics. Five randomized datasets per transformation are used for worst-case aggregation; human review checks semantic preservation. | Human annotators judged over 90% of perturbed prompts meaning-preserving. Models still show substantial robustness drops; syntax transformations are most disruptive. The study covers Python function completion and older model families, not repository E2E tasks, requirement smells, causal treatment isolation or current agents. Its control transformations therefore motivate a baseline for wording sensitivity, not an expected effect size for this thesis. | Thesis: separates instability under equivalent phrasing from loss caused by a defective requirement. Experiment: require a distinct, independently reviewed rewrite-control arm; bind clean, rewrite-control and smelly text hashes; hold scaffold and oracle fixed across them; interpret smelly versus complete together with rewrite-control versus complete. Product: a detector must not call every wording-sensitive output a requirement-smell defect. Action: harden `repository-e2e-case/v1` before any case is admitted. | 9/10: peer-reviewed ACL long paper with released code/data, human checks and explicit metrics; domain and model-age transfer limits remain material. |

## 2026-09-17 — Equivalent wording can change generated code and correctness

Search/read date: 2026-09-17; deduplicated by DOI/title. Read abstract,
sampling and filtering, paraphrase review, generation procedure, evaluation,
results and stated oracle limitations.

| Reference / evidence | Question, sample and method | Result / limitations | Thesis / experiment / product relevance and action | Credibility |
| --- | --- | --- | --- | --- |
| Mastropaolo et al., *On the Robustness of Code Generation Techniques: An Empirical Study on GitHub Copilot*, ICSE 2023, peer-reviewed; [DOI](https://doi.org/10.1109/ICSE48619.2023.00181), [paper](https://arxiv.org/abs/2302.00438), [replication package](https://github.com/antonio-mastropaolo/robustness-copilot) | Do semantically equivalent natural-language descriptions change Copilot output? The study selects 892 Java methods from 33 repositories after build, JUnit, JaCoCo and at-least-75%-statement-coverage filters. It creates manual, PEGASUS and translation-pivot paraphrases, independently reviews automated paraphrases with two authors plus adjudication, invokes Copilot with full and truncated file context, and evaluates syntax, tests and code similarity. | Equivalent descriptions changed recommendations in about 46% of cases; the paper reports that correctness can change in about 28%. Only about 13% of the studied generations passed all associated tests. Tests remain partial oracles: the authors show behaviorally different methods that both pass, and high coverage does not establish semantic completeness. The sample is Java-method generation with an older Copilot version, not repository-level UI tasks or controlled requirement defects. | Thesis: wording sensitivity is a competing explanation, not evidence that a smell caused a defect. Experiment: retain the independently reviewed rewrite-control arm and one frozen executable oracle across complete, rewrite-control and smelly variants; never use output difference or LLM judgment alone as the label. Product: report executed behavioral obligations and distinguish wording instability from a missing-condition diagnosis. Action: keep TodoMVC's same-session Escape assertion frozen and require mutant-kill plus independent oracle review before admission. | 9/10: peer-reviewed ICSE paper with a released replication package, explicit sampling, human semantic checks and executable evaluation; partial-oracle, model-age and task-transfer limitations are material. |


## 2026-09-18 — Mutation kill qualifies an oracle, not a causal claim

Search/read date: 2026-09-18; new source, deduplicated by DOI/title. Read
the abstract, literature-repository method, mutation process, empirical trends,
practical limitations and conclusions.

| Reference / evidence | Question, sample and method | Result / limitations | Thesis / experiment / product relevance and action | Credibility |
| --- | --- | --- | --- | --- |
| Jia and Harman, *An Analysis and Survey of the Development of Mutation Testing*, IEEE Transactions on Software Engineering 37(5), 649–678 (2011), peer-reviewed; [DOI](https://doi.org/10.1109/TSE.2010.62), [author technical report](https://mutationtesting.uni.lu/TR-09-06.pdf) | How did mutation testing develop, what evidence and tools existed, and what limits practical use? The survey assembled more than 350 English-language publications from 1977–2009 by searching major publishers, following references and asking cited authors to check citations; it analyzes theory, cost reduction, tools, applications and empirical subjects. | Mutation analysis assesses a test set by executing seeded faults and observing whether behavior differs. The field showed increasing practical maturity, but equivalent mutants, human-oracle effort and computational cost remain material. Many empirical subjects were small laboratory programs, and some large-program studies used only a few operators. The paper predates modern browser applications and LLM code generation. | Thesis: no direct support for H1/H2. Experiment: retain gold-pass plus a targeted mutant-kill as an admission check for the frozen E2E oracle, while treating one killed mutant only as evidence that this specific observable obligation is exercised. Do not infer corpus validity, smell causality or external validity from mutation kill. Product: expose the seeded fault, unchanged oracle and execution receipt rather than a bare score. Action: require each gold/mutant arm to rebuild from its current source before the identical browser command runs. | 9/10: peer-reviewed TSE survey with an explicit search repository and broad technical synthesis; strong for mutation-testing method, but old and indirect for repository-level LLM experiments. |

## 2026-09-19 — Mutant coupling is substantial but incomplete

Search/read date: 2026-09-19; new source, deduplicated by DOI/title. Read the
abstract, study design, subjects, test-generation and coverage controls,
results, threats to validity and conclusion.

| Reference / evidence | Question, sample and method | Result / limitations | Thesis / experiment / product relevance and action | Credibility |
| --- | --- | --- | --- | --- |
| Just et al., *Are Mutants a Valid Substitute for Real Faults in Software Testing?*, FSE 2014, peer-reviewed; [DOI](https://doi.org/10.1145/2635868.2635929), [author paper](https://homes.cs.washington.edu/~rjust/publ/mutants_real_faults_fse_2014.pdf) | Do mutation scores predict real-fault detection and are real faults coupled to mutants? The study uses 357 real faults from five open-source Java programs (321 KLOC), 230,000 mutants, developer-written tests and 35,141 automatically generated suites while controlling for code coverage. | Mutation score correlates significantly with real-fault detection and more strongly than statement coverage. Mutants couple to 73% of real faults; 10% require stronger or new operators, while 17% are not coupled to any studied mutant. The subjects are Java programs and 2014 mutation operators, not browser applications, repository agents or requirement-smell treatments. | Thesis: no direct support for H1/H2. Experiment: retain targeted mutant-kill as an oracle-sensitivity admission check, but require actual clean/rewrite-control/smelly generated outputs under the same frozen oracle for causal evidence. A killed mutant must never become a scientific label. Product: present mutation evidence as diagnostic coverage, not semantic approval. Action: preserve TodoMVC's successful rehearsal while keeping independent mapping, manipulation, oracle and rights reviews blocking. | 9/10: peer-reviewed FSE study with a large controlled empirical design and transparent threats; strong for mutant/real-fault coupling, but indirect for browser E2E and LLM-generated code. |
| [van der Lee et al., *Best practices for the human evaluation of automatically generated text*](https://doi.org/10.18653/v1/W19-8643) | 2019, INLG, peer-reviewed proceedings | How human evaluation was conducted in 2018 NLG research and which practices improve consistency; 51 INLG and 38 ACL papers were reviewed | Bibliometric snapshot plus literature-grounded recommendations covering criteria, participants, design, agreement and analysis | Reporting was sparse: among papers with human evaluation, 55% reported participant count, 18% demographics, 12.5% inter-annotator agreement and 12.5% design details such as order or randomization; the authors recommend task-specific criteria, transparent participant reporting, pilots and analysis of disagreement | The sample is NLG-specific, mostly intrinsic evaluation and observational; recommendations are not causal validation of this thesis, repository E2E review or a four-role design | Supports keeping human semantic review explicit and criterion-specific without treating reviewer judgments as automatic labels | Give each repository reviewer only role-relevant evidence; require prior-exposure declaration, rationale and limitations; pilot the packet workflow before distribution. Do not infer that four identifiers prove expertise or sufficient sample size | Supports an auditable review workflow but not automated approval | Implement role-isolated, hash-bound mapping, manipulation, oracle and rights packets and keep reviewer competence/governance as human gates | 8/10: peer-reviewed venue, transparent sample and literature basis with explicit scope; strong evaluation guidance but indirect to requirements-to-code causality and not an experimental validation of these controls |


## 2026-09-21 — Complete, version-bound computational evidence

Search/read date: 2026-09-21; new source, deduplicated by DOI/title. Read the
publication type, motivation, all ten rules, examples, practical trade-offs and
scope limitations.

| Reference / evidence | Question, sample and method | Result / limitations | Thesis / experiment / product relevance and action | Credibility |
| --- | --- | --- | --- | --- |
| [Sandve et al., *Ten Simple Rules for Reproducible Computational Research*](https://doi.org/10.1371/journal.pcbi.1003285) | 2013, PLOS Computational Biology editorial. The authors synthesize practical reproducibility guidance for computational analyses: record the full executable workflow, exact program versions and parameters; version custom scripts; preserve intermediate and raw results; record randomness; and link claims to underlying evidence. | The paper argues that these habits make self- and peer-reproduction practical and identifies time/cost trade-offs. It is methodological guidance, not an empirical comparison, security standard or validation of this experiment; examples come primarily from computational biology. | Thesis: supports traceable claim-to-evidence custody but does not support H1/H2. Experiment: fail closed when the TodoMVC inventory contains unrecorded links or special files, bind raw responses and mutable outcomes to private durable files, and keep exact code/image/version bindings. Product: prefer inspectable receipts over summary-only scores. Action: harden the future collector without rewriting retained PR #60 evidence. | 7/10: reputable peer-reviewed journal venue and transparent, actionable scope, but an editorial without an empirical effectiveness study and indirect to LLM repository experiments. |

## 2026-09-22 — Generator/judge overlap requires a scoped sensitivity

Search/read date: 2026-09-22; new source, deduplicated by DOI/title. Read the
abstract, datasets/models, pairwise and individual measurements, results,
confounder controls, discussion and stated limitations.

| Reference / evidence | Question, sample and method | Result / limitations | Thesis / experiment / product relevance and action | Credibility |
| --- | --- | --- | --- | --- |
| Panickssery, Bowman and Feng, *LLM Evaluators Recognize and Favor Their Own Generations*, NeurIPS 2024 main conference, peer-reviewed; [proceedings and DOI](https://proceedings.neurips.cc/paper_files/paper/2024/hash/7f1f0218e45f5414c79c0679633e47bc-Abstract-Conference.html), [paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/7f1f0218e45f5414c79c0679633e47bc-Paper-Conference.pdf) | Can self-recognition contribute to an evaluator preferring its own output? The study samples 1,000 articles from each of XSUM and CNN/DailyMail, generates summaries with GPT-4, GPT-3.5 and Llama 2, and measures pairwise/individual self-recognition and preference. Fine-tuning and unrelated control tasks vary self-recognition to test correlation and alternative explanations. | The three models show nontrivial self-recognition and self-preference; GPT-4 reaches 73.5% self-recognition in one reported comparison, and self-recognition strength correlates with self-preference after fine-tuning. The authors present evidence rather than definitive causal validation. The task is summarization with older model families; generation quality is not fully ground-truth controlled, example-level causality is unresolved, and transfer to source-obligation classification is untested. | Thesis: no H1/H2 support. Experiment: retain every raw judge vote and the frozen three-judge primary analysis. Preserve the prespecified Astra/Terra-only sensitivity, but add a clearly supplementary generator-specific diagnostic that excludes a judge only for artifacts generated by the same model. For Luna, retain the 3/3 primary label; for Sol, require Astra/Terra agreement. Product: disclose model-role overlap rather than presenting panel consensus as independent human validation. | 9/10: peer-reviewed NeurIPS main-track paper with explicit datasets, model roles, controlled fine-tuning and released code; strong evidence for a plausible bias, but task/model transfer and causal limitations are material. |
