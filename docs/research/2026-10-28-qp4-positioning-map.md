# QP4 positioning: evidence map against close antecedents

Date: 2026-10-28. Status: working document for review by Codex, Dante and Márcio. It does
not claim novelty from an absent search, and it does not turn planning into decisions.
Reading status of every source is in `docs/research/literature-matrix.md` (section of
28/10). "Read by Claude" below means the sections named were read through a fetch of the
primary text (PDF or HTML) in this session; some arXiv HTML pages are blocked for this
session by robots rules, which is an access limit, not evidence about the source.

## The narrow contribution being positioned

One obligation, documented in a real project, is removed from the request. The same
incomplete request drives (a) the implementation and (b) the review tests. Against browser
oracles frozen before generation, the study separates implementation loss, conditional
detection by tests, and joint escape per requirement, with a meaning-preserving rewording
control. All QP4 findings so far are exploratory and post hoc on 25 requirements.

## Close antecedents, what they already show, and what is left

| Source (status) | What it already shows that overlaps QP4 | What it does not do (as far as read) |
|---|---|---|
| Haeri and Ghelichi, *Specification Grounding Drives Test Effectiveness for LLM Code*, arXiv 2607.06636 (read by Claude from a truncated PDF fetch: §3.1–3.4, §4.5, §5–6, App. A, E, I.2–I.5; read by Codex from the primary HTML v1, including App. G, H/Table 10, I.5/Table 15, I.6, I.8 and I.9, which the PDF fetch did not reach) | The code model sees only the ticket; the ungrounded tester also writes from the ticket, so the **same source** feeds both (§3.1, §3.3). Removing validation rules drops detection 30/30 → 6/30 (§4.5). Showing code to an ungrounded tester drops detection 7/24 → 0/24, grounded stays 24/24 (App. E). Rules derived from the ticket recover 47% of detection (App. I.2). **Best-of-N:** unioning ungrounded suites gives 15/29 from k = 2 to 8 against 29/29 with the specification (App. I.5, Table 15). Beyond the 26 core functions: six stateful, multi-step tasks (I.6), transformers/NLTK utilities at fixed commits (I.8) and four PyPA packaging utilities with an external oracle (I.9). A null on HumanEval+: grounded 13/22 vs free+ 14/22 (App. H, Table 10). | "Small functions vs real projects" is **not** a sufficient boundary: I.8 and I.9 use real library utilities with external oracles. The distinction that holds in the sections read is narrower: no browser journeys over project-documented obligations, no single controlled removal of one obligation with a rewording control, and no joint-escape measure (loss and miss on the same obligation). Best-of-N in I.5 unions suites of one tester configuration; App. G runs each model full-stack, not pooled across models. This limits what was found in the sections read and does not show that cross-model pooling is absent from the literature. |
| Konstantinou, Tambon, Papadakis, *On the risk of coding before testing*, arXiv 2607.05139v1, no venue stated (read by Claude: §I, §III–V, §VII-B, §IX–X; Codex: IV-E, VII-B) | Detection requires failing the faulty code and passing the reference (§IV-E), the same soundness logic as QP4. Test-Driven workflow writes tests from the same description as the code (§V). Weakened descriptions (Underspecified, Lexical Vagueness, Syntax/Formatting; MBPP only) change gains over Prompt+Code by 10.6–14.0% (§VII-B). Hypothesises that code and tests "may converge to the same incorrect interpretation" (§X). | Convergence is argued, not measured (§I, §X); faulty implementations are sampled, not tied to a removed obligation; no browser or project-level obligations; multi-model setups explicitly out of scope (§IX). |
| Egashira, Mündler-Sasahara, Müller, Vechev, *TestSuiteBench: Coding Agents Struggle to Generate Strong Test Suites from Specifications*, arXiv 2610.13065v1, 9/10/2026 per the arXiv page (Codex), no venue (read by Claude from the primary HTML on 28/10: abstract, §1–6, App. A.1–A.6, B.1–B.3, C, D.1–D.2, E; Table 5 partly garbled for Claude; Codex read it: official docs V 75.4%, M 4.0%; refined V 86.7%, M 25.5%; 30 instances) | 165 compiled CLI applications (Rust, Go, C/C++); a refined specification (median ~5k words, 23 sections), reference executable, reference tests (median 679) and mutants (median 67), each mutant targeting one requirement (§2.1–2.5). Agents write implementations and test suites from the same specification (§2.6, App. C). Mutation score M after dropping tests that fail on the reference; validity V; reference pass rate R (§2.6). Headline M 19.3–55.5% across six models with V 74–96% and R 65–93% (Table 2). Official documentation instead of the refined specification: Sol M 25.5% → 4.0% on 30 instances (§3.2). **Cross-model pooling (App. A.5, Fig. 12):** of 12,130 mutants, 25% are killed by all three of Opus, Sol and Gemini; the union kills 59% against 54% for Opus alone ("only modest gains"); 41% are killed by none. | Testers write from the full refined specification, not from a request missing one obligation, so A.5 is pooling and shared misses **with complete information**; no per-requirement link between implementation failure (R) and test miss (M); some specification content is dropped only to match skipped tests (App. B.3), not as an experimental removal; mutants are synthetic, not oracle-confirmed losses from generated implementations. |
| Yin, Chen, Wang, Sun, Jin, Song, Zhang, *VerifierBench: Benchmarking the Generation of Executable Verifiers for LLM Agents*, arXiv 2610.28679v1, 19/10/2026, preprint (primary text checked by Codex: §2.2–2.4, §4, limitations; Claude: abstract only) | 222 tasks, 19 models; verifiers reject invalid solutions more reliably than they accept valid ones; case studies of unsupported assumptions; errors persist because agents' self-tests share the verifier's mistaken assumptions (abstract; §4 per Codex). | Per Codex: trace inspection is not a causal intervention and does not measure prevalence; the information given to the verifier generator is not manipulated (abstract describes instruction + environment). Concerns over-restrictive verifiers rather than missed losses. |

