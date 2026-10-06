# Shared-omission extension: feasibility and design audit

Reviewed on 2026-10-06. No model call was made by this audit. Separately,
the three-arm collection in PR #184 had already started before the audit's
factorial proposal was opened. This note does not revise that frozen study.

## External evidence

**Hossain, Taylor and Dwyer, Doc2OracLL: Investigating the Impact of
Documentation on LLM-Based Test Oracle Generation, PACMSE/FSE 2025, DOI
[10.1145/3729354](https://doi.org/10.1145/3729354).** Peer-reviewed primary
study. The authors fine-tuned ten models, ablated Javadoc components and tested
unseen bug detection on 374 Defects4J samples. Documentation usually improved
oracle accuracy; the description and `@return` content contributed most.
Documentation-only oracles detected 68 bugs in their comparison and could
match or outperform contexts containing the method under test. The authors
explicitly warn that a faulty implementation can anchor an oracle to observed
rather than intended behavior. Limits include Java/Javadoc tasks, fine-tuned
models, exact-match training metrics and author-coded qualitative categories.

**Tzafrir Rehan, Test-Driven AI Agent Definition (TDAD), arXiv:2603.08806.**
Preprint. The abstract describes tests compiled from behavioral specifications
and semantic prompt mutation. It prevents a generic novelty claim for mutation
testing of agent evals. The benchmark and its license have not been reproduced.

## Consequence for the existing experiment

PR #180 showed that tests generated from complete requirements detect confirmed
losses much more often than tests generated from incomplete requests. Its code
arm received a correct implementation, so it measured regression-test
generation from a known-good version rather than review of a defective PR.

The first version of PR #181 compared complete requirement + scaffold against
incomplete request + defective code. That comparison changed requirement
completeness and implementation context together. Doc2OracLL makes this
confounding material: code can independently anchor the generated oracle.

PR #184 completed the original three-arm design: scores were 0.760 for
complete requirement plus scaffold, 0.100 for incomplete requirement plus
scaffold, and 0.040 for incomplete requirement plus mutant code. The first
contrast holds scaffold constant; the complete-scaffold versus incomplete-code
contrast changes both factors. These results remain exploratory and are
preserved under the original protocol.

The proposed, unexecuted successor in PR #183 would use a 2×2 design. Both code conditions see
the same seeded confirmed mutant; only the requirement changes. Both scaffold
conditions are regenerated in the same batch. The primary contrast is complete
versus incomplete requirement while mutant code is held constant. Code-context
effects and the factorial interaction are reported separately.

The proposal is for 200 fresh calls and 1,528 planned suite/page pairs,
not a 50-call top-up to the completed 150-call study. It requires a separate
human decision, fresh freeze and result packet. It does not change H1/H2,
reuse old calls, generate new implementations or convert the selected sample
into confirmatory evidence. The proposal is informed by known results.

## Correction to the execution claim

The original audit incorrectly described an inevitable overwrite failure in
the frozen three-arm adapter. That code delegates once to `ma.execute`;
the claim is not supported by that implementation and is withdrawn.
Single-write four-arm finalization was needed while developing the factorial
adaptation, not evidence that the original collector was broken. The completed
PR #184 study and its frozen scripts, receipts and results are unchanged.
