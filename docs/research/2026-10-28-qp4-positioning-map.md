# QP4 positioning: evidence map against close antecedents

Date: 2026-10-28. Status: working document for review by Codex, Dante and Márcio. It does
not claim novelty from an absent search, and it does not turn planning into decisions.
Reading status of every source is in `docs/research/literature-matrix.md` (section of
28/10). "Read by Claude" below means the sections named were read through a fetch of the
primary PDF in this session; arXiv HTML and abstract pages were mostly not reachable.

## The narrow contribution being positioned

One obligation, documented in a real project, is removed from the request. The same
incomplete request drives (a) the implementation and (b) the review tests. Against browser
oracles frozen before generation, the study separates implementation loss, conditional
detection by tests, and joint escape per requirement, with a meaning-preserving rewording
control. All QP4 findings so far are exploratory and post hoc on 25 requirements.

## Close antecedents, what they already show, and what is left

| Source (status) | What it already shows that overlaps QP4 | What it does not do (as far as read) |
|---|---|---|
| Haeri and Ghelichi, *Specification Grounding Drives Test Effectiveness for LLM Code*, arXiv 2607.06636 (read by Claude from a truncated PDF fetch: §3.1–3.4, §4.5, §5–6, App. A, E, I.2–I.5; read by Codex from the primary HTML v1, including App. G, H/Table 10, I.5/Table 15, I.6, I.8 and I.9, which the PDF fetch did not reach) | The code model sees only the ticket; the ungrounded tester also writes from the ticket, so the **same source** feeds both (§3.1, §3.3). Removing validation rules drops detection 30/30 → 6/30 (§4.5). Showing code to an ungrounded tester drops detection 7/24 → 0/24, grounded stays 24/24 (App. E). Rules derived from the ticket recover 47% of detection (App. I.2). **Best-of-N:** unioning ungrounded suites gives 15/29 from k = 2 to 8 against 29/29 with the specification (App. I.5, Table 15). Beyond the 26 core functions: six stateful, multi-step tasks (I.6), transformers/NLTK utilities at fixed commits (I.8) and four PyPA packaging utilities with an external oracle (I.9). A null on HumanEval+: grounded 13/22 vs free+ 14/22 (App. H, Table 10). "Small functions vs real projects" is **not** a sufficient boundary: I.8 and I.9 use real library utilities with external oracles. The distinction that holds in the sections read is narrower: no browser journeys over project-documented obligations, no single controlled removal of one obligation with a rewording control, and no joint-escape measure (loss and miss on the same obligation). Best-of-N in I.5 unions suites of one tester configuration; App. G runs each model full-stack, not pooled across models. This limits what was found in the sections read and does not show that cross-model pooling is absent from the literature. |
| Konstantinou, Tambon, Papadakis, *On the risk of coding before testing*, arXiv 2607.05139v1, no venue stated (read by Claude: §I, §III–V, §VII-B, §IX–X; Codex: IV-E, VII-B) | Detection requires failing the faulty code and passing the reference (§IV-E), the same soundness logic as QP4. Test-Driven workflow writes tests from the same description as the code (§V). Weakened descriptions (Underspecified, Lexical Vagueness, Syntax/Formatting; MBPP only) change gains over Prompt+Code by 10.6–14.0% (§VII-B). Hypothesises that code and tests "may converge to the same incorrect interpretation" (§X). | Convergence is argued, not measured (§I, §X); faulty implementations are sampled, not tied to a removed obligation; no browser or project-level obligations; multi-model setups explicitly out of scope (§IX). |
| TestSuiteBench, arXiv 2610.13065 (read by Codex: §3.2; not reachable from Claude's session) | Implementations and tests generated from the same specification; ablation of official documentation against a refined specification (§3.2). | Not verified by Claude; relation to removed obligations and joint escape unknown here. |
| Yin, Chen, Wang, Sun, Jin, Song, Zhang, *VerifierBench: Benchmarking the Generation of Executable Verifiers for LLM Agents*, arXiv 2610.28679v1, 19/10/2026, preprint (primary text checked by Codex: §2.2–2.4, §4, limitations; Claude: abstract only) | 222 tasks, 19 models; verifiers reject invalid solutions more reliably than they accept valid ones; case studies of unsupported assumptions; errors persist because agents' self-tests share the verifier's mistaken assumptions (abstract; §4 per Codex). | Per Codex: trace inspection is not a causal intervention and does not measure prevalence; the information given to the verifier generator is not manipulated (abstract describes instruction + environment). Concerns over-restrictive verifiers rather than missed losses. |

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
underspecification). Ungrounded Enforcement remains unread.

