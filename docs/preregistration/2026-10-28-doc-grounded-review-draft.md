# Design draft: documentation-grounded review tests (candidate RQ5)

Status: **draft for Dante, Márcio and Codex; not frozen; no calls authorised.** τ² is out
of scope. Any execution needs explicit authorisation of budget and models.

## Motivation

On the frozen QP4 data, tests written from the incomplete request detect 0.18 of
confirmed losses per tester and 0.50 with five testers pooled, against 0.82 for one tester
with the complete requirement (`docs/research/2026-10-28-verifier-coupling.md`). The
omitted obligation is usually present in the project's documentation: with the request
as BM25 query, the source passage is in the top 5 for 18 of 24 requirements, and for all
13 in which no generator kept the rule; with only the request's first sentence, for 8 of
24 (`docs/research/2026-10-28-obligation-retrieval.md`). The question is whether giving
the test writer access to the documentation, rather than the complete requirement,
recovers detection, and which way of giving it works when the ticket is short.

## Reuse of frozen material (exploratory pilot)

The pilot reuses the 25 QP4 requirements, their frozen pages, the frozen implementations
with their oracle roles (correct, mutant, recovered) and the existing evaluation runner.
Only new suites are generated. Because the requirements and outcomes are already known,
the pilot is exploratory; a confirmatory version runs on the new requirements of the
tester extension (`2026-10-28-qp4-tester-extension-draft.md`).

## Sources compared

| Source | What the tester receives |
|---|---|
| `spec_incomplete` (existing) | incomplete request + scaffold |
| `docs_bm25_full` | incomplete request + scaffold + top 5 BM25 passages, full request as query |
| `docs_bm25_title` | incomplete request + scaffold + top 5 BM25 passages, first sentence as query |
| `docs_agentic` | incomplete request + scaffold + read-only tools to list, search and open the documentation snapshot, with a call budget fixed in advance |
| `spec_complete` (existing) | complete requirement + scaffold |

Documentation snapshots are those in `data/obligation-retrieval/sources.json`. For
`docs_agentic`, the tool log is kept so that retrieval (did the tester open a gold
passage?) can be separated from use (did the suite then check the rule?).

Leakage control: the documentation is the project's own text at the snapshot, which is
what a reviewer could consult. The arm-A requirement text itself is never given in the
documentation sources. Oracle code, references and outcomes are never visible.

## Outcomes

As in `scripts/mutation_adequacy.py`: per-requirement mutation score with unsound suites
as zero; detection by at least one sound suite; alarm rate on correct and recovered
implementations (false alarms); for `docs_agentic`, whether a gold passage was opened.

## Planned comparisons (exploratory)

1. `docs_bm25_full` and `docs_agentic` against `spec_incomplete` (does documentation access
   recover detection?).
2. `docs_agentic` against `spec_complete` (how much of the gap is closed).
3. `docs_bm25_title` against `docs_agentic` (does searching beat lexical top-k from a
   short ticket?).
4. False alarms of every documentation source against `spec_complete` (does extra text add
   noise?).

Equal weight per requirement; project bootstrap intervals and exact project sign-flip
tests, reported descriptively.

## Budget sketch

Two suites per tester, source and requirement: 25 × 2 = 50 suites per source and tester.
Three new sources with two testers (one per provider) is 300 tester calls plus the
browser evaluations of each suite against every implementation of its requirement, as in
the existing runs. Exact counts and cost to be computed from the frozen manifests before
asking for authorisation.

## Why it matters

If documentation access recovers most of the detection, the thesis gains a constructive
result next to the diagnosis, and the product hypothesis (auditing and grounding
verifiers against written obligations) gains a measured mechanism. If it does not, the
failure modes (passage not found, found but not used, used but test too weak) are
themselves informative and separable through the tool log.
