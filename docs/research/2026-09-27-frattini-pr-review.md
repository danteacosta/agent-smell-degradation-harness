# Research: review of the endpoint rationale in PR 107

- **Slug:** `2026-09-27-frattini-pr-review`
- **Date:** 2026-09-27
- **Status:** complete
- **Triggered by:** Review of the open endpoint-gate pull request.
- **Informed:** [cross-case E2E synthesis](e2e-cross-case-synthesis-20260927.md) and PR 107 review.

## Question

Does the primary study support the proposed distinction between downstream
task outcomes, rather than transfer an effect size to coding agents?

## Sources

### [Frattini et al., Applying bayesian data analysis for causal inference about requirements quality](https://link.springer.com/article/10.1007/s10664-024-10582-1)

- **Authors / Org:** Julian Frattini and coauthors.
- **Type:** peer-reviewed academic paper, primary source.
- **Published:** online 2024; 2025 journal volume.
- **Accessed:** 2026-09-27.
- **Relevance:** high.
- **What this contributed:** The paper reports 25 human participants deriving
  domain models from four short requirements, with passive voice and
  ambiguous pronouns as treatments. Its results vary by treatment and
  domain-model attribute; passive voice had a smaller effect than the
  authors expected. The paper does not study coding agents, browser E2E
  behavior, or the thesis's omission treatment. It supports defining the
  downstream task and outcome before a general quality claim, not borrowing
  an effect size.

## Synthesis

PR 107's task-specific reading is supported by the primary paper. Its
endpoint decision gate should say **confirmatory** candidate admission
unambiguously, because exploratory source-screening and E2E instrument
qualification can continue without changing formal H1.

## Downstream uses

- [Cross-case synthesis](e2e-cross-case-synthesis-20260927.md).
- [PR 107](https://github.com/danteacosta/agent-smell-degradation-harness/pull/107) review.
