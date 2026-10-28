# Can the omitted obligation be retrieved from the project's documentation?

Date: 2026-10-28. Status: exploratory, offline, no model call. Script:
`scripts/obligation_retrieval.py`; sources: `data/obligation-retrieval/sources.json`;
results: `data/obligation-retrieval/v1/results.json`; tests:
`tests/test_obligation_retrieval.py`.

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

24 of 25 requirements have a gold passage (for openproject-more-menu-subproject the
source file at the snapshot does not contain the omitted words).

| k | 1 | 3 | 5 | 10 | 20 |
|---|---:|---:|---:|---:|---:|
| recall@k, query = incomplete request | 0.58 | 0.75 | 0.75 | 0.83 | 0.92 |
| recall@k, query = its first sentence only | 0.13 | 0.29 | 0.33 | 0.33 | 0.50 |
| recall@k, first sentence + visible text of the page scaffold | 0.13 | 0.25 | 0.29 | 0.42 | 0.54 |

Split by the F3 groups of the coupling analysis: in the 13 requirements with a gold
passage where no generator kept the rule, the gold passage is in the top 5 for all 13;
in the 11 where some generator kept it, for 5 of 11 (0.45).

The first-sentence query ("Implement the Restart button of the tutorial popup.") is a
ticket-title-like lower bound: it drops the documentation sentences that the full request
shares with the gold passage. Adding the visible text of the page scaffold the tester also
receives (labels, buttons) does not help lexical retrieval much.

## Reading

The rules that agents never recovered and testers almost never detected are, in this
sample, the easiest to retrieve from the documentation with the request as query. This
makes documentation-grounded review a concrete candidate remedy for the double blind
spot: retrieve the top passages for the ticket and give them to the test writer. It is
also a candidate product feature. The gap between the two query rows (0.75 against 0.33
at k = 5) is the technical problem: retrieval from a short, ticket-like request needs more
than lexical matching (query expansion, dense retrieval or an agent that searches), and
that is where a method contribution could sit.

## Limits

- The full requests were built from the same documentation paragraphs, so that query
  shares vocabulary with the gold passage by construction (upper bound); the
  first-sentence query is closer to a ticket title (lower bound). Real tickets lie
  somewhere between; a test with real issue text is needed.
- The gold criterion is lexical; a passage can contain the words without stating the
  rule, and paraphrased documentation can be missed.
- Retrieval is necessary but not sufficient: whether testers given the retrieved passages
  write suites that detect the loss is a model-based experiment (a candidate fourth
  source, `spec_retrieved`, for the confirmatory tester extension).
- Snapshots differ per project; Paperless uses the commit that introduced each rule.