Other sources found by the adversarial search of 28/10 (primary text as stated):

| Source (status) | Relevance | Boundary |
|---|---|---|
| Huang, Zhang, Harman, Du, Cui, *Measuring the Influence of Incorrect Code on Test Generation*, arXiv 2409.09464v3 (28/3/2025; under review per the arXiv record; read by Claude from the HTML, §1–8) | Five input conditions for the tester: description, description + correct code, description + incorrect code, correct code, incorrect code (§3.1). With the description, incorrect instead of correct code lowers test accuracy 73.9% → 47.1%, coverage 96.8% → 86.5% and detection 47.4% → 38.1% (averages, test level); on 41 real-world tasks, detection 13.5% (correct code only) vs 7.1% (incorrect code only) (§5.5) | An antecedent for manipulating the information given to the tester (and for QP4 F4); it varies the code shown, not the requirement; no removed obligation; its "misled" measure is criticised by Zhao et al. (see the counting table) |
| Zhao, Zhou, Cohen, *Evaluating and Mitigating the Misguidance Effect of Buggy Code in LLM-Generated Unit Tests*, PACMSE 3 (ISSTA 2026), DOI 10.1145/3832204, arXiv 2607.22883 (read by Claude: §1–4.3 from the HTML, which is truncated in §4.4; §4.2–8 from the PDF, whose first part came back garbled; reference list cut at [51]) | Showing buggy code to the test generator raises misguided tests (pass on buggy, fail on fixed) from 0.46% to 3.84% and lowers effective tests from 8.51% to 2.98% on 318 Defects4J focal methods, 11 models (Table 4); a docstring-first pipeline mitigates it (Tables 6, 8); on fixed code it is comparable to code prompting (§5: CFR 21.30% → 20.10%, FAR 37.45% → 39.04%, line coverage +3.61 pp); 15.09–20.75% of generated docstrings preserve the bug (§4.4). Builds on Huang et al. (arXiv 2409.09464), whose buggy-code metric it argues overstates misguidance (§2.6, §7) | Close antecedent for F4 (code anchoring), at ISSTA itself; unit tests on Defects4J focal methods, no omitted requirement; threats (§6) name stateful, dependency-rich code where method docstrings may omit needed information; in the sections examined (§6–7), incomplete requirements are named only as a threat for stateful, dependency-rich code; no claim is made about the wider literature |
| Qi, Liu, Lin, Zhou, Sun, Dong, *Benchmarking LLM Agents for Behaviorally Adequate Test Generation from Software Requirements* (Req2Test-Bench), arXiv 2610.36584v1, 27/10/2026 (Claude: abstract only, HTML and PDF blocked by robots for Claude; Codex read the primary HTML §3.2–4.3, §5.4–5.5, §6 and Tables 3–4) | 5,086 instances constructed from Gherkin requirements in 8 projects, but 2,051 evaluated (780 Features, one per group sharing the same StepDefinitions, §4.3); the 82.8% passing and 33.8% behaviorally adequate (kill every mutant the developer test kills) are means over the 8 projects in that evaluated subset, not over 5,086 generations; diminishing returns from scaling agents (abstract). **Informational intervention (§5.5, per Codex):** an author clarifies setup and expected outcomes using the ground truth, and kill-complete rises 2 → 14 of 17 (Algorand) and 25 → 36 of 60 (python-docx); §6 admits that a narrower reading can be valid where a test is kill-incomplete | Close to QP4 as an intervention on the information given to test writers, but not a controlled removal of one obligation, and no implementation loss or joint escape. §3.2 excludes browser and live-service scenarios. Adequacy is relative to the developer test's kills, not universal semantic truth |
| Ding, *What the Specification Did Not Say: Specification-Oracle Gaps in Test-Graded Coding-Agent Benchmarks*, arXiv 2610.30635v1, 22/10/2026 (Claude: abstract only, HTML and PDF blocked by robots; Codex read the primary HTML §4.1–9, Limitations and Ethics; Appendix I not read) | Benchmarks grade on names, paths or literals the specification omits. The **main formal extractor** G(o) covers dependencies on identifiers, paths and literals; behaviour the specification leaves open is outside that extractor (§4.1–4.2), but not outside the paper: Limitations reports a separate text heuristic for unspecified behaviour, and §6.5 attributes 28 of 40 hard unflagged cases to behaviour left open. On SWE-Milestone, 80.6% vs 48.4% failure is an **association** in comparable units with new tests; the reported OR 4.64 is an odds ratio, not a risk ratio. §6.2 is an offline mechanical intervention without agents: renaming a hidden identifier in the reference breaks compilation in 126 of 128 Go units. §7: specification addenda are generated, and their effect on agents has not been evaluated with new agent runs. §6.4: blind, held-out expert review gives precision 58/65 and recall 13/14, with wide intervals (all per Codex) | Evaluator-side. Our arm C is an **analogous informational tension** (the frozen oracle enforces an obligation the request omits), not an instance of the main formal extractor's definition; the paper's separate heuristic and §6.5 show it also discusses behavioural gaps, which is closer to arm C. QP4 reads arm-C failures as loss of a documented obligation relative to A and B, not as agent error on an uninformed requirement |
| Li, Liu, Lyu, Cheng, Guan, *Ungrounded Enforcement: When Agent Benchmarks Grade on Conditions Their Specifications Do Not Determine*, NeurIPS 2026 workshop "Who Verifies the Agents?" (title, authors and OpenReview id V8QjW4TS6i confirmed on the workshop schedule page; abstract and paper not reachable from this session) | By title, the same evaluator-side gap as Ding | Content unknown; nothing is inferred beyond the title. Unreachable is an access limit, not absence |
| Gao, Zhou, *Can Agent Benchmarks Support Their Scores? Evidence-Supported Bounds for Interactive-Agent Evaluation*, arXiv 2605.10448v1 (read by Claude: main text; appendices not reached) | Outcome-evidence gaps and benchmark conflicts in five interactive benchmarks (e.g. τ³-bench retail: 24 conflicts in 300 records) | Context for evaluator validity; agents' tests not studied |

