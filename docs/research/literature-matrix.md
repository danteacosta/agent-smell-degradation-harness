# Literature matrix

Last updated: 2026-10-06
Canonical policy: deduplicate by DOI, then by normalized title. A source enters this
matrix only after its abstract and the relevant method, results, and limitations
have been read. Product-only sources must not support scientific claims.

| Source | Year / venue / status | Question and data | Method | Main result | Limitations and threats | Thesis relevance | Experiment relevance | Product relevance | Concrete action | Credibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: |
| [Suriadi et al., *Event log imperfection patterns for process mining*](https://doi.org/10.1016/j.is.2016.07.011) | 2017, *Information Systems*, peer-reviewed | Which recurring defects in event logs warrant systematic checks? Eleven patterns distilled from process-mining practice; one case study and a researcher/practitioner questionnaire. The accessible publisher material does not give the questionnaire sample size. | Pattern catalogue, case-study application, and questionnaire on recognition, importance, and usefulness. | The authors demonstrate the patterns' use in a case study and report practitioner evaluation; this does not establish that all log errors are covered or that cleaning improves downstream agent prediction. | Domain is organizational process mining, not LLM-agent traces; pattern set is intentionally incomplete, and the accessible material does not expose enough questionnaire detail to assess sampling. | Trace quality is a prerequisite for interpreting T1–T3, not evidence for H1/H2. | Require unique event IDs and strictly increasing sequence numbers before a trace can supply confirmatory H2 features; preserve the separate checkpoint-order and hash checks. | A future diagnostic should distinguish invalid provenance from semantic requirement loss. | Add strict trace-identity/order regression tests to the feature manifest; do not turn log-quality checks into scientific labels. Search/read: 2026-09-29; abstract, publisher method/evaluation summary, and stated incompleteness reviewed. | 8/10: peer-reviewed journal article with case-study and practitioner evaluation; transfer is indirect and accessible sample details are limited. |
| [Frattini et al., *Applying bayesian data analysis for causal inference about requirements quality: a controlled experiment*](https://doi.org/10.1007/s10664-024-10582-1) | 2025 volume (published 22 November 2024), *Empirical Software Engineering*, peer-reviewed | Do passive voice and ambiguous pronouns affect downstream domain modeling? 25 university/industry participants modeled four natural-language requirements. | Randomized-order factorial crossover; evaluates missing/superfluous entities, missing/wrong associations and duration with frequentist and Bayesian analyses; records context factors and shares a replication package. | Ambiguous pronouns had a stronger effect, especially on wrong associations; passive voice had a minor effect. Domain knowledge may mitigate some errors, with substantial uncertainty. Effects vary by quality factor and measured attribute. | Four short requirements and a contrived domain-modeling task; volunteer sample, possible sequence/carryover effects, limited interaction power and unvalidated context measures. Neither LLM agents nor acceptance criteria were studied. | Supports an activity- and outcome-specific account of requirement quality; cannot establish H1/H2 or transfer its effect sizes to code generation. | Keep criteria, ordinal artifact severity and browser behavior distinct; freeze the endpoint and its unit before confirmatory sizing. Retain null and recovery cases instead of selecting only successful omissions. | Prioritize diagnoses by demonstrated downstream loss in a defined workflow, not a universal smell score. | Add an explicit endpoint decision gate to the existing research roadmap; seek advisor approval before promoting browser failure to a confirmatory endpoint. | 9/10: peer-reviewed controlled experiment with disclosed methods, data and replication package, but a small human domain-modeling sample limits transfer to agents. |
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

## 2026-09-23 — GUI oracle state must match the observation goal

Search/read date: 2026-09-23; new source, deduplicated by title. Read the
abstract, oracle model, experiment, results, threats and conclusion.

| Reference / evidence | Question, sample and method | Result / limitations | Thesis / experiment / product relevance and action | Credibility |
| --- | --- | --- | --- | --- |
| Memon, Banerjee and Nagarajan, *What Test Oracle Should I Use for Effective GUI Testing?*, ASE 2003, peer-reviewed; [author manuscript](https://www.cs.umd.edu/~atif/pubs/MemonASE2003.pdf) | How do GUI oracle information and comparison procedure affect fault detection and cost? The study defines 11 oracle types, seeds 100 faulty versions for each of four GUI systems, and executes 600 tests per version and oracle type, reporting 660,000 runs per subject system. | More detailed GUI state and stronger procedures generally detect faults earlier and with fewer tests, at greater storage and execution cost. The study uses seeded faults, four older desktop GUI systems and platform-specific state extraction; some faults may not manifest through the GUI, and timing varies. It does not evaluate web applications, LLM code generation or requirement smells. | Thesis: no H1/H2 support. Experiment: align oracle information with the user-level outcome rather than DOM existence. A restored but hidden todo cannot satisfy browser-visible persistence; preserve a separate unknown target when the prerequisite is unavailable. Product: show the exact visible state and event at which a violation was observed. Action: add a hidden-restoration mutant, require visible row/identity, and requalify the changed oracle bytes before admission. | 8/10: peer-reviewed ASE empirical study with explicit oracle taxonomy, four systems and large repeated execution; seeded faults, age and desktop-to-web transfer limit applicability. |

## 2026-09-24 — E2E assertions need explicit GUI identities and state relations

Search/read date: 2026-09-24; new source, deduplicated by DOI/title. Read the
abstract, approach, benchmark construction, test-script method, experiments,
results, data-availability statement, discussion and threats.

| Reference / evidence | Question, sample and method | Result / limitations | Thesis / experiment / product relevance and action | Credibility |
| --- | --- | --- | --- | --- |
| Teoh et al., *WebTestPilot: Agentic End-to-End Web Testing against Natural Language Specification by Inferring Oracles with Symbolized GUI Elements*, PACMSE 3 / FSE 2026, peer-reviewed; [DOI](https://doi.org/10.1145/3797115), [paper](https://arxiv.org/html/2602.11724v2), [artifact](https://github.com/code-philia/WebTestPilot) | Can a neurosymbolic agent derive reliable E2E actions and assertions from natural-language requirements? The authors package four mature web applications, curate 100 requirements from documentation plus CRUD extrapolation, implement sequential Playwright ground-truth assertions, and inject one reproducible bug per requirement. Bug categories come from open coding a 10% random sample of 2,043 closed issues by two authors with adjudication. Three agent baselines are compared; robustness varies requirement wording and model scale. | WebTestPilot reports 99% task completion and 96% precision/recall for injected-bug detection, plus 39/40 widget re-identifications under selected UI changes. Dropout, restyling and summarization reduce task completion for several models. Ground truth can underestimate alternative valid paths; the benchmark contains seeded JavaScript faults and partially extrapolated requirements, and four applications cannot establish broad external validity. The industrial case reports eight discovered bugs but does not provide a controlled false-negative denominator. It does not study requirement smells, generated implementations or causal clean/rewrite/smelly pairs. | Thesis: supports the feasibility of requirement-relative, user-interface evidence but not H1/H2. Experiment: keep independent frozen assertions as the label plane; bind each GUI role to an explicit identity and evaluate temporal pre/postconditions rather than raw DOM existence. Do not replace the oracle with the generator or an LLM judge. Product: symbolized state and dependency traces are a plausible diagnostic interface, still requiring human validation. Action: define the Mark all master as the exact visible `#toggle-all`, treat hidden/removed state consistently at the user-visible endpoint, add replacement/duplicate controls and version the changed report schema. | 9/10: peer-reviewed FSE/PACMSE study with explicit benchmark construction, multiple baselines, robustness analysis and released code/data; seeded bugs, curated requirements and limited application diversity remain material transfer threats. |

## 2026-09-25 — Repository holdout and benchmark validity

Search/read date: 2026-09-25. New sources, deduplicated by title; read the
abstract, construction, evaluation, limitations and, for Verified, annotation
rubric summary and results. Neither source supplies H1/H2 evidence.

| Reference / evidence | Question, sample and method | Result / limitations | Thesis / experiment / product relevance and action | Credibility |
| --- | --- | --- | --- | --- |
| Jimenez et al., *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?*, ICLR 2024, peer-reviewed; [conference paper](https://proceedings.iclr.cc/paper_files/paper/2024/file/edac78c3e300629acfe6cbe9ca88fb84-Paper-Conference.pdf) | How do language models resolve repository-level issues? Construct 2,294 issue/PR/test instances from 12 Python repositories using fail-to-pass execution filtering; evaluate generated patches against associated tests. SWE-Llama training examples come from 37 repositories disjoint from the evaluation repositories. | The original best evaluated setup resolved 1.96% of cases. The authors explicitly limit transfer beyond Python and state that execution-only tests do not guarantee reliable or comprehensive solutions; later model performance should not be inferred from the historical baseline. Disjoint training repositories reduce one measured contamination route but cannot establish absence of pretrained-model exposure. | Thesis: repository-level benchmark context, not causal evidence about requirement smells or temporal provenance. Experiment: a project-disjoint partition must remain disjoint when a frozen manifest is **applied**, not only when constructed; enforce project and source-intent exclusivity, unique rows and the recorded assignment hash at the H2 input boundary. This code safeguard follows from the study design's grouping invariant, not from an estimated effect in SWE-bench. Product: benchmark pass rate alone is not proof of correct requirement preservation. | 9/10: reviewed ICLR paper with large publicly specified construction, released data/code and explicit limitations; Python-only and test-oracle validity constrain transfer. |
| OpenAI, *Introducing SWE-bench Verified*, 2024 (updated 2025), first-party technical report, **not peer-reviewed**; [report](https://openai.com/index/introducing-swe-bench-verified/) | How many apparently runnable tasks have underspecified issues or unfair tests? 93 developers screened 1,699 sampled SWE-bench tasks for specification/test quality, with three annotations per task and a conservative maximum-severity filter; 500 tasks form the released subset. | 38.3% of sampled tasks were flagged for underspecification and 61.1% for unfair tests; 68.3% were filtered for these or other issues. The conservative filter may exclude valid tasks; sampling, evaluator criteria and studied Python repositories limit generalization. These are not prevalence rates for this thesis's corpus. | Thesis: a passing repository test is not automatically a valid requirement label. Experiment: preserve independent mapping/oracle review before case admission; treat a test that encodes inaccessible requirements as a validity threat. Product: show inspectable specification-to-oracle evidence and abstain where mapping is uncertain. Action: retain current human gates rather than converting executable qualification into a scientific label. | 7/10: transparent first-party methodology, sizable professional-annotator sample and released annotations, but not peer-reviewed and the filtering is intentionally conservative. |

## 2026-09-26 — Degenerate project-bootstrap draws must fail closed

Search/read date: 2026-09-26; new source, deduplicated by DOI/title. Read the
abstract, cluster-bootstrap choices, few-cluster failure modes, Monte Carlo
design and results, applications, limitations and appendices.

| Reference / evidence | Question, sample and method | Result / limitations | Thesis / experiment / product relevance and action | Credibility |
| --- | --- | --- | --- | --- |
| Cameron, Gelbach and Miller, *Bootstrap-Based Improvements for Inference with Clustered Errors*, Review of Economics and Statistics 90(3), 2008, peer-reviewed; [DOI](https://doi.org/10.1162/rest.90.3.414), [author-accessible paper](https://www.nber.org/papers/t0344) | Which cluster-resampling and test procedures improve finite-sample inference when observations are dependent within clusters? The paper develops pairs, residual and wild cluster bootstraps, evaluates them with Monte Carlo experiments including designs with as few as five clusters, and reanalyzes two empirical settings. | Cluster-aware bootstrap-t variants reduce over-rejection in several studied linear-regression designs. The authors also show that few clusters yield a finite, nonsmooth bootstrap distribution and that pairs-cluster pseudo-samples can make a binary, cluster-invariant estimand inestimable. Results concern OLS/Wald tests, not PR-AUC, rare labels, repository agents or this exact percentile interval; performance depends on the resampling statistic and design. | Thesis: no H1/H2 evidence. Experiment: keep project-level resampling, but do not turn a one-class pseudo-sample into a numerical PR-AUC delta. Count every attempted draw and expose effective and degenerate counts/rates. Because this source does not establish coverage for a PR-AUC percentile interval conditioned on estimable draws, bootstrap support capable of producing a one-class resample makes the analysis descriptive-only; conditional endpoints remain diagnostics. The deterministic support check prevents seed or draw count from changing inferential validity. The precision simulation applies the same rule and divides power by all planned simulations. The frozen maximum degeneracy rate remains a design-health threshold, not a coverage guarantee. Product: none beyond honest uncertainty reporting. Action: harden `clustered_pr_auc_delta`, the precision simulation and the claim gate before any confirmatory freeze. | 9/10: peer-reviewed methods paper with explicit algorithms, Monte Carlo evidence and empirical replications; highly credible for clustered-inference failure modes, though transfer from linear-model tests to a PR-AUC difference is methodological rather than directly validated. |


## 2026-09-30 — Checkpoint provenance and the downstream-code novelty boundary

Search/read date: 2026-09-30. Both sources are new to this matrix (DOI/title
checked). Read the requirements paper's abstract, method, results and threats.
For leakage, verified the published abstract and read the accessible 2022
manuscript and authors' case-study account; these are not identical versions.

| Reference / evidence | Question, sample and method | Result / limitations | Thesis / experiment / product relevance and action | Credibility |
| --- | --- | --- | --- | --- |
| Kapoor and Narayanan, *Leakage and the reproducibility crisis in machine-learning-based science*, Patterns 4(9), 100804, 2023, peer-reviewed; [DOI](https://doi.org/10.1016/j.patter.2023.100804), [author account](https://reproducible.cs.princeton.edu/), [2022 manuscript](https://arxiv.org/abs/2207.07048) | What leakage mechanisms undermine predictive claims? Cross-field review, eight-part taxonomy, and reanalysis of four civil-war prediction studies. Method details were read in the accessible author materials, not an accessible final publisher PDF. | Correcting leakage removes the claimed machine-learning advantage in the reanalyses. The examples do not estimate leakage prevalence or effects in agent traces; disclosure cannot guarantee valid experiments. | Thesis: motivates auditable prediction-time information boundaries, not H2 support. Experiment: ensure each manifest checkpoint names the first non-Tier-B observation actually selected by the extractor; test later-event and label-plane rebinding. Product: distinguish invalid provenance from semantic loss. Action: align manifest construction and strict validation, without changing frozen evidence or feature values. This source motivates the audit; local regressions establish the specific defect. | 8/10: peer-reviewed taxonomy with reproducible case analyses; indirect domain transfer and manuscript/final-version differences limit application. |
| Villamizar et al., *On the Impact of Requirement Smells in LLM-Based Code Generation*, 2026, **preprint**, no peer-reviewed venue verified; [DOI](https://doi.org/10.48550/arXiv.2609.29208), [full text v1](https://arxiv.org/html/2609.29208v1) | Do smells affect generated-code quality? 74 requirements from four Java games, GPT-4o and DeepSeek-V3, five runs per condition; manipulated smell densities/categories, fixed skeletons and requirement-level unit tests. | Descriptive decreases vary by setting; density correlations and category associations are not significant after Bonferroni correction. Small game projects, injected smells, skeleton/test dependence and possible model familiarity limit transfer. Nonsignificance does not establish equivalence. | Thesis: direct neighboring work on downstream code, not a test of T1–T3 early warning or acceptance-criterion loss. Experiment: retain acceptance criteria as the primary task and distinguish controlled smell injection from historical defects. Product: no demonstrated customer value. Action: avoid claiming that studying smells and generated code is itself novel; position the contribution around condition-level loss and incremental pre-final provenance. Any primary-endpoint change requires an explicit methodological decision. | 7/10: transparent methods and linked replication materials, directly relevant; unreviewed preprint with four small applications and limited statistical evidence. |

Implementation outcome: six T1/T2/T3 regressions first reproduced invalid source
bindings, then passed after the manifest fix. Two isolated offline mutations
(removing the first-observation guard; admitting Tier B during selection) were
killed by the corresponding regressions. This qualifies these checks only:
it is not evidence of empirical leakage, H1/H2 performance, or corpus validity.
The existing first-observation policy is preserved. A different checkpoint
aggregation policy would require coordinated extractor/manifest changes and
an explicit protocol decision, not a silent reinterpretation of old traces.

## 2026-09-28: A passing repository test is bounded evidence

Search/read date: 2026-09-28; new source, deduplicated by DOI/title. Read the
abstract, patch and differential-testing methods, empirical results, manual
inspection procedure, discussion and threats to validity.

| Reference / evidence | Question, sample and method | Result / limitations | Thesis / experiment / product relevance and action | Credibility |
| --- | --- | --- | --- | --- |
| Wang, Pradel and Liu, *Are “Solved Issues” in SWE-bench Really Solved Correctly? An Empirical Study*, ICSE 2026 research track, peer-reviewed; [DOI](https://doi.org/10.1145/3744916.3764576), [author paper](https://arxiv.org/html/2503.15223v2) | How often do test-passing repository patches remain behaviorally divergent or incorrect? Study 877 plausible patches from three issue-solving tools on SWE-bench Verified; rerun all developer tests, use PatchDiff to generate tests comparing candidate and developer patches, then manually inspect a sample of suspicious patches. | 7.8% of plausible patches fail the full developer test suite; 29.6% show a PatchDiff-detected behavioral divergence. In the manually inspected suspicious sample, 28.6% of behaviorally divergent patches were judged certainly incorrect. Divergence alone does not imply an error: unspecified behavior may permit multiple valid implementations. Manual review covers a sample, PatchDiff has detection limits, generated tests and the developer patch are imperfect references, and the study concerns Python issue repair rather than requirement omissions or browser E2E. | Thesis: supports caution about treating a passing executable check as complete requirement satisfaction, but does not establish H1/H2. Experiment: retain per-constraint browser target outcomes, unknowns and independent mapping/oracle review; do not convert a gold pass, mutant kill, or absent target failure into a global correctness label. The source reinforces the existing endpoint decision gate without changing the frozen estimand or exploratory counts. Product: show the exact checked condition and evidence boundary rather than a generic “correct” badge. Action: record this oracle-coverage threat in the canonical matrix and carry it into the human endpoint decision; no new benchmark or provider run follows from this paper alone. | 8/10: peer-reviewed ICSE empirical study with 877 patches, explicit methods and public paper; relevant to repository-agent evaluation, but manual subsampling, differential-test limits and uncertain oracle equivalence constrain transfer. |

## 2026-09-30 — Search log: candidates not yet read (not matrix entries)

Search date: 2026-09-30. The cloud session's network egress blocked arxiv.org,
doi.org, ACM, OpenReview, W3C and OpenTelemetry hosts, so only search-result
snippets were available. Under this matrix's policy (abstract plus method,
results and limitations must be read), none of the items below is a matrix entry,
has a credibility score, or supports any claim. All are preprints or unverified
venues. arXiv 2609.29208 is excluded: it was read and entered above the same day. Next action: read the rest from an unrestricted session, then classify.

| Candidate (preprint unless noted) | Why it may matter | Intended check |
| --- | --- | --- |
| arXiv 2603.26233, *Ask or Assume? Uncertainty-Aware Clarification-Seeking in Coding Agents* | Underspecified SWE-bench Verified variants; state-history underspecification detection | Relevance to optional RQ3 and to B0 operational signals |
| arXiv 2603.00187, *ClarEval*; arXiv 2608.09072, *SWE-RPG* | Ambiguity taxonomies (missing goal/premise/terminology) for code agents | Compare taxonomy with the smell/condition-loss separation |
| arXiv 2603.24755, *SlopCodeBench* | Degradation over iterative checkpoints | Possible multi-step analogue of T1–T4 |
| arXiv 2607.01980, *Epic-Organized vs. Requirement-Aligned Gherkin* | LLM acceptance-criteria generation quality | Rubric and rater-agreement design for the primary task |

Resolution (2026-10-01): all five candidates above were read from an unrestricted
session; see the next section. This log is kept as history.

## 2026-10-01 — Clarification, stage attribution and rater-scale evidence

Search/read date: 2026-10-01. Candidates came from the 2026-09-30 log; each was
deduplicated by arXiv ID/title. Read the abstract and the accessible full text
(method, results, limitations) via arXiv HTML. None is peer-review verified
except where stated; none supports a confirmatory H1/H2 claim.

| Reference / evidence | Question, sample and method | Result / limitations | Thesis / experiment / product relevance and action | Credibility |
| --- | --- | --- | --- | ---: |
| Li et al., *ClarEval*, arXiv 2603.00187, 2026, **preprint**; [arXiv](https://arxiv.org/abs/2603.00187), [code](https://github.com/JialinLi13/ClarEval) | Can agents elicit missing information? GPT-4o injects three ambiguity types (missing goal, missing premise, ambiguous terminology) into code tasks; three senior engineers review (Fleiss κ 0.82, about 12% discarded/rewritten); rule-based user simulator (96.5% agreement with an LLM judge on 200 turns); 11 agents. | Single-turn and multi-turn clarification skill correlate weakly (r = 0.32); ambiguous terminology is hardest (GPT-4o Pass@1 6.71% vs 9.76% and 10.37%). Synthetic injection by an LLM; small human validation; no link shown to real-development outcomes. | Thesis: injected ambiguity is a *smell* manipulation, not a measure of lost testable conditions; confirms the need to keep smell family and constraint loss separate. Experiment: reuse the idea of reviewer-filtered injection with agreement reporting for clean/defective pair construction. Product: clarification is a different workflow from post-hoc loss detection. Action: incorporated into the recoverability audit as a rationale for independent manipulation review, without adopting its taxonomy as validated labels. | 5/10: transparent code, reviewed injection, but unreviewed preprint and synthetic tasks. |
| Edwards and Schuster, *Ask or Assume? Uncertainty-Aware Clarification-Seeking in Coding Agents*, arXiv 2603.26233v3, 2026, **preprint**; [arXiv](https://arxiv.org/abs/2603.26233), [code](https://github.com/nedwards99/ask-or-assume) | Can agents decide when to ask? Underspecified SWE-bench Verified variants from prior work (GPT-4o summaries); an intent agent monitors state history; Full/Hidden/Interactive baselines; two models. | UA-Multi resolves 69.40% vs 61.2–61.6% single-agent and 70.8–72.8% fully specified; queries rise with difficulty. Only a 10-task manual spot-check of the variants (5 essential, 5 recoverable); user simulator is an LLM; cost about $3.50/task for one model. | Experiment: provides a conceptual comparator for underspecification monitoring, not an admitted B0 baseline; its semantic history access and clarification intervention require a matched-information and cost audit; the same 10-task check shows removed detail is not always load-bearing, supporting per-constraint labels rather than treating every omission as a defect. Product: cost per task is a deployment constraint. Action: incorporated into the context-recoverability audit; no B0 feature or protocol change. | 4/10: relevant design, but preprint, weak dataset validation, LLM-simulated user. |
| *SWE-RPG*, arXiv 2608.09072, 2026, **preprint**; [arXiv](https://arxiv.org/abs/2608.09072) | Where do agent trajectories diverge? 163 tasks, 31 repositories; ground-truth clarification and planning references from interviews with ten engineers, LLM synthesis and review by two authors; LLM judge assigns the earliest deviating stage; three agents, six backends. | Resolve rate 31.5%; requirement-clarification failures 24.5–46.0%. Similar resolve rates hide different bottlenecks (40.5% vs 39.3% resolved, 26.4% vs 40.5% requirement failures). Judge agreed with humans on 96% of 50 coverage items and 92% of 50 stage labels. Python/Java only; LLM-built references; agreement sample small. | Thesis: a close stage-attribution comparator among the sources reviewed. Its information-point references and full-trajectory coverage overlap the motivation; the testable distinction is prospective pre-T4 predictive value under matched information boundaries, not an asserted absence of fine-grained references. Experiment: propose, subject to human approval, an earliest-loss-stage descriptor as a *secondary* readout; its judge-agreement sample is too small to adopt as a label source. Action: incorporated into the audit discussion as a retrospective comparator; novelty remains to be demonstrated empirically. | 5/10: directly on topic with numbers, but unreviewed and judge-dependent. |
| *SlopCodeBench*, arXiv 2603.24755v2, 2026, **preprint**; [arXiv](https://arxiv.org/abs/2603.24755) | Does quality degrade across iterative extensions? 36 problems, 196 checkpoints, 15 agents, 473 human repositories as reference. | Best agent passes 14.8% of checkpoints; erosion rises in 77% and verbosity in 75.5% of trajectories; quality prompts lower initial but not iterative degradation. Measures structure, not requirement retention. | Thesis/product: shows degradation can accumulate while checkpoints pass; a code-quality, not requirement-loss, construct. Experiment: no change. Action: context only. | 5/10: open benchmark, wide agent coverage, wrong construct for H1/H2. |
| *Epic-Organized vs. Requirement-Aligned Gherkin*, SEET 2026 (Springer proceedings per the preprint), arXiv 2607.01980; [arXiv](https://arxiv.org/abs/2607.01980) | Does epic-level organization improve LLM acceptance-criteria quality? 107 requirements from four PURE documents; one gpt-4o-mini run; TF-IDF and embedding coverage; four blinded researchers, pre-registered. | Semantic coverage 94.3% vs 92.9%; expert ratings favour epic-organized (completeness 4.31 vs 3.50). Fleiss κ between −0.08 and 0.03 despite preferences, attributed to scale-usage differences; coverage embeddings come from the generating provider family; single run. | Experiment: the authors recommend complementary lexical and semantic measures and report scale-use disagreements; this does not validate our ordinal alpha or 0.70 threshold. Independent constraint labels remain necessary. Action taken: regression test `test_scale_offset_is_judged_by_declared_measurement_level` shows a one-step offset yields negative nominal alpha but ordinal alpha at or above 0.70, so the rubric must declare its level beforehand. | 5/10: peer-reviewed venue claimed by the authors but not independently verified here; pre-registered and candid, tiny sample. |

Tension to record: none of these sources contradicts a current decision. The
SWE-RPG stage-attribution framing is close to the thesis motivation, so related
work must state that it localizes failures after the fact from references, whereas
T1–T3 provenance targets constraint loss before the final artifact. Whether to add
earliest-loss-stage as a secondary readout is a human decision.

## 2026-10-01 — SMT checking is a bounded auxiliary control

Search/read date: 2026-10-01; new source, deduplicated by DOI/title. Read the
abstract, method, data construction, four research questions, results, threats
and conclusion.

| Reference / evidence | Question, sample and method | Result / limitations | Thesis / experiment / product relevance and action | Credibility |
| --- | --- | --- | --- | ---: |
| Chen, Babikian, Feng, Varró and Mussbacher, *LLM-based Satisfiability Checking of String Requirements by Consistent Data and Checker Generation*, IEEE RE 2025, peer-reviewed; [DOI](https://doi.org/10.1109/RE63999.2025.00030), [author manuscript](https://arxiv.org/html/2506.16639) | Can LLM-generated data and Python/SMT checkers decide consistency for natural-language string requirements? The study builds 340 manually formalized requirement sets across 12 string-constraint categories (283 satisfiable, 57 unsatisfiable), evaluates four LLMs, and compares direct generation, hybrid checking and feedback-enhanced variants against manually defined ground truth. | Hybrid generation plus valid-formula feedback substantially improves generated-string validity and unsatisfiable-case detection; the best end-to-end F1 remains below the ground-truth-checker upper bound. A generated example and a generated checker can agree while both are wrong. The corpus is imbalanced, manually constructed from programming exercises, limited to string constraints, uses differing temperatures, and is not industrial scale. | Thesis: no H1/H2 evidence and no basis for equating satisfiability with requirement quality. Experiment: an SMT checker may become a secondary control only for constraints explicitly marked formalizable; it must remain outside the label plane and cannot replace the independent executable oracle or human mapping. Product: a structured contradiction warning could be useful for exact string constraints, with abstention elsewhere. Action: record a future feasibility slice rather than add SMT to the confirmatory protocol now. | 9/10: peer-reviewed IEEE RE research paper with explicit ground truth, four models, artifacts and detailed threats; strong within a narrow formal domain, but indirect for requirement smells, repository agents and temporal provenance. |

Implementation outcome: the primary human-agreement policy is now bound to
`rubric-v3`. It explicitly freezes ordinal Krippendorff alpha, label order,
bootstrap configuration and decision thresholds. The analysis entry point
validates that policy before reading labels, and the rubric loader rejects a
missing level, a nominal policy carrying an ordinal order, or an order that
does not exactly match the non-missing labels. This prevents the nominal versus
ordinal choice from being made after the observed agreement is known. It does
not establish annotator reliability; actual independent annotations remain a
human dependency.

## 2026-10-01 — Incorporation and outcome audit

Re-read the five author manuscripts above (ClarEval v1, Ask or Assume v3,
SWE-RPG v1, SlopCodeBench v2 and Gherkin v1), including methods and relevant
limitations. Credibility ratings remain provisional and unchanged. Corrected
the automatic B0 analogy, categorical novelty claim and overinterpretation
of Gherkin agreement/coverage findings. The [E2E recoverability audit](2026-10-01-e2e-recoverability-audit.md) incorporates all five into concrete interpretation
and review decisions, with public-record accounting and limits of verification.
No source is counted twice and no existing outcome is reclassified.

## 2026-10-02 — Structure-only trace monitors as an operational comparator

Search/read date: 2026-10-02 (web search plus arXiv HTML full text). Both items are
new (deduplicated by arXiv ID/title against this matrix). Abstract, method, data,
results and stated limitations were read. Both are **preprints**; neither supports
a confirmatory H1/H2 claim.

| Reference / evidence | Question, sample and method | Result / limitations | Thesis / experiment / product relevance and action | Credibility |
| --- | --- | --- | --- | ---: |
| *Automata from Agent Traces: Failure and Next-Step Prediction*, arXiv 2608.23670v1, 2026, **preprint**; [arXiv](https://arxiv.org/abs/2608.23670) | Can finite-state machines extracted from agent traces predict failure and next steps? 12 public benchmarks over 8 domains; 2,000 SWE-agent traces; deterministic prefix-tree/right-congruence construction; gradient-boosted failure classifier; prefix monitor. | Full-trace failure AUROC 0.799 on SWE-agent (up to 0.941 on tau2-bench telecom) differs from prefix-monitor rank-AUROC 0.66 near 25% completion. Retrospective trace replay simulates stopping near 32%; it does not establish a live intervention benefit. High failure prevalence makes F1 alone misleading. Splits are random 80/20 by trace with no task/repo stratification reported; the activity-extraction function is dataset-specific; no requirement or task semantics. | Thesis/experiment: shows that a semantics-free process-structure monitor can already rank failing runs before the end, so B0 (static + operational) must not be assumed weak; any B3 gain has to be shown over a strong structure-only operational feature set, with project-level splits (their trace-level split does not establish unseen-project generalization and risks shared-project regularities). Product: a cheap generic trace monitor is the obvious alternative to explaining *which* requirement condition was lost. Action: add a "structure-only trace monitor" as an optional operational ablation (see `temporal-warning-protocol.md`); no change to B0/B3 definitions. | 5/10: transparent method and many datasets, but preprint, trace-level split, outcome = task failure rather than constraint loss. |
| Li et al., *CodeTracer: Towards Traceable Agent States*, arXiv 2604.11641v3, 2026, **preprint**; [arXiv](https://arxiv.org/abs/2604.11641) | Can failure onset be localized in long code-agent trajectories? CodeTraceBench: 4,354 annotated trajectories (3,326 after filtering) from 5 benchmarks, 5 backbones, 4 agent frameworks; tree-indexed traces and backward tracing from failing tests; reflective replay of diagnoses into failed runs. | Step-level macro F1 about 46-48% vs 16-19% for bare LLM; replay improves Pass@1 with matched replay budgets, but diagnosis tokens are additional expenditure. Labels by the authors only, Cohen kappa 0.73 on a 15% double-annotated subset; error taxonomy is environment/dependency/localization/hypothesis/verification/looping, not requirement conditions; offline matched budgets. | Thesis: another *post hoc* earliest-failure localizer working backward from test failure; it reinforces the SWE-RPG framing already recorded (retrospective attribution vs prospective pre-T4 lineage) and adds no requirement-loss construct. Experiment: its agreement level (0.73, single annotation team) is a reminder that stage labels need blind double annotation; no change. Product: tree-indexed trace normalization across frameworks is the integration cost our adapter layer will also face; context only. | 5/10: large, open-ended benchmark, but preprint, author-only labels, wrong construct. |

Candidates found but not read in full (not matrix entries, no claim): arXiv 2606.04990
(survey of evidence tracing and execution provenance in LLM agents), arXiv 2605.09934
(TRACER, claim-level provenance for multimodal agents), arXiv 2606.25550 (requirements
generation from code, experience report). OpenTelemetry GenAI conventions: per
secondary reports (not the primary repository) they moved to a dedicated repository in
June 2026 and are still marked Development; pin versions in any exporter. Primary
documentation was not verified in this run.

Tension recorded: none of the above contradicts a decision. Human decision needed:
whether a structure-only trace monitor becomes a preregistered B0 ablation or stays an
optional sensitivity analysis.

## 2026-10-02 — Repeated generations are not independent requirements

Search/read date: 2026-10-02. Read the abstract, survey, method and limitations in the primary paper; deduplicated by DOI/title.

| Source / status | Question, sample and method | Finding / limits | Thesis, experiment, product and action | Credibility |
| --- | --- | --- | --- | --- |
| Dror, Baumer, Shlomov and Reichart, *The Hitchhiker's Guide to Testing Statistical Significance in Natural Language Processing*, ACL 2018, peer-reviewed methods/opinion paper; [original](https://aclanthology.org/P18-1128/), DOI 10.18653/v1/P18-1128 | How should significance tests match NLP experiments? Test-selection protocol plus survey of 196 ACL and 37 TACL papers from 2017. | Testing was often omitted or underspecified. Section 5 identifies dependent observations as an unresolved complication. Predates LLM agents; does not solve our clustered design. | Thesis: preserve the sampling unit. Experiment: retain per-requirement nested repetitions in the [extended audit](2026-10-01-e2e-recoverability-audit.md), without pooled iid inference. Product: report sample provenance with comparisons. Action implemented: six-lot accounting and classification replay; no post-hoc test selection or protocol change. | 8/10: peer-reviewed, transparent survey and test assumptions; reproducible guidance, but indirect to agents and insufficient for our dependency structure. |

## 2026-10-03 — Exchangeability and the existing H1 estimand

Search/read date: 2026-10-03. Deduplicated by DOI/title. Read the abstract,
theory, simulations, real-data example and discussion in the original article.

| Source / status | Question, data and method | Findings / limitations | Thesis, experiment, product and action | Credibility |
| --- | --- | --- | --- | --- |
| Winkler, Webster, Vidaurre, Nichols and Smith, *Multi-level block permutation*, NeuroImage 123 (2015), 253–268; peer-reviewed; DOI [10.1016/j.neuroimage.2015.05.092](https://doi.org/10.1016/j.neuroimage.2015.05.092); [full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC4644991/) | Can permutation inference preserve hierarchical dependence? Nested exchangeability blocks, simulations including 36- and 27-observation structures, and a Human Connectome Project application. | Restricting rearrangements to preserve dependence controls false positives in evaluated settings; unrestricted rearrangements can inflate error. Assumptions and reduced permutation space affect validity/power. Neuroimaging GLMs, not requirement-loss outcomes. | Thesis/experiment: project bootstrap does not validate independent intent-level sign flips. Product: expose inference assumptions alongside comparisons. Action: clarify the existing estimand's Monte Carlo test assumptions; flag the exchangeability decision for prospective review. No retrospective p-value replacement. | 9/10: peer-reviewed theory, simulations, real-data demonstration and implementation; transparent and replicable, but indirect to our ordinal estimand. |

Tension requiring a human decision: `paired_probability_of_superiority` averages
repetitions within intent and bootstraps projects, but its p-value flips each
intent independently. Before confirmatory use, justify independent arm
exchangeability under the actual randomized design or preregister a dependence-
preserving alternative. Two projects alone do not establish validity; the legacy
`valid_for_inference` flag is only a project-count check.

Implementation audit: a NaN rating previously entered the "defective better"
branch, while infinities and out-of-scale values also produced scientific pair
outcomes. Null IDs were converted to the text "None". The estimand now rejects
nontext/empty identities and ratings outside its declared 0–3 categories, with
regressions for both arms and identity fields. Integer-valued floats remain
accepted. This input-contract repair preserves valid-input estimates and does
not validate annotation, pairing upstream, missingness or the inference design.

## 2026-10-03 — Requirement-traceability multi-agent generation (ISSTA 2026)

Search/read date: 2026-10-03. Deduplicated by arXiv ID/title (absent from this
matrix). Read the abstract, method, evaluation protocol, ablation and threats
sections of the full text. Candidates seen in search snippets only and **not**
matrix entries (no claim): arXiv 2604.21505 (ambiguity and function-level code
generation), 2607.02949 (BeSpec), 2607.00711 (ClarifyCodeBench), 2609.00568
(WiseSpec).

| Source / status | Question, sample and method | Findings / limitations | Thesis, experiment, product and action | Credibility |
| --- | --- | --- | --- | --- |
| Chen et al., *TraceDev: A Traceability-Driven Multi-agent Framework for Requirement-to-Code Development*, Proc. ACM Softw. Eng. 3 (ISSTA), article ISSTA080, 2026; accepted at ISSTA 2026 per arXiv listing, arXiv [2607.18886](https://arxiv.org/abs/2607.18886) | Does a requirement-to-design-to-code traceability graph (five agents; Validator maintains the graph) improve generated code? Use cases from eTour (53) and SMOS (72); baselines ChatDev and MetaGPT; Gemini-2.5-Flash and DeepSeek-V3.2; ablation by agent removal; human evaluation of 20 sampled use cases. | Reports success 53.63% (eTour) and 56.82% (SMOS) with Gemini-2.5-Flash, far above the baselines; removing the Tester drops success to 13.9% while LOC is unchanged, so code volume is not correctness. Semantic coverage is judged by a DeepSeek-V3.2 LLM judge (3-vote majority) and tests are LLM-generated; no controlled requirement defect, no pre-artifact warning, and one judge family also generates in one setting. | Thesis: independent motivation that omitted entry conditions (their example: "The agency has logged in") are a recognised failure of requirement-to-code agents; it does not test H1 or H2. Experiment: confirms that traceability graphs are a design for prevention, not a measurement of loss before T4; the semantic-coverage metric is the judge-based outcome our protocol treats as advisory (see the judge-control results). Product: closest published design to a requirement-to-artifact lineage; a candidate comparator for positioning, not validation. Action: cite as related work only; no protocol change. Open question for the human: whether its traceability graph should be an ablation of the T1-T3 provenance features (B3) or remain background. | 7/10: peer-reviewed venue, transparent ablation and public datasets; LLM-judged coverage and generated tests, no controlled defect, and gains are against two weak baselines. Read from the full-text PDF. |

OpenTelemetry GenAI conventions: the `open-telemetry/semantic-conventions-genai`
repository exists (primary page checked 2026-10-03), but its README states no
stability level; the "all Development, none Stable" statement remains from
secondary reports. Pin a version in any exporter and re-verify on the primary
registry before relying on it. No contradiction with a current decision.

## 2026-10-04 — Under-specification: reversal risk, inference rate and ambiguity benchmarks

Search/read date: 2026-10-04. Deduplicated by arXiv ID/title (none previously in
this matrix; 2604.21505 and 2607.00711 were snippet-only candidates on
2026-10-03 and are now read at abstract level). Akli et al. was audited in
full text (method, results, and threats); the other four remain abstract-level
reads and are listed in a separate pending-reading queue, outside the canonical
matrix and without credibility scores or evidentiary recommendations. All five are
arXiv preprints (not peer-reviewed as of this reading)
and none are evidence for H1/H2.

| Source / status | Question, sample and method | Findings / limitations | Thesis, experiment, product and action | Credibility |
| --- | --- | --- | --- | ---: |
| Akli, Papadakis, Cordy, Le Traon, *When Prompt Under-Specification Improves Code Correctness*, arXiv [2604.24712](https://arxiv.org/abs/2604.24712), 2026 preprint (cs.SE), full text read 2026-10-04 | Do prompt wording/structure mutations always hurt code generation? 10 LLMs over HumanEval and 1,055 LiveCodeBench tasks; 3,651 GPT-5-mini-generated lexical-vagueness, under-specification, and syntax/format variants. Qwen2.5-Coder-32B judged all variants; three researchers reviewed a stratified sample of 100 (97% agreement with the judge on compliance, 86% on naturalness). Greedy Pass@1 plus pass→fail/fail→pass transitions; manual root-cause analysis of consistently improved tasks. | Under-specification changed Pass@1 by −11.8 points on HumanEval but −0.9 on LiveCodeBench; the LiveCodeBench fail→pass/pass→fail mean per-model ratio for under-specification was 0.89 (the 0.99 value belongs to lexical vagueness), so near-zero aggregate change concealed opposing transitions. Richer descriptions supplied redundant cues, while removing misleading lexical/constraint cues sometimes improved code. Threats: synthetic variants may not resemble developer defects (US naturalness was 0.61 on LiveCodeBench); HumanEval contamination; Python-only code-generation tasks, including HumanEval functions and LiveCodeBench competitive-programming tasks; greedy one-shot decoding hides stochastic variance; exploratory root-cause claims are not causal. | **Thesis:** supports recoverability/context redundancy and shows that the sign of an omission effect is not guaranteed. **Experiment:** report C-better-than-A as a reversal; retain B; code `context_cue` before outcomes; do not use the paper as an effect-size anchor because its task, mutation, and oracle differ. **Product:** it argues against generic “more specification is always safer” warnings; any product must show the lost condition and downstream evidence. | 7/10: broad multi-model sample, transition analysis, manual validation, explicit threats and a replication package, but still a non-peer-reviewed exploratory preprint with synthetic mutations and Python code-generation tasks. |

### Pending full-text reading, outside the canonical matrix

The following primary abstracts were checked on 2026-10-04. Their methods,
results and limitations have not been reviewed in full. No credibility score,
quantitative anchor or thesis/experiment recommendation is assigned here.

| Candidate and primary version | Authors | Reading status |
| --- | --- | --- |
| [What Prompts Don't Say](https://arxiv.org/abs/2505.13360v3) | Chenyang Yang, Yike Shi, Qianou Ma, Michael Xieyang Liu, Christian Kästner, Tongshuang Wu | Abstract only; full-text review pending. |
| [From Business Requirements to Test Assertions](https://arxiv.org/abs/2607.10277v1) | Ma and Eisty | Abstract only; full-text review pending. |
| [Clarity Is Not Assumed (Orchid)](https://arxiv.org/abs/2604.21505v3) | Yang et al. | Abstract only; full-text review pending. |
| [ClarifyCodeBench](https://arxiv.org/abs/2607.00711v2) | Fang et al. | Abstract only; full-text review pending. |

**Source verification, 2026-10-04.** Review of [Akli et al.'s primary methods,
results and threats](https://arxiv.org/html/2604.24712v1) corrected the mutation
ratio: Table 4 and section 5.2 give 0.89 for under-specification, whereas 0.99
belongs to lexical vagueness. The task description now distinguishes HumanEval
functions from LiveCodeBench competitive-programming tasks. This review informs
the reversal wording below, not the effect size of the selected46 study. The
four abstract-only candidates remain outside the admitted matrix under its
canonical reading policy.

**Incorporation decisions (2026-10-04).**

1. Akli et al. do not contradict H1a, but they show the omission effect can be
   null or reversed. The pre-registration draft stated only the support
   criterion (interval above 0.5). Added a sentence committing to report an
   interval below 0.5 as a reversal. The decision to keep H1a one-directional
   for the confirmatory claim remains with the advisor (new open decision 5).
2. Akli et al. study code-generation benchmarks rather than browser journeys.
   The paper does not validate this study's browser oracle, requirement-smell
   mapping or pre-final warning. The four pending candidates must not support
   a scientific gap claim until their full methods and limitations are reviewed.
3. Korn et al. (AIRE'26, entry above) report unreliable LLM injection of
   synthetic smells and omissions. The pre-registered LLM panel for A/B/C
   validity plus the 20% human audit (open decision 2) is therefore a
   necessary control, not an optional one.
4. Proposal table note: Siddeeq et al. (SEET 2026) is now listed as accepted at
   SEET 2026 (CCIS vol. 3126, Springer, per arXiv listing); the Drive proposal
   labels it "preprint". Drive text was not edited (see run summary).

## 2026-10-05 — Few-cluster inference for confirmatory planning

Search/read date: 2026-10-05. Read the abstract, the few-cluster methods
section, simulation discussion, and cautions in the full author manuscript.
Deduplicated by DOI/title; the source was not previously in this matrix.

| Source / status | Question, sample and method | Findings / limitations | Thesis, experiment, product and action | Credibility |
| --- | --- | --- | --- | ---: |
| Cameron and Miller, *A Practitioner's Guide to Cluster-Robust Inference*, Journal of Human Resources 50(2), 317–372, 2015, DOI [10.3368/jhr.50.2.317](https://doi.org/10.3368/jhr.50.2.317); peer-reviewed methodological review | How should regression inference handle observations correlated within clusters, especially with few clusters? The paper develops the cluster-robust framework, reviews finite-cluster corrections, bootstrap variants and simulations, and illustrates the methods empirically. | Ignoring within-cluster dependence can make intervals too narrow and tests over-reject. "Few" can extend well beyond 20 clusters depending on balance and leverage. In the reviewed simulations, pairs-cluster bootstrap did not eliminate over-rejection; wild-cluster and bias-corrected methods improved size but were not universally exact. The methods and simulations concern regression estimators, not this thesis's probability-of-superiority statistic. | **Thesis:** supports treating `project_id`, not repeated requirements or runs, as the independence unit. **Experiment:** the PR #169 requirement-level sign-flip cannot be a confirmatory gate merely because its interval bootstraps projects. Add an exact project-level sign-flip sensitivity, retain the requirement-level result as optimistic only, and withdraw the 9×4 recommendation until the grid is regenerated and reconciled with the 8- or 7-project candidate frames. **Product:** no direct claim. | 9/10: peer-reviewed journal review with formal derivations, simulations, implementation guidance and explicit limitations; highly credible for clustered-inference cautions, but indirect for the custom ordinal estimand and very small project count here. |

**Incorporation decision.** This source changes the planning gate, not the
observed H1a estimate. The 46-case result remains exploratory. A project-level
exact sign flip is now the nonparametric test used in the power sensitivity;
the existing requirement-level p-value is explicitly diagnostic until a human
methodological decision freezes the confirmatory analysis.

## 2026-10-05 — Unspecified requirements: recovery is partial, conditional and unstable across model updates

Search/read date: 2026-10-05. Deduplicated by arXiv ID (previously listed only in the
pending-reading queue of 2026-10-04, abstract level). Full text read: setup,
section 3 results, limitations. Orchid (arXiv 2604.21505) and ClarifyCodeBench
(arXiv 2607.00711) were re-checked at abstract level only and remain in the pending
queue; no entry or claim.

| Source / status | Question, sample and method | Findings / limitations | Thesis, experiment, product and action | Credibility |
| --- | --- | --- | --- | ---: |
| Yang, Shi, Ma, Liu, Kästner, Wu, [*What Prompts Don't Say: Understanding and Managing Underspecification in LLM Prompts*](https://arxiv.org/abs/2505.13360), arXiv preprint v3 (venue not stated in the PDF header), Carnegie Mellon | How do LLMs behave on requirements a prompt leaves out? Three tasks (code explanation, trip advice, product descriptions), 20 requirements per task (60 total, from existing prompts, LLM brainstorming and error analysis, kept if at least one of three annotators selected them), 240 synthetic prompts built by a cyclic design (each prompt states 10 consecutive requirements), models Llama-3.3-70B, gpt-4o-2024-08-06, o3-mini; per-requirement validators (scripts or LLM, 95.6% human agreement on a sample). | Unspecified requirements are satisfied less often (-22.6% mean accuracy, up to -93.1%), yet 41.1% are guessed at >=98% accuracy. Format requirements are guessed more (70.7%); conditional (corner-case) requirements less (22.9%). Across model updates, 22.9% of cases regress, and unspecified requirements regress about twice as often (5.9% regress by >20%). Limits stated by the authors: small requirement set (n=60), synthetic prompts, LLM validators with same-family bias. Additional limits for this project: requirements are LLM-elicited and not tied to repository documentation; no browser or executable-UI oracle; not peer-reviewed as read. | Thesis: independent support that omission effects are heterogeneous (matches the H1b recoverability framing), not support for the A/B/C effect size. Experiment: adds `conditional_rule` as a recorded exploratory descriptor and requires pinned, call-level model identifiers in the freeze receipt (pre-registration note 2026-10-05, advisor decision 6). Product: model-update drift on unspecified rules is a plausible reason to re-run requirement-anchored checks after provider changes; hypothesis only. Do not cite the 41.1% or 22.9% figures as expectations for this study. | 6 (detailed method and public code; preprint; small and synthetic; different task family) |

## 2026-10-06 — Early detection: a prefix monitor confirms failure more than it anticipates it

Search/read date: 2026-10-06. Deduplicated by arXiv ID/title (not previously in this
matrix). Read: abstract, methodology (sections II.E–F), RQ1 findings 1–4, and threats to
validity of the PDF. The 2026-10-06 web search also surfaced AgentForesight (ICML 2026,
online auditing of multi-agent failures; result page only), a strained-coherence blog post
(vendor/practitioner blog, product intelligence only) and OpenTelemetry GenAI conventions
(see the 2026-09-30/10-03 entries: still `Development`, repository `semantic-conventions-genai`).
AgentForesight and Terminal-Bench-2 follow-ups are queued, not entered: only the result page
was read, so they carry no score or claim.

| Source / status | Question, sample and method | Findings / limitations | Thesis, experiment, product and action | Credibility |
| --- | --- | --- | --- | ---: |
| Zhao, Li, Li, Zhao, Barr, Sarro, Ye, [*Failure as a Process: An Anatomy of CLI Coding Agent Trajectories*](https://arxiv.org/abs/2607.09510), arXiv preprint (cs.SE), submitted 2026-07-10 | When do coding-agent failures begin, why, and can they be caught early? 3,843 Terminal-Bench executions (7 models, 3 scaffolds); 1,794 complete trajectories (63k+ steps) manually annotated for decisive error (t_err), failure lock-in (t_lock) and first observable sign (t_obs), with a root-cause taxonomy (Cohen's kappa 0.78–0.94 reported). A blind prefix monitor (an LLM) reads the first t steps, with or without the task's core requirements, on 2,659 prefixes from 600 trajectories. | Median decisive error at step 7, lock-in about step 12, first observable signal about step 16. The monitor flags locked-in runs at 82% precision but has median lead time zero relative to t_lock; only 3.7–8.7% of failures are flagged before lock-in; recall is 18.2% with the task name only and 28.8% with requirements. Self-revealing failures (environment errors) barely benefit from the requirements; specification-relative ones (ignored requirements 3%→22%, false premises 15%→32%) do. Limits: Terminal-Bench CLI tasks, not requirement-to-UI generation; the same LLM family annotated and monitored; labels are hindsight-based; the monitor is an LLM, not a provenance model; preprint. | **Thesis:** independent support for the premise behind H2 that a loss can precede its observable symptom, and for the H1/H2 separation: a requirement-ignoring failure is detectable mainly when the monitor sees the requirement. It is not evidence for T1–T3 provenance features. **Experiment:** B0 (requirement plus operational telemetry) is the correct strong baseline because giving a monitor the requirement is what moved recall; keep B0 requirement-aware. Report detection relative to a pre-registered lock-in analogue (first stage after which the omitted rule can no longer be recovered, e.g. T2 plan committed) in addition to ms lead time, because alerts after lock-in only confirm. A human decision is needed on whether to add that stage-relative lead metric to the H2 pre-registration. No change made to the frozen protocol. **Product:** supports "explain the semantic loss, not just flag the run" as a differentiator versus generic trace monitors; hypothesis only. | 6/10: transparent method, high reported annotation agreement and released annotations, but a preprint with CLI-task transfer, same-family annotator/monitor and hindsight labels |

**Decision (2026-10-06).** Tension noted, not resolved: the paper's monitor shows little
foresight, which makes the H2 margin (PR-AUC +0.05 for B3 over B0) harder to expect on
omissions that lock in at T1. This is a reason to report the stage at which each first alert
fires, not a reason to change H2. Pending advisor decision 3 (collect T1–T3 in the H1 round or
drop H2) is unchanged.
