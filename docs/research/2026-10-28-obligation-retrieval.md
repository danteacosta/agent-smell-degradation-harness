# Can the omitted obligation be retrieved from the project's documentation?

Date: 2026-10-28. Status: exploratory, offline, no model call. Script:
`scripts/obligation_retrieval.py`; sources: `data/obligation-retrieval/sources.json`;
semantic gold: `data/obligation-retrieval/semantic-gold.json`; results:
`data/obligation-retrieval/v1/results.json`; tests: `tests/test_obligation_retrieval.py`.

**Revision after review by Codex (28/10).** The first version used a lexical gold (a
passage of the source file containing half of the omitted span's content words). Codex
pointed out that it was never validated semantically and that numeric omissions reduce
to one or two tokens (`10`, `2`). Reading the best lexical gold passage per requirement
confirmed the problem: 3 of 24 did not state the rule (a navigation table, a device
list, a list of channel permissions) and 3 stated it only partly. The primary result is
now the **semantic gold** below; the lexical numbers are kept for comparison only. The
cache is also verified against the pinned snapshot (sha, origin, sparse paths, clean
tree) before `fetch` reuses it and before `run` reads it, failing closed otherwise.

## Question

QP4 shows that tests written from the incomplete request miss the loss and that pooling
testers does not compensate. The practical follow-up is whether the missing obligation
could be put back in front of the tester automatically, from documentation the project
already has. This study measures only the retrieval step.

## Method

For each of the 25 QP4 requirements, the documentation of its project was fetched at the
snapshot recorded for arm A (sparse, shallow git fetch of the documentation folder),
split into paragraph passages, and indexed with BM25 (k1 1.5, b 0.75). The query is the
arm-C text. A gold passage is a passage of the requirement's source documentation file
that contains at least half of the content words of the omitted span (the words of A
that the edit to C removed). A loose variant accepts gold passages from any file and is
reported per row.

## Results

**Semantic gold (primary).** For each requirement, a quote of the sentence in the
snapshot that states the omitted obligation was located by reading arm A and searching
the documentation (coded by Claude, not blind, not a human coder; see the JSON). A
passage is gold when its normalised text contains the quote, in any file. All 25
requirements have one; for zulip-unsubscribe-self it is in a different file
(`unsubscribe-from-a-channel.mdx`) from the recorded source file.

| recall@k, semantic gold, 25 requirements | 1 | 3 | 5 | 10 | 20 |
|---|---:|---:|---:|---:|---:|
| query = incomplete request | 0.40 | 0.68 | 0.68 | 0.76 | 0.92 |
| query = its first sentence only | 0.00 | 0.16 | 0.16 | 0.24 | 0.36 |
| first sentence + visible text of the page scaffold | 0.04 | 0.16 | 0.16 | 0.32 | 0.40 |

Split by the recovery groups of the coupling analysis (a post hoc grouping, see the
coupling report): top 5 for 12 of 14 requirements where no generator kept the rule, and
for 5 of 11 where some generator kept it.

**Lexical gold (v1, superseded).** 24 of 25 requirements had a lexical gold passage;
recall@5 was 0.75 (incomplete request), 0.33 (first sentence) and 0.29 (first sentence +
page text); 13 of 13 in the zero-recovery group. These figures over-credit retrieval in
the cases where the matching passage did not state the rule.

The first-sentence query ("Implement the Restart button of the tutorial popup.") is a
shorter, ticket-title-like proxy: it drops the documentation sentences that the full request
shares with the gold passage. Adding the visible text of the page scaffold the tester also
receives (labels, buttons) does not help lexical retrieval much.

## Reading

In this sample, the rules that no generator recovered are retrieved in the top 5 more
often (12 of 14) than the others (5 of 11) when the full request is the query; this is a
descriptive contrast on a post hoc grouping, and the query shares wording with the
documentation by construction. This
makes documentation-grounded review a concrete candidate remedy for the double blind
spot: retrieve the top passages for the ticket and give them to the test writer. It is
also a candidate product feature. The gap between the two query rows (0.68 against 0.16
at k = 5, semantic gold) is the technical problem: retrieval from a short, ticket-like request needs more
than lexical matching (query expansion, dense retrieval or an agent that searches).
Grounding generated tests in documentation has strong antecedents (Doc2OracLL;
TestSuiteBench's documentation ablation; Haeri and Ghelichi), so any contribution here is
specific: whether grounding recovers detection of an obligation that was removed from
the request that also drove the implementation, measured against frozen oracles; no
broad novelty is claimed for documentation grounding or retrieval as such.

## Limits

- The full requests were built from the same documentation paragraphs, so that query
  shares vocabulary with the gold passage by construction: an optimistic selection, not
  a mathematical upper bound on retrieval from natural tickets (a real ticket can name
  the rule's domain words more directly than the derived request). The first-sentence
  query is a shorter, more pessimistic proxy closer to a ticket title, likewise not a
  lower bound. Neither row says where real tickets fall; a test with real issue text is
  needed. (Wording corrected after review by Codex, 28/10.)
- The semantic gold was coded by one agent that knew the requirements and their
  outcomes; it needs a blind check (it is short enough to add to a human audit). A quote
  match also does not show that a tester given the passage would read it as binding.
- Retrieval is necessary but not sufficient: whether testers given the retrieved passages
  write suites that detect the loss is a model-based experiment (a candidate fourth
  source, `spec_retrieved`, for the confirmatory tester extension).
- Snapshots differ per project; Paperless uses the commit that introduced each rule.