Context sources (not close antecedents for the joint claim): TiGanEval (agent success
under partial instructions; agents' tests not measured), TRACE (verifier brittleness;
§5 read by Codex from the primary HTML: the main test uses 88 new τ²-bench tasks, 12
airline and 76 retail, three repetitions per condition; identical reruns flip 14.7–16.3%
of outcomes for three agents and 35.6% for a fourth (Laguna), so 15–36% is a per-agent
range in that setting, not a universal rate; Telecom 108 is a separate exploratory
extension; 7 of 8 contrasts within ±0.10, 6 of 8 after Bonferroni; context only, it does
not authorise any τ² rerun), Policy Loopholes (evaluator-side policy ambiguity in τ²-bench), Doc2OracLL
(documentation in unit-level oracle generation, with and without code), EvalMutationBench
(software artefact; synthetic labels), ClarifyCodeBench (clarifying deletion-only
underspecification).

## Claim-by-claim map

| QP4 claim (exploratory) | Our evidence | Closest antecedent | What is specific here | Pending |
|---|---|---|---|---|
| F1. Pooling testers does not substitute the missing obligation | Five testers, two providers: union from the incomplete request 0.50 vs one complete-source tester 0.82, diff −0.32 [−0.57, −0.09], p 0.047 (8 projects) | Haeri App. I.5: unioned ungrounded suites of one configuration reach 15/29 (k = 2–8) vs 29/29 with the specification. TestSuiteBench App. A.5: **cross-model** pooling of three agents from the complete specification adds about 5 points (54% → 59%); Req2Test-Bench (abstract): diminishing returns from scaling agents | Cross-model pooling itself is **not** specific (TestSuiteBench A.5). What remains specific is the contrast: pooling from the request missing one obligation against a single tester given the complete requirement, on browser journeys over oracle-confirmed losses of that obligation. A replication and extension, not a new phenomenon | Confirmatory H-b; power depends on the smallest effect of interest (corrected simulation) |
| F2. Misses are shared beyond marginal independence | 60.5% of 81 losses missed by all five vs 43.7% under marginal independence; within-requirement expectation 58.6% | TestSuiteBench App. A.5: 41% of mutants killed by none of three models, from the complete specification; VerifierBench (shared assumptions, case studies); Konstantinou (argued convergence) | Shared misses across models are **not** specific (TestSuiteBench A.5). Specific: misses of loss of the obligation removed from the testers' source, compared with an independence expectation; largely explained by between-requirement heterogeneity, so it says misses concentrate on the same requirements, not that testers err alike within a requirement | Report as concentration by requirement; no causal mechanism |
| F3. Rules no generator recovers are rarely detected | Descriptive contrast 0.048 (14) vs 0.242 (11); ρ 0.59, much of it from 11 zero–zero requirements; post hoc | Konstantinou §X (hypothesis only); VerifierBench (same-agent self-tests); TestSuiteBench reports R and M per model only, with no per-requirement link | Generator and tester are different models reading the same incomplete request, measured per requirement against frozen oracles | Truncated by eligibility; H-c estimation only; mechanism waits for the #185 human audit |
| F4. Showing the mutant's code anchors tests on it | Code-anchored suites reject the correct reference in 17–34 of 50 per tester | Zhao, Zhou, Cohen (ISSTA 2026): buggy code raises misguided tests and suppresses effective ones; Haeri App. E; Konstantinou RQ1 | Browser setting, five testers, shown mutant is an oracle-confirmed loss of the removed obligation | Replication; no novelty claim |
| RQ5. The omitted obligation is retrievable from project docs | Semantic gold (agent-coded, not blind): top 5 for 17/25 with the full request, 4/25 with its first sentence | Doc2OracLL; TestSuiteBench §3.2 (official docs instead of the refined specification: M 25.5% → 4.0%); Haeri App. I.2 (rules derived from the ticket recover 47%) | Retrieval of the specific removed obligation from the project's own documentation snapshot | Detection with retrieved documentation is untested; no pilot authorised |
| Design: same obligation in both sources, with rewording control and frozen browser oracles | 46 requirements, 552 implementations; A/B/C; 25 QP4 requirements | Haeri has the same-source structure on functions and on real library utilities (I.8, I.9); Konstantinou at benchmark-task level | Project documentation obligations, one controlled removal, rewording control, browser oracles frozen before generation, joint escape | The combination is the claim; no priority is asserted over its parts. Arm C creates an informational tension analogous to Ding's specification–oracle gaps (not an instance of his formal definition), to be framed explicitly |

