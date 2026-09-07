# Locating evidence is separate from validating support

Question: after the v3 quote failures, can a mechanically resolvable citation
improve the diagnostic instrument without overstating semantic validity?

Reading date: 2026-09-07. The sources below informed the
[offline artifact-addressing design](../superpowers/specs/2026-09-07-evidence-addressing-design.md).
The motivating observations remain in the [v3 results](scoped-judge-results.md).

## Sources and contribution

### Gao et al., ALCE

Tianyu Gao, Howard Yen, Jiatong Yu, and Danqi Chen. *Enabling Large Language
Models to Generate Text with Citations*. EMNLP 2023, pp. 6465-6488.
[Paper and metadata](https://aclanthology.org/2023.emnlp-main.398/).
DOI: 10.18653/v1/2023.emnlp-main.398.

ALCE separates answer correctness from citation support and relevance. Its
citation metrics use an entailment model and are compared with human judgments.
The authors identify limits in partial-support detection and coverage of harder
tasks. Read: abstract, Section 3.3, results in Sections 5-6, and limitations.
Credibility: 8/10, based on the peer-reviewed method and explicit evaluation;
requirements coverage is outside its tested tasks.

Design inference: resolving a source ID cannot substitute for a support
judgment. We do not import ALCE's scores or its NLI model, nor claim that its
validation transfers to this rubric.

### Rashkin et al., AIS

Hannah Rashkin et al. *Measuring Attribution in Natural Language Generation
Models*. Computational Linguistics 49(4), 2023, pp. 777-840.
[Paper and metadata](https://aclanthology.org/2023.cl-4.2/).
DOI: 10.1162/coli_a_00486.

AIS distinguishes interpretation from attribution to identified sources. Its
two-stage human annotation studies cover conversational QA, summarization, and
table-to-text output. Fine-grained annotation adds effort; ambiguous language
and imperfect references remain limitations. Read: abstract, Sections 3.2-3.3,
4.1, 5.5.5, 5.7, and the discussion. Credibility: 9/10 for the peer-reviewed
framework, human evaluation, and explicit limitations; requirements are not a
validated target domain.

Design inference: preserve ambiguity and separate source location from semantic
assessment. This paper does not justify replacing independent annotators with
model consensus.

### W3C Web Annotation Data Model

W3C Recommendation, 23 February 2017, Sections 4.2.5-4.3.
[Position selectors and states](https://www.w3.org/TR/annotation-model/#selectors).

The standard distinguishes character-position and byte-position selectors and
warns that edits can invalidate positions. Its state model identifies the
representation being annotated. Authority: a normative interoperability
specification, not empirical evidence of evaluator quality.

Engineering inference: bind UTF-8 byte ranges to a content digest and a versioned
segmentation policy. Preserve original bytes rather than silently normalizing
them. The proposed local contract is not W3C-conformant JSON-LD.

## Decision and limits

An artifact-only namespace can reject a reference-only citation mechanically.
It cannot detect every irrelevant citation: an actual paragraph may share words
with an obligation without supporting it. A regression must demonstrate this
limitation explicitly, so a passing parser cannot become an approval signal.

The next increment is offline software validation. It does not spend money,
rescore the failed studies, inspect locked evaluation cases, or change H1/H2.
Future provider comparisons must freeze both the representation change and the
semantic rubric. A presentation change is an intervention, not a neutral
formatting detail whose effect can be ignored.

For a product, exact evidence resolution supports trace inspection and replay.
Useful diagnoses and appropriate user reliance remain separate evaluation
targets. Neither a citation hash nor a deterministic policy decision certifies
that a natural-language condition was preserved.
