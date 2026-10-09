# Comparing the historical "vaguer" group with Orchid

Revised 2026-10-09 (English translation of the 2026-10-05 note, with the full-text reading added). The comparison discusses design differences; the results do not establish a direct contradiction.

In the five historical requirements classified as "vaguer", 20 A/H pairs showed worse behaviour. H keeps the whole of C and adds the old passage verbatim in another paragraph. This keeps the modern context controlled but changes the position of the passage and may repeat information. The subset was chosen after the A/C results were known, and repetitions of one requirement are not independent units. The exploratory result shows little degradation in this slice; it does not show that vagueness has no effect in general.

[Orchid / Clarity Is Not Assumed](https://arxiv.org/abs/2604.21505) (Yang et al., arXiv preprint v3, 2026-09-27; not peer-reviewed as read) studies function-level tasks with injected ambiguity: 1,312 curated variants (Orchid-HEval and Orchid-BCB) plus 3,904 uncurated variants (Orchid-BCB-Expand); the abstract cites 1,304 tasks, a discrepancy left unresolved here. Its criterion requires at least two plausible interpretations that lead to functionally different implementations. It reports a mean Pass@1 drop of 7.22 points (16.25% relative) from single-run tables, with no significance testing.

What the full-text reading adds (2026-10-09):

- Orchid has **no omission or incompleteness category**. Its "vagueness" type ("omits necessary details", e.g. an unspecified scope) is the closest match, and the limitations section leaves "incompleteness, or inconsistency" to future work. Orchid therefore neither supports nor contradicts H1a; it is adjacent evidence about injected ambiguity.
- DeepSeek-V3 generated and judged the ambiguous variants and is also an evaluated model; GPT-4 is both an evaluated model and the recognition judge. This is the generator/judge overlap this project already treats as a threat (matrix entry 2026-09-22).
- Treatment, context and unit of analysis differ from the historical reconstruction with scaffold used here: one injected ambiguity per function-level task versus a browser oracle over a multi-paragraph project documentation page.

Suggested wording for the defense and dissertation: "The five-case historical group showed little degradation. Orchid found degradation in its injected-ambiguity design, which does not include omission of a testable condition. The studies use different interventions, contexts and units; these elements must be compared before attributing the difference to the smell type."

The design and construction of H are in the [historical arm protocol](2026-10-04-historical-arm-protocol.md); counts are in the [results report](2026-10-05-historical-arm-results.md).

This note corrects the interpretation suggested for the two documents without changing results, labels or protocol. The 2026-10-05 reading covered only the definition and benchmark-construction sections of v2; the 2026-10-09 reading covers the injection and validation pipeline, evaluation setup, RQ1–RQ3 results and limitations of v3 (the last ~8.5k characters of the HTML were not read).