## Claim-by-claim map

| QP4 claim (exploratory) | Our evidence | Closest antecedent | What is specific here | Pending |
|---|---|---|---|---|
| F1. Pooling testers does not substitute the missing obligation | Five testers, two providers: union from the incomplete request 0.50 vs one complete-source tester 0.82, diff −0.32 [−0.57, −0.09], p 0.047 (8 projects) | Haeri App. I.5: unioned ungrounded suites of one configuration reach 15/29 (k = 2–8) vs 29/29 with the specification | Pooling across models and providers, on browser journeys, over oracle-confirmed losses of one removed documented obligation. This is a **replication and extension**, not a new phenomenon; cross-model pooling was not found in the sections read, which is not evidence that it is absent elsewhere | Confirmatory H-b; power depends on the smallest effect of interest (corrected simulation) |
| F2. Misses are shared beyond marginal independence | 60.5% of 81 losses missed by all five vs 43.7% under marginal independence; within-requirement expectation 58.6% | VerifierBench (shared assumptions, case studies); Konstantinou (argued convergence) | A quantitative joint-miss estimate; but it is largely explained by between-requirement heterogeneity, so it says misses concentrate on the same requirements, not that testers err alike within a requirement | Report as concentration by requirement; no causal mechanism |
| F3. Rules no generator recovers are rarely detected | Descriptive contrast 0.048 (14) vs 0.242 (11); ρ 0.59, much of it from 11 zero–zero requirements; post hoc | Konstantinou §X (hypothesis only); VerifierBench (same-agent self-tests) | Generator and tester are different models reading the same incomplete request, measured per requirement against frozen oracles | Truncated by eligibility; H-c estimation only; mechanism waits for the #185 human audit |
| F4. Showing the mutant's code anchors tests on it | Code-anchored suites reject the correct reference in 17–34 of 50 per tester | Haeri App. E; Konstantinou RQ1 | Browser setting, five testers | Replication; no novelty claim |
| RQ5. The omitted obligation is retrievable from project docs | Semantic gold (agent-coded, not blind): top 5 for 17/25 with the full request, 4/25 with its first sentence | Doc2OracLL; TestSuiteBench §3.2; Haeri App. I.2 (rules derived from the ticket recover 47%) | Retrieval of the specific removed obligation from the project's own documentation snapshot | Detection with retrieved documentation is untested; no pilot authorised |
| Design: same obligation in both sources, with rewording control and frozen browser oracles | 46 requirements, 552 implementations; A/B/C; 25 QP4 requirements | Haeri has the same-source structure on functions and on real library utilities (I.8, I.9); Konstantinou at benchmark-task level | Project documentation obligations, one controlled removal, rewording control, browser oracles frozen before generation, joint escape | The combination is the claim; no priority is asserted over its parts |

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

## Open items (concrete)

- Read TestSuiteBench beyond §3.2 from a session that can reach arXiv. (TRACE closed by
  Codex from the primary HTML §5; see context sources.)
- Read Ungrounded Enforcement once the NeurIPS page or a preprint is reachable.
- Haeri and Ghelichi: Codex read I.5–I.9, G and H in the HTML; no cross-model pooling in
  those sections. Other sources were not searched exhaustively for it.
- Blind check of the RQ5 semantic gold quotes (short; can join a human audit).
- Decisions for Dante and Márcio: smallest H-b effect of interest (fixes N), the
  eligible-sample option, tester list and budget, workshop submission by 13/11.
- #185 blind human audit stays pending; nothing here substitutes it.
