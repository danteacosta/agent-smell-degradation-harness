# Preliminary source: incomplete requirements and LLM ensembles

Status: outside the canonical [literature matrix](literature-matrix.md) pending
full-paper review. Original abstract read: 2026-10-15. Venue source rechecked:
2026-10-17. This note does not change H1, H2, labels or the experimental protocol.


Search/read date: 2026-10-15. Deduplicated by title and arXiv ID against this matrix:
TraceDev (2607.18886), WiseSpec (2609.00568), UnderSpecBench (2607.02294), ClarEval
(2603.00187), "Ask or Assume?" (2603.26233) and Orchid (2604.21505) were re-surfaced by
the search and are already entered; no update to them. The item below was not previously recorded in the
matrix. Read: the ASE 2025 NIER program page (abstract, method summary, data, headline
results). The paper itself, its DOI and any limitations section were not accessible, so
this is a preliminary abstract-only note and supports context only.

| Source / status | Question, sample and method | Findings / limitations | Thesis, experiment, product and action | Credibility |
| --- | --- | --- | --- | ---: |
| Kassab and AbdElhameed, [*Detecting and Repairing Incomplete Software Requirements with Multi-LLM Ensembles*](https://conf.researchr.org/details/ase-2025/ase-2025-nier-track/13/Detecting-and-Repairing-Incomplete-Software-Requirements-with-Multi-LLM-Ensembles), ASE 2025 NIER track (short paper; peer-review status of NIER acceptance stated by the venue, paper text not read; no DOI found) | Can an ensemble of three LLMs (DeepSeek Chat, GPT-4o Mini, Claude Sonnet 4) detect missing requirements in an SRS and propose fixes? Builds a structured domain model from the SRS, runs external and internal completeness analyses, aggregates by majority vote, weighted vote or meta-LLM fusion. Four SRSs with seeded omissions. | Reported single-model recall 0–52%; full ensemble consistently above 75%, up to 100%; suggestion plausibility 95–100%. Limits visible from the abstract: four documents, seeded omissions of unknown construction, self-built tool, "early" results, no stated threats; recall of a single model varies widely, and plausibility is not correctness. | **Thesis:** upstream-completeness precedent (find the omitted requirement in the document). It does not measure whether an omission becomes a downstream artifact defect, so it does not narrow the H1 gap; it does reinforce the already recorded point that single-LLM reviewers miss deletions. **Experiment:** weak extra support for qualifying the A/B/C review panel against authored deletion controls and reporting per-model recall, not only the ensemble result; no change to the frozen rubric. **Product:** spec-level completeness checkers are an adjacent category to position against. **Action:** context only; no hypothesis, label, protocol or code change. | 3 |

**Decision needed from Dante (not applied):** none required; if the panel-qualification
section is revisited, consider citing this as a secondary pointer after reading the full
paper.

## Source verification

Primary source: the linked ASE 2025 NIER program abstract, by Mohamad Kassab and
Marwan AbdElhameed. Type: conference program abstract; relevance: medium. It
confirms the named models, four seeded-omission SRSs and the reported numerical
ranges. Plausibility remains distinct from correctness. The full paper and its
threats to validity remain unreviewed, so this source is not admitted to the
canonical matrix.

The [official NIER track policy](https://conf.researchr.org/track/ase-2025/ase-2025-nier-track)
(accessed 2026-10-17) states the evaluation criteria and double-blind review
process. This supports venue status, not independent validation of the reported
results.
