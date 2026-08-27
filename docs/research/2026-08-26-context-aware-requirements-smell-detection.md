# Context-aware requirements-smell detection

Date: 2026-08-26
Status: literature synthesis and implementation input; not confirmatory evidence

## Research question

How does the literature operationalize requirements smells, and what should
replace a detector that only searches for a fixed list of words in the
requirement text?

## Short answer

The literature does not support treating keyword presence as a semantic
verdict. A lexical scan is useful as a transparent lower-bound or triage
baseline, but the strongest practical approaches combine several layers:

1. linguistic preprocessing and normalization (tokenization, lemmatization,
   part-of-speech or dependency cues);
2. phrase- and structure-level patterns, sometimes expressed in a controlled
   natural language for requirements;
3. learned representations or classifiers for domain-sensitive variation;
4. an explanation/recommendation step that identifies the problematic span and
   how to make the requirement testable; and
5. independent human and behavioral validation, because a smell indicator is
   not the same thing as a defect in every domain or context.

This is exactly what the v8 screening exposes: the frozen lexical comparator
misses source-marked cases whose indicators are synonyms, morphology, scope,
condition structure, or domain-specific ambiguity. Expanding a dictionary is
therefore a useful next comparator, not the final contribution.

## What the relevant studies do

| Source | Detection or evaluation strategy | Implication for this project |
| --- | --- | --- |
| [Femmer et al., *Rapid Quality Assurance with Requirements Smells*](https://arxiv.org/abs/1611.08847) | Smella performs lightweight static analysis and reports average precision of 59% and recall of 82%, with high variation across cases; the authors position it as a supplement to reviews. | Retain a transparent lexical/pattern baseline, but report false alerts and variation by smell instead of presenting it as understanding. |
| [Habib, Wagner and Graziotin, *Detecting Requirements Smells With Deep Learning*](https://arxiv.org/abs/2108.03087) | Moves from classical NLP toward manually labeled data, word embeddings, transfer learning and deep/ensemble models; it explicitly reports class imbalance and overfitting/generalization concerns. | Use project-held-out splits, expert labels, class-aware metrics and a simple baseline before evaluating contextual models. |
| [Fischbach et al., *How Do Practitioners Interpret Conditionals in Requirements?*](https://arxiv.org/abs/2109.02063) | Surveyed 104 requirements-engineering practitioners interpreting 12 conditional clauses and mapped answers to propositional/temporal logic. Practitioners disagreed about whether conditions were necessary or merely sufficient. | Detect and represent antecedent, consequent, negation and temporal relation; generate tests for both branches rather than searching for `if` alone. |
| [Veizaga, Shin and Briand, *Automated Smell Detection and Recommendation in Natural Language Requirements*](https://arxiv.org/abs/2305.07097) | Paska combines NLP with Rimay controlled-natural-language patterns and produces recommendations. Its industrial case covered 2,725 annotated requirements from 13 financial systems. | Make the detector actionable: evidence span, violated pattern, clarification question and revised requirement, not only a boolean flag. |
| [Zakeri-Nasrabadi and Parsa, *Natural Language Requirements Testability Measurement Based on Requirement Smells*](https://arxiv.org/abs/2403.17479) | Uses nine smell families, a neural word-embedding method to build a dictionary, and nearly 1,000 requirements from six projects; it reports gains over Smella and links smells to testability. | A learned vocabulary can improve coverage, but it must be trained/calibrated without touching held-out projects and evaluated against independent labels. |
| [Gentili and Falessi, *Characterizing Requirements Smells*](https://arxiv.org/abs/2404.11106) | Interviews ten experienced practitioners in a safety-critical company about frequency, severity and effects of 12 smells. Ambiguity and verifiability were among the most severe, while ambiguity and complexity were among the most frequent. | Do not collapse all families into one score. Effects, usefulness and acceptable language depend on smell type, role and domain. |
| [Vogelsang et al., *On the Impact of Requirements Smells in Prompts*](https://arxiv.org/abs/2501.04810) | Uses two LLMs for automated traceability and finds mixed, task-dependent effects: a small significant effect for deciding whether a requirement is implemented, but not for tracing exact code lines. | Measure the downstream task directly. For this project that means hidden behavioral tests, generated tests and code, not detector accuracy alone. |
| [Wolf, Trendowicz and Siebert, *Quality assessment of software requirements using artificial intelligence methods: A systematic literature review*](https://doi.org/10.1016/j.infsof.2025.107979) | Reviews 26 peer-reviewed studies from 2019--2025. It finds a shift toward contextual embeddings and LLMs, but heavy use of public/synthetic data, inconsistent metrics, few actionable improvements and rare semantic or expert evaluation. | The contribution needs reproducible artifacts, standardized metrics, difficult clean cases, expert annotation and a real improvement condition. A high F1 on source markers is insufficient. |

## How keyword search fails in the current round

The v8 lexical comparator was intentionally frozen as a simple lower bound. On
the project-held-out test split, its recall was 0.0 for three families and
0.375--0.714 for the other families. The per-case audit shows why, without
publishing private ARTA requirement text:

- subjective-language markers include morphology and domain/contextual uses
  such as adverbs, evaluative nouns and words whose subjectivity depends on
  the surrounding clause;
- ambiguous-adjective/adverb markers include scope and quantifier patterns
  (`at least`, `minimum`, `maximum`, `each`, `correctly`), not only adverbs such
  as `quickly`;
- non-verifiable markers include underspecified operations and objects
  (`several`, `too large`, `detail`, `limit`, `defined`), where verifiability
  depends on a missing criterion or response;
- vague-pronoun markers include anaphora and referring expressions such as
  `another` and `which`, requiring a local antecedent/role analysis;
- uncertain-verb markers include modal and auxiliary variation (`can`, `will`)
  whose interpretation depends on whether the clause states permission,
  capability, prediction or obligation; and
- polysemy markers include broad nouns and verbs (`action`, `information`,
  `log`, `support`, `store`) whose ambiguity is domain-sensitive.

These are not all confirmed semantic errors: ARTA marker values are source
annotations, not independent expert labels. The audit therefore records
automatic disagreement categories and leaves semantic adjudication pending.

## Proposed detector architecture

The implementation now has three explicitly separated levels:

```text
lexical lower bound
    -> contextual linguistic triage
        -> provider-backed semantic adjudication
            -> clarification/rewrite + generated tests/code
                -> hidden behavioral oracle
```

### Level 1: transparent lower bound

Keep the existing `natural-lexicon/v1` comparator. It gives an easy-to-audit
answer to “what happens if we search for a small fixed list?” and makes the
failure mode visible. It must remain a baseline, not the proposed detector.

### Level 2: contextual linguistic triage

The new `contextual-linguistic/v1` comparator adds:

- broader phrase and morphological cues;
- measurable quantities, units and comparison operators;
- conditions and temporal cues;
- actors, normative modals and explicit system responses;
- an approximate local-antecedent check for vague pronouns; and
- family-specific scoring and evidence terms.

It emits a score, evidence terms and structural features. It does not read
labels or oracle outcomes. Because it is still heuristic, its results are
diagnostic and source-label agreement is not confirmatory evidence.

The v8 implementation is explicitly retrospective: its cue inventory was
assembled while investigating this round's lexical misses. Consequently, the
v8 contextual numbers are useful for exposing failure modes and exercising the
artifact contract, but they are not a fair predictive comparison. A
confirmatory run must freeze the inventory (or model and prompt) using only
training/calibration projects before opening the project-held-out test set.

### Level 3: semantic adjudication and intervention

After credentials and approved data handling are available, evaluate at least
two real model/provider configurations. The provider response should be
schema-constrained and include:

```json
{
  "decision": "clean | smelly | uncertain",
  "family": "...",
  "evidence_span": "...",
  "explanation": "...",
  "missing_or_ambiguous_condition": "...",
  "clarification_question": "...",
  "revised_requirement": "...",
  "testable_prediction": "..."
}
```

The system should abstain when context is insufficient. The generated code
track then tests whether the clarification/revision actually preserves the
intended condition. The central comparison is:

```text
agent without verifier
vs. agent with contextual alert
vs. agent with alert + review/revision opportunity
```

Primary downstream outcomes are hidden-test pass rate, defects introduced,
false alerts, post-alert correction rate, clarification count, time, tokens,
cost and provider error rate.

## Error-audit protocol

The bundle's `error-analysis.json` is an automatic, redacted triage of the
held-out cases. It contains IDs, requirement hashes, outcomes, matched
evidence and structural features, but not private requirement text or marker
values. Every FP and FN is marked `pending` for expert review. The eventual
manual category should be one of:

- synonym/morphology or uncovered linguistic form;
- structural/context-dependent smell;
- legitimate term or acceptable domain usage;
- domain knowledge required;
- source-marker disagreement or insufficient context; or
- parser/data-quality issue.

The manual category must be assigned independently by two annotators, with an
adjudication record. It must not be inferred from whether the lexical or
contextual comparator fired.

## Consequence for the proposal

The proposal should state that the research gap is not “invent a larger list
of bad words.” It is to evaluate whether context-aware, explainable
requirements analysis can improve an agent's downstream artifacts. Keyword and
pattern detectors are baselines and candidate generators; the scientific
claim concerns semantic review plus behavioral validation under project-held-
out evaluation. Any contextual comparator developed after inspecting test
failures must be labeled exploratory and excluded from superiority claims until
it is frozen and re-evaluated.

## Downstream artifacts

- Implementation: [`baselines/contextual_smell.py`](../../baselines/contextual_smell.py)
- Redacted error audit: [`error-analysis.json`](../../artifacts/experiments/runs/discovery-20260826-v8-screening/error-analysis.json)
- Contextual metrics: [`contextual-results.json`](../../artifacts/experiments/runs/discovery-20260826-v8-screening/contextual-results.json)
- Companion experiment report: [`report.md`](../../artifacts/experiments/runs/discovery-20260826-v8-screening/report.md)
- Proposal/experiment separation: [`2026-08-25 requirements-smell discovery catalog`](2026-08-25-requirements-smell-discovery-catalog.md)