## How each study counts detection (denominators and soundness)

Rates are not comparable across these designs and are not imported into QP4; the table
records only how each one counts.

| Study (sections) | Unit tested against | Soundness / filtering | Detection numerator and denominator | "Misled" notion |
|---|---|---|---|---|
| Huang, Zhang, Harman, Du, Cui, *Measuring the Influence of Incorrect Code on Test Generation*, arXiv 2409.09464v3 (28/3/2025; the arXiv record says under review, no venue assumed; read by Claude from the HTML, §1–8, references truncated; §3.1 per Codex) | Correct code (accuracy, coverage); a constructed set of LLM-generated incorrect solutions, or pre-patch code for BugsInPy and SWE-bench (§3.4) | Two levels. Task level (§3.4.1): a task's tests count as correct only if all of them pass on the correct code. Test level (§3.4.2–3.4.3): coverage and detection count only individual tests that pass the correct code. The exact denominator and the treatment of excluded tasks are not stated in the text and were not checked in code | Percentage of bug-set programs detected by correct tests, reported at test and task level; "detected" is implied (a correct test failing on the buggy program) rather than defined (§3.4.3) | Share of tests that pass the incorrect code (RQ3, §5.3); denominator not stated |
| Zhao, Zhou, Cohen (ISSTA 2026), arXiv 2607.22883 (§2.6, §7) | Buggy and fixed version of each Defects4J focal method | Each test labelled by its result on both versions (Table 2) | Effective tests: fail on buggy, pass on fixed; counted per model and condition (Table 4) | Misguided: pass on buggy, fail on fixed. The authors criticise Huang's measure (all buggy-passing tests) as overstating misguidance, since over 90% of those tests are true negatives that pass on both versions (§2.6, Table 3; §7); this is a critique of the metric, not a refutation of Huang's results |
| Konstantinou, Tambon, Papadakis, arXiv 2607.05139 (§IV-E) | One faulty implementation per task and the reference | Test level: a detecting test must fail on the faulty code and pass on the reference | Detection per faulty implementation | — |
| TestSuiteBench, arXiv 2610.13065 (§2.6) | Reference executable and its mutants | Test level: tests that fail on the reference are dropped before scoring; validity V reported separately | Mutation score M: killed mutants / mutants | — |
| Qi, Liu, Lin, Zhou, Sun, Dong, Req2Test-Bench, arXiv 2610.36584v1 (§3.3–4.3, Tables 3–4, per Codex) | Developer-written tests and mutants for each evaluated instance; 2,051 evaluated instances (780 Features, §4.3) out of 5,086 constructed | Pass@1 uses N_exec, the instances executed after infrastructure exclusions | KillComplete@1 uses the planned population N; a test that does not pass is never kill-complete; project means with equal weight per project | — |
| **QP4** (`scripts/mutation_adequacy.py`) | Correct reference, oracle-confirmed mutants (arm-C losses of the target obligation) and recovered implementations of the same requirement | **Suite level:** a suite is sound only if it is quiet on the reference; unusable or unsound suites stay in the denominator as zero; an error alarm on the reference makes the suite unsound in every sensitivity | Per requirement: killed confirmed mutants / confirmed mutants, mean over suites (H-a), or any sound suite of a pool (H-b, Q1); equal weight per requirement | Not used. Alarms on recovered implementations are reported separately (F5) |

