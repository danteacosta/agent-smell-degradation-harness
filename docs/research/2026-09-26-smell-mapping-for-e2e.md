# Research: mapping the E2E manipulation to requirement-smell literature

- **Slug:** `2026-09-26-smell-mapping-for-e2e`
- **Date:** 2026-09-26
- **Status:** complete for the present omission pilots
- **Triggered by:** request to link each experiment to a literature-mapped smell
- **Informed:** [E2E mapping](../thesis/e2e-smell-mapping-20260926.md)

## Question

Which published smell construct accurately describes experiments that remove
one testable obligation from an otherwise source-grounded requirement?

## Sources

### [Alemneh and Berhanu, *Software Requirement Smells and Detection Techniques: A Systematic Literature Review*](https://doi.org/10.2478/cait-2024-0037)
- **Authors / Org:** Esubalew Alemneh and Fekerte Berhanu
- **Type:** academic systematic literature review, secondary synthesis of 19 studies
- **Published:** 2024
- **Accessed:** 2026-09-26
- **Relevance:** high
- **What this contributed:** Table 3 groups incomplete requirement, missing condition,
  incomplete system response, and partial content under incompleteness and
  language-related smells. This supports a broad family label for our controlled
  clause deletion, while the review explicitly reports no comprehensive,
  universally accepted smell classification. Our subtypes remain analyst
  mappings, not author-validated labels for our cases.

### [Femmer et al., *Rapid Quality Assurance with Requirements Smells*](https://arxiv.org/abs/1611.08847)
- **Authors / Org:** Henning Femmer, Daniel Méndez Fernández, Stefan Wagner,
  and Sebastian Eder
- **Type:** academic primary study
- **Published:** 2016 preprint, 2017 journal article
- **Accessed:** 2026-09-26
- **Relevance:** high
- **What this contributed:** The paper distinguishes automatable linguistic
  indicators from completeness defects that require domain knowledge. Its
  catalog of language smells cannot establish that our deleted obligation is
  a naturally occurring, detectable smell. This motivates the separate
  source-grounded reference and explicit intervention label.

### [Veizaga, Shin, and Briand, *Automated Smell Detection and Recommendation in Natural Language Requirements*](https://arxiv.org/pdf/2305.07097)
- **Authors / Org:** Alvaro Veizaga, Seung Yeob Shin, and Lionel C. Briand
- **Type:** academic primary study
- **Published:** 2023 preprint
- **Accessed:** 2026-09-26
- **Relevance:** high
- **What this contributed:** Table 3 gives narrow meanings to `incomplete
  requirement`, `incomplete condition`, and `incomplete system response`.
  For Paska, an incomplete condition lacks actor or verb; an incomplete
  requirement lacks the system-response segment. Most C variants remove a
  whole obligation while retaining another response, so these exact Paska
  labels would be inaccurate. The study supplies a boundary for the mapping.

### [Gentili and Falessi, *Characterizing Requirements Smells*](https://arxiv.org/abs/2404.11106)
- **Authors / Org:** Emanuele Gentili and Davide Falessi
- **Type:** academic primary interview study
- **Published:** 2024 preprint
- **Accessed:** 2026-09-26
- **Relevance:** medium
- **What this contributed:** Ten industrial practitioners perceived smell
  severity, frequency, and effects differently across types. This supports
  keeping each obligation and project separate and avoiding a universal
  effect claim from the E2E pilots. It does not measure our intervention.

## Synthesis

The treatment is best named **controlled omission of a source-grounded
obligation**, linked to the broad **semantic incompleteness / partial-content**
family in Alemneh and Berhanu. A conditional rule can additionally be described
as a *missing condition*, and an omitted required action as a *missing response
clause*, but those are interpretations of the manipulated text. We do not
equate either phrase with Paska's stricter pattern definitions. The mapping
is construct alignment, not a finding that a smell detector would flag the C
text or that such text naturally occurs. Natural-smell detection, mapping
adjudication, and outcome effects are separate empirical questions.

## Downstream uses

- [Per-experiment mapping and outcomes](../thesis/e2e-smell-mapping-20260926.md)
- [E2E evidence matrix](../thesis/e2e-evidence-matrix-20260925.md)
