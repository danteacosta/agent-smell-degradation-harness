# SRS-163: exploratory acceptance-criteria consensus

The separately authorized pilot completed **39/39 calls** through the ChatGPT
subscription: three calibration batches, nine generations and 27 isolated
judgments. No API key, fallback, regeneration or retry was used. This is one
public StrictDoc source intent, not nine independent requirements.

## Frozen design and operational result

The [protocol](../plans/2026-09-21-criteria-consensus.md) reused the nine exact
requests from the immutable offline packet. A is complete, B the proposed
meaning-preserving rewrite, and C removes only the links obligation. Generation
used requested model `gpt-5.6-luna`; the three judges were `gpt-6-astra`,
`gpt-5.6-sol` and `gpt-5.6-terra`. All used low reasoning and fresh contexts.
Judge payloads contained the complete reference, rubric and one artifact, with
no arm, paired response, generator identity or previous votes.

All three judges passed all eight authored calibration fixtures before any
generation. All nine generations and 27 judgments satisfied their output
contracts. No planned slot is missing or invalid. These are operational checks;
they do not establish semantic validity of every auxiliary annotation.

The endpoint is six-category coverage in `criteria`; statements in
`uncertainties` cannot satisfy a category. Primary consensus requires 3/3 votes.
Two-of-three majority is reported only as sensitivity. The source's per-command
versus collective scope is deliberately unresolved.

## Complete category results

Supported artifacts / three planned artifacts, with unanimous category votes:

| Category | Complete A | Rewrite B | Omitted links C |
| --- | --- | --- | --- |
| about command | 3/3 | 3/3 | 3/3 |
| version command | 3/3 | 3/3 | 3/3 |
| project title | 3/3 | 3/3 | 3/3 |
| current version | 3/3 | 3/3 | 3/3 |
| license | 3/3 | 3/3 | 3/3 |
| links | 3/3 | 3/3 | 0/3 |

All 54 artifact/category cells have unanimous labels: 51 supported and three
absent. None is unclear or unresolved. Majority sensitivity gives the same
category result. Links coverage is 100% for A and B and 0% for C; the descriptive
C−A difference is −100 percentage points in this single intent. The bounds for
unobserved/uncertain coverage collapse to these observed rates because no such
cells occurred; they are not population confidence intervals.

The generated C criteria omit links, while A and B explicitly require them.
The loss is relative to the full source obligation; C can still obey its shortened
prompt. This supports requirement-induced coverage loss in this bounded criteria
task. It is not a runtime/E2E defect result, a validated natural-smell taxonomy,
an independent-project estimate or confirmation of H1/H2.

## Auxiliary judgments expose remaining evaluator limitations

Category unanimity does **not** mean agreement or correctness in every field.
Scope annotations disagree for eight of nine artifacts. All artifacts explicitly
attribute their listed fields to both commands, but many judgments label scope
`collective_or_unspecified`; the panel does not resolve the source ambiguity.

Terra listed links as an unsupported addition in two omitted-condition artifacts
(`artifact-445ab653441b` and `artifact-812a9bec048e`). Links are absent from their
criteria and present in the full reference. These are observed auxiliary-field
errors, preserved exactly as returned. Two judges flagged “executes successfully”
in A repetition 1; the third did not. No auxiliary annotation was repaired or
used to replace the frozen category endpoint. Calibration checked the constructed
category vectors and citation contract; passing it did not validate every scope
or additions decision on generated artifacts.

## Custody, usage and limitations

Private packet: `criteria-consensus-20260921-v1`, 258 files plus final receipt.
Final receipt SHA-256:
`08e9e396bff2ae7bf5ea766c8f6de03f0f8295481fa262632b10be6bf820b65a`.
Frozen-input receipt:
`5ca61584a8a47c84fd05bf6dc6997e80aef5460e0c378d8923344961f5c99d32`.
Script SHA-256:
`52b2d86e6921787dd89f308b7edf874a1f4de1f0237997d0113c9492aee801ad`.
CLI `0.155.0-alpha.9.2`, binary SHA-256:
`9280c0754e8f1f6b72f495d30c8c82a006dbc4995bf0492916fa0901f6bfd1f9`.

Reported usage totals 550,566 input tokens, including 96,640 cached input tokens,
and 14,698 output tokens. Runtime context is included. API-equivalent USD cost
and immutable response-model snapshots are unavailable; cost is not asserted
to be zero. All models share a provider and potentially correlated errors.

The public source and license were byte-checked before dispatch against StrictDoc
revision `abf7be7daa2a25721a56980b5be15845336ea0b8`. No Drive document, private
corpus record or local path entered model prompts. The prior offline packet and
all older negative/failed studies remain unchanged. Human approvals remain zero;
labels are `llm_panel`, and `confirmatory_eligible` remains false. The
[consensus boundary](2026-09-21-llm-consensus-boundary.md) details these limits.

Software verification: 33 focused tests; 1,626 macOS-compatible tests and nine
subtests passed, with 12 skips and four OS resource-limit checks reserved for
Linux CI. The full local attempt reproduced those four known macOS preexec
failures. Wheel/sdist builds and compilation passed. Independent code review
found no remaining P1/P2 issue after correcting bounds for unanimous `unclear`.