Req2Test-Bench §4.3 allows reruns per provider and regeneration after leakage under its
own rules (per Codex). That is an external contract of that study and gives no
authorisation for reruns or regeneration in QP4, where each slot is attempted once.

Consequences: on the same batch of candidate tests, zeroing a whole suite that alarms on
the reference is more restrictive than keeping its individually valid tests (the
test-level variants of Huang, TestSuiteBench and Konstantinou). Huang's task-level
variant (all tests must pass on the correct code) is closer to QP4's suite-level rule,
but its exact denominators were not checked. Across studies the rates are not
comparable, and no ordering of strictness or performance between studies is claimed.

## Threats to QP4 raised by the antecedents (synthesis)

Each item names the source and its reading status; none is a new result.

1. **Arm C enforces what the request omits.** Ding (abstract; §4.1–9 per Codex) treats
   grading on unstated dependencies as a benchmark gap, with a formal extractor for
   identifiers, paths and literals and a separate heuristic for unspecified behaviour;
   Ungrounded Enforcement is known only by its title, and nothing about its content is
   assumed. QP4's arm C is an analogous informational tension by design.
   Response available in the design: arm A and the rewording control B, the obligation
   is documented in the project, and arm-C failures are reported as loss relative to A
   and B, not as agent error. Residual threat: readers may still see C as unfair grading.
