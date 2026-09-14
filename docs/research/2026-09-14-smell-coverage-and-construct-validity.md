# Smell coverage and construct validity

Reviewed: 2026-09-14. Assistant literature review; not independent human
annotation, a systematic mapping update, or a completed ten-smell experiment.

## Question and current coverage

Do the three completed original-policy pairs establish coverage of distinct
literature smells? No. They exercise one local intervention, removal of an
explicit policy sentence, in three intents. The discount artifact violates the
removed cap; the access and token artifacts retain the required behavior.
No detector was evaluated in this collection.

A later, separately frozen [24-episode language-control pilot](codex-language-controls-results-20260914.md)
adds original coordination and pronoun probes plus two meaning-preserving
controls. All 12 explicit-policy artifacts passed. Coordination rewrites chose
one grouping in all four outputs (two intended, two alternative by twin label);
pronoun rewrites required both actors in all four outputs (neither frozen
antecedent policy). All eight control artifacts passed. These are four clusters with dependent twin cases,
not six independently sampled projects, and remain assistant-reviewed
candidates rather than human-admitted instances of the literature categories.

## Primary evidence and correction

[Femmer, Méndez Fernández, Wagner and Eder, *Rapid Quality Assurance with
Requirements Smells*](https://arxiv.org/html/1611.08847v1), §3.1–3.2 and Table 3,
distinguish a locatable, detectable symptom from a demonstrated defect. Their
listed language categories inform rows F1–F9 below. References that cannot be
resolved are discussed, but excluded from their implemented study. Detection
does not guarantee downstream failure.

[Veizaga, Shin and Briand, *Automated Smell Detection and Recommendation in
Natural Language Requirements*](https://arxiv.org/html/2305.07097v2), Table III,
defines coordination ambiguity and syntactically incomplete segments in the
Rimay/Paska context. A condition lacking an actor or verb is not the same
operation as deleting an entire rule. Likewise, a missing response segment and
a response missing grammatical components have distinct definitions.

The older local catalog combined these terms as aliases too freely. Its
operational families are engineering groupings, not equivalent literature
categories. A removed cap is currently a **controlled omission relative to a
known complete policy**. Do not relabel it as a validated Paska smell. The
shortened discount text alone does not reveal that the intended cap was 7.

## Ten catalog entries and their next evaluation route

These are catalog entries, not ten independent or mutually exclusive dimensions.
All proposed operations and tests below are our design suggestions, not
experiments performed by the cited papers. None of these ten rows has been
isolated and evaluated by the 18-episode Codex demonstration.

| ID / category | Source | Proposed operation or control | Acceptance and confound check | Current status |
|---|---|---|---|---|
| F1 Linguagem subjetiva | Femmer §3.2 | Replace a measurable usability target with an evaluative adjective. | Needs a usability task and observable user outcome; pure Python cannot establish usability. | Catalog only; no executable case admitted. |
| F2 Advérbio/adjetivo ambíguo | Femmer §3.2 | Replace an explicit threshold with a vague qualifier. | Record the deleted policy as intended context; do not call deviation disobedience to an unspecified threshold. | Candidate route; requires semantic review. |
| F3 Brecha ou ressalva vaga | Femmer §3.2 | Add a vague exception to an otherwise mandatory guard. | Verify that only obligation strength changes; retain required and exception-domain tests. | Candidate route; requires semantic review. |
| F4 Termo aberto ou não verificável | Femmer §3.2 | Make a previously enumerated output set open-ended. | Separate membership already specified from newly unspecified membership; record overlap with F2. | Candidate route; requires semantic review. |
| F5 Superlativo | Femmer §3.2 | Replace a bounded optimization objective with an unbounded superlative. | Freeze feasible choices and ties; otherwise no unique correctness oracle exists. | Catalog only until an objective is justified. |
| F6 Comparativo | Femmer §3.2 | Remove the reference value from a comparison. | Record the missing comparator as unavailable; measure ambiguity/clarification rather than invent its value. | Catalog only until interpretation is adjudicated. |
| F7 Enunciado negativo | Femmer §3.2 | Express the same finite-domain rule affirmatively and negatively. | Preserve truth table and all behavior. Useful control: negative wording is not an injected defect by itself. | Two complementary-response controls executed; 8/8 artifacts passed. Not validated F7 positives. |
| F8 Pronome vago | Femmer §3.2 | Replace one of two named actors with a pronoun. | Enumerate possible antecedents and record interface clues; a cue-removal ablation requires a separate manifest. | Original twin probe executed; 4/4 rewrites required both actors. Named argument cues retained; human category validation pending. |
| F9 Referência incompleta | Femmer §3.2/Table 3 | Remove the locator of a referenced policy while preserving surrounding text. | Freeze available context; distinguish unresolved reference from an invented rule and from retrieval failure. | Catalog only; reference-enabled task required. |
| P1 Ambiguidade de coordenação | Paska Table III | Remove grouping from a conjunction/disjunction rule. | Freeze intended grouping and complete Boolean truth table; retain alternative interpretations in reporting. | Original twin probe executed; all four rewrites chose a or (b and c). Human category validation pending. |

The existing access pair still says Boolean authorization and allow/deny in its
interface. The token pair still names a Boolean argument `used`. These are
retained context cues, so a null contrast does not show that the model recovered
an entirely unobservable rule. Preserve them in the completed run; a separate
future interface-cue ablation must have its own frozen manifest and denominator.

## Admission contract for a broader study

Before new generation, record the source definition, exact span and operation,
known full intent, admissible domain, target tests, preserved-behavior tests,
alternative interpretations, scaffold cues, rights and annotation decision.
Reject cases whose oracle strengthens a source claim or selects an unsupported
interpretation. Have reviewers assess cases before seeing output; assistant
agreement does not replace the human annotation gate. Preserve multiple labels
when categories overlap rather than forcing ten artificially distinct groups.

Use semantics-preserving rewrites as controls and keep whole-rule omission as a
separate intervention. Freeze the sampling unit at intent/project and never
inflate it with repetitions or extra test inputs. Two Codex model configurations
are not two providers. A model comparison must remain separate from smell
coverage and from the T1–T3 observability and H1/H2 evaluation.

## Downstream use

This correction informs the [saved-artifact audit design](../superpowers/specs/2026-09-14-paired-evidence-followup-design.md),
the [original result](codex-original-demo-results-20260914.md), and the thesis
Drive report/slides. It supersedes equivalence claims in the older normalized
smell map; it does not change frozen source bytes or historical outcomes.
