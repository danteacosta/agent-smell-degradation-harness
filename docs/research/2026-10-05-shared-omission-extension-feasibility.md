# Shared-omission extension: feasibility and design audit

Reviewed on 2026-10-06. No new model call was made in this audit.

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

The corrected extension therefore uses a 2×2 design. Both code conditions see
the same seeded confirmed mutant; only the requirement changes. Both scaffold
conditions are regenerated in the same batch. The primary contrast is complete
versus incomplete requirement while mutant code is held constant. Code-context
effects and the factorial interaction are reported separately.

This costs 200 calls rather than 150, but removes a larger interpretability risk
before collection. It does not change H1/H2, reuse old calls, generate new
implementations or convert this selected exploratory sample into confirmatory
evidence.