2. **Adequacy is relative to the oracle.** TestSuiteBench (read) and Req2Test-Bench (§6
   per Codex) define adequacy against reference tests or mutants, not universal semantic
   truth. QP4's frozen browser oracles are authored for this study; qualification with
   positive and negative controls mitigates but does not remove this.
3. **Information interventions already exist.** Huang (code shown, read), Haeri (rules
   removed, read), Req2Test-Bench §5.5 (clarification from the ground truth, per Codex),
   Konstantinou §VII-B (weakened descriptions, read). QP4's specificity is narrower: one
   documented obligation removed from the source of both implementation and tests.
4. **Scope.** TestSuiteBench covers compiled CLI applications; Req2Test-Bench §3.2
   excludes browser and live-service scenarios (per Codex); QP4 covers web pages with a
   fixed scaffold, not full applications. Generalisation either way is not shown.
5. **Mutants.** TestSuiteBench and Haeri use synthetic or model-produced bugs; QP4 uses
   oracle-confirmed losses from generated implementations, but only for requirements that
   pass the eligibility filter, which defines a conditional population.
6. **Counting choices change rates.** Huang vs Zhao §2.6 show that the definition of a
   misled or detecting test changes conclusions; QP4 fixes suite-level soundness and
   reports assertion-only and per-tester sensitivities.
7. **Pooling and shared misses are not specific** (TestSuiteBench A.5, Haeri I.5).
8. **Code anchoring is known** (Zhao, Huang, Haeri App. E, Konstantinou RQ1); F4 is a
   replication.
9. **Run-to-run variance.** TRACE §5 (per Codex) finds that identical reruns flip 14.7–16.3% of
   outcomes for three agents and 35.6% for a fourth in its setting. In QP4, each slot is
   attempted once (no rerun of the same slot), but there are repetitions per requirement
   and condition: two generators × two repetitions per arm in the 46-case collection, and
   two suites per tester and source. Variation across those repetitions is observable;
   what is not observed is the variance of an identical rerun of one slot.

## Priority

Priority remains open. The map records what the sections read do and do not contain; it
is not an exhaustive search, and no claim of being first rests on it.

## Consequences for the paper text

1. F1 must cite Haeri App. I.5 as the antecedent for "more samples do not replace the
   specification" and present the five-model, two-provider pooling as an extension. The
   boundary with Haeri is browser journeys, one removed obligation and joint escape, not
   "functions versus real projects" (their I.8 and I.9 use real library utilities). Their
   HumanEval+ null (App. H, Table 10) should be cited as a limit on generality.
