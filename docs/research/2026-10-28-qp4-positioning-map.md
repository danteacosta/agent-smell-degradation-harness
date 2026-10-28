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
| Zhao, Zhou, Cohen, *Evaluating and Mitigating the Misguidance Effect of Buggy Code in LLM-Generated Unit Tests*, PACMSE 3 (ISSTA 2026), DOI 10.1145/3832204, arXiv 2607.22883 (read by Claude: §1–4.3 from the HTML, which is truncated in §4.4; §4.2–8 from the PDF, whose first part came back garbled; reference list cut at [51]) | Showing buggy code to the test generator raises misguided tests (pass on buggy, fail on fixed) from 0.46% to 3.84% and lowers effective tests from 8.51% to 2.98% on 318 Defects4J focal methods, 11 models (Table 4); a docstring-first pipeline mitigates it (Tables 6, 8); on fixed code it is comparable to code prompting (§5: CFR 21.30% → 20.10%, FAR 37.45% → 39.04%, line coverage +3.61 pp); 15.09–20.75% of generated docstrings preserve the bug (§4.4). Builds on Huang et al. (arXiv 2409.09464), whose buggy-code metric it argues overstates misguidance (§2.6, §7) | Close antecedent for F4 (code anchoring), at ISSTA itself; unit tests on Defects4J focal methods, no omitted requirement; threats (§6) name stateful, dependency-rich code where method docstrings may omit needed information; related work (§7) does not treat incomplete requirements |
| Qi, Liu, Lin, Zhou, Sun, Dong, *Benchmarking LLM Agents for Behaviorally Adequate Test Generation from Software Requirements* (Req2Test-Bench), arXiv 2610.36584v1, 27/10/2026 (Claude: abstract only, HTML blocked by robots for Claude; Codex read the primary HTML §3.2, §5.4–5.5, §6) | 5,086 Gherkin requirements from 8 projects; best configuration passes 82.8% but only 33.8% are behaviorally adequate (kill every mutant the developer test kills); diminishing returns from scaling agents (abstract). **Informational intervention (§5.5, per Codex):** an author clarifies setup and expected outcomes using the ground truth, and kill-complete rises 2 → 14 of 17 (Algorand) and 25 → 36 of 60 (python-docx); §6 admits that a narrower reading can be valid where a test is kill-incomplete | Close to QP4 as an intervention on the information given to test writers, but not a controlled removal of one obligation, and no implementation loss or joint escape. §3.2 excludes browser and live-service scenarios. Adequacy is relative to the developer test's kills, not universal semantic truth |
| Ding, *What the Specification Did Not Say: Specification-Oracle Gaps in Test-Graded Coding-Agent Benchmarks*, arXiv 2610.30635v1, 22/10/2026 (Claude: abstract only, HTML blocked by robots; Codex read the primary HTML §4.1–4.2) | Benchmarks grade on names, paths or literals the specification omits; on SWE-Milestone, units with an unstated, non-inferable dependency fail in 80.6% of runs vs 48.4% (abstract). The audited set G(o) covers dependencies on identifiers, paths and literals; behaviour the specification leaves open is outside that set (§4.1–4.2, per Codex) | Evaluator-side. Our arm C is an **analogous informational tension** (the frozen oracle enforces an obligation the request omits), not an instance of Ding's formal definition. QP4 reads arm-C failures as loss of a documented obligation relative to A and B, not as agent error on an uninformed requirement |
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
   to Ding's specification–oracle gaps (his G(o) audits identifier, path and literal
   dependencies; open behaviour is outside it, §4.1–4.2), and cite Ungrounded Enforcement
   once read: QP4 measures loss of a documented obligation relative to A and B, not agent
   error on an uninformed requirement.
8. Req2Test-Bench §5.5 must be cited as a close informational intervention on test
   writers (clarifying setup and outcomes from the ground truth), distinct from removing
   one obligation and measuring implementation loss and joint escape.

## Open items (concrete)

- TestSuiteBench: read (see table); Table 5 confirmed by Codex (official docs V 75.4%,
  M 4.0%; refined V 86.7%, M 25.5%; 30 instances). TRACE closed by Codex from §5.
- Ding §4.1–4.2 and Req2Test-Bench §3.2, §5.4–5.5, §6 read by Codex; the rest of both
  remains unread by either. Zhao et al.: §1–8 read by Claude (HTML §1–4.3, PDF §4.2–8);
  Huang et al. (arXiv 2409.09464), its antecedent, not yet read.
- Ungrounded Enforcement: title, authors and OpenReview id confirmed; read the abstract or
  paper when reachable.
- Haeri and Ghelichi: Codex read I.5–I.9, G and H in the HTML; no cross-model pooling in
  those sections. Other sources were not searched exhaustively for it.
- Blind check of the RQ5 semantic gold quotes (short; can join a human audit).
- Decisions for Dante and Márcio: smallest H-b effect of interest (fixes N), the
  eligible-sample option, tester list and budget, workshop submission by 13/11.
- #185 blind human audit stays pending; nothing here substitutes it.
