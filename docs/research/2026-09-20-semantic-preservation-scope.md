# Semantic preservation as thesis framing

## Question and decision

Should natural-language-to-formal-specification research become a new experiment
in this thesis? Retain it as theoretical framing and related work. The primary
acceptance-criteria task and pre-final T1–T3 versus T4 boundary remain unchanged.
No temporal-logic translation or model-checking benchmark is added.

## Sources that informed the decision

- Andreas Vogelsang et al., *On the Impact of Requirements Smells in Prompts:
  The Case of Automated Traceability*, ICSE-NIER 2025.
  [Author manuscript](https://arxiv.org/abs/2501.04810),
  [DOI](https://doi.org/10.1109/ICSE-NIER66352.2025.00016).
  Two LLMs were evaluated on trace-link tasks. A small significant effect for
  trace existence coexisted with no significant line-level effect. This motivates
  task-specific measurement, not a universal causal claim about smells.
- Baoluo Meng et al., *Transforming Natural Language Requirements to Formalism
  Using LLMs*, Systems Engineering 29(2), 195–204; online publication December
  2025, issue year 2026. [Publisher](https://doi.org/10.1002/sys.70023).
  The publisher abstract describes interactive translation to logical formalism
  and an industrial landing-gear evaluation. This is a related translation task;
  the abstract does not establish correctness guarantees for our agents or
  performance on our task. No full-text-specific method or effect is inferred.
- Guilherme Paiva, Edna Dias Canedo and Geraldo Pereira Rocha Filho,
  *From issue titles to requirements: an empirical study of large language
  models and prompt engineering strategies*, Requirements Engineering, 2026.
  [Publisher](https://doi.org/10.1007/s00766-026-00462-z).
  Requirement generation is assessed along unambiguity, verifiability and
  singularity. These dimensions motivate distinguishing quality properties;
  they do not supply independent labels for our requirement/code pairs.

The primary-source pages were checked during the preceding discussion of this
proposal. These are conceptual inputs, not new experimental observations.

## Operational interpretation

Preservation concerns a reviewed reference condition and observable behavior,
not word overlap or the presence of a phrase in a plan. In the original discount
pilot, `min(total * 0.1, 7)` and `total * 0.1` disagree at input 100. This is a
counterexample for that condition. It is not proof of full-program equivalence,
independent smell classification, prevalence, or a general degradation effect.

A vague word such as “quickly” lacks an operational threshold; this alone is not
computational undecidability. Choosing two seconds adds a domain decision. A
bounded temporal operator also requires an explicit time model and logic.
Neither is introduced into the current measurement contract.

T1 contains interpretation evidence, T2 plans, T3 execution checkpoints, and T4
terminal artifacts and evaluation. Intermediate mention is a potential signal,
not a semantic verdict. H2 asks whether those pre-final signals add predictive
value on held-out projects; they must never consume the terminal oracle.

## Downstream use

Add a bounded framing subsection to the thesis proposal. Use the executable
counterexample to explain why condition preservation matters. Keep the
[thesis/product boundary](../thesis-product-boundary.md), candidate-admission
review and independent outcome evaluation as the controlling protocol.