2. The same-source structure must be credited to Haeri (ticket for code and ungrounded
   tester) and Konstantinou (Test-Driven workflow); our design differs in the controlled
   removal of one documented obligation and in measuring loss and miss on that obligation.
3. F2 should be worded as concentration of misses on the same requirements, not as a
   shared error mechanism.
4. VerifierBench is cited as a preprint for shared assumptions between verifiers and
   self-tests (case studies), not as evidence of prevalence.
5. Cross-model pooling and shared misses must cite TestSuiteBench App. A.5; F1 and F2 are
   specific only in comparing an incomplete source with a complete one.
6. F4 must cite Zhao, Zhou and Cohen (ISSTA 2026) as the closest antecedent for code
   anchoring.
7. The threats section must say that arm C creates an informational tension analogous
   to Ding's specification–oracle gaps (his main extractor G(o) audits identifier, path and
   literal dependencies, §4.1–4.2; a separate text heuristic and §6.5's 28 of 40 hard
   unflagged cases concern behaviour left open), and cite Ungrounded Enforcement once read: QP4 measures loss of a documented obligation relative to A and B, not agent
   error on an uninformed requirement.
8. Req2Test-Bench §5.5 must be cited as a close informational intervention on test
   writers (clarifying setup and outcomes from the ground truth), distinct from removing
   one obligation and measuring implementation loss and joint escape.

## Reading status and backlog (consolidated 28/10)

Read, by source and reader (details in the tables above and in the literature matrix):
- Claude: Haeri (§3, §4.5, §5–6, App. A, E, I.2–I.5, from a truncated PDF);
  Konstantinou (§I, III–V, VII-B, IX–X); TestSuiteBench (§1–6, App. A–E); Zhao
  (§1–8 across HTML and PDF); Huang (§1–8); Doc2OracLL (v2 summary); Policy Loopholes;
  Gao and Zhou (main text); abstracts only of TRACE, VerifierBench, Req2Test-Bench and
  Ding (their HTML/PDF are blocked for this session).
- Codex: Haeri HTML (§4.5, App. G, H, I.5–I.9); TRACE §5; VerifierBench §2.2–2.4, §4,
  limitations; TestSuiteBench §3.2 and Table 5; Req2Test-Bench §3.2–4.3, §5.4–5.5, §6,
  Tables 3–4, plus introduction and related work (works cited there are pointers, not
  individually verified primaries); Ding §4.1–9, Limitations and Ethics; Zhao targeted
  checks (§2.6, §4.4, §5/Table 12, §6); Huang §3.1, §3.4.1–3.4.3; EvalMutationBench
  README.

Reading that can continue (no human decision needed):
- Ding Appendix I (not read by either).
- Req2Test-Bench sections outside those listed; the works it cites, if any becomes a
  close antecedent, read individually from their primaries.
- Ungrounded Enforcement abstract or paper (title, authors and OpenReview id only).
- TRACE beyond §5 and VerifierBench beyond the sections above, if the paper text needs
  them.
- Cross-model pooling was found in TestSuiteBench App. A.5; no exhaustive search for
  other instances was made.

Decisions that belong to people (not to Claude, Codex or this map):
- Dante and Márcio: tester list and k; smallest H-b effect of interest or a practical
  margin with its own test; eligible-sample option; whether H-b stays confirmatory;
  workshop submission by 13/11; budget for any new collection or for the RQ5 pilot.

Human audit work (not substitutable by models):
- The #185 blind audit with a second human coder.
- A blind check of the 25 semantic-gold quotes for RQ5 (could join that audit).

Reviewed by Codex on PR #234 (reproduction or text check, not independent validation of
every modelling choice): coupling analysis and its hashed inputs; retrieval snapshot
verification, committed-blob indexing and semantic-gold evidence; power simulation v2 and
the H-b decision sheet; this map and the matrix. PR #234 is open and not merged.

No priority or novelty is established by this package; the map records what the sections
read contain.

Unchanged throughout: H1 and H2; the 25-requirement, 8-project QP4 results are post hoc;
zero and None stay distinct; τ² is out of scope.
