# Audit citations against the artifact a judge received

The experimental `scope-addressed/v4-dev` interface replaces copied quotations
with IDs of exact artifact segments. It can reject an invented or stale
citation. It cannot establish that a real cited segment supports the obligation.
Provider performance has not been measured for this version.

This is an offline label-plane tool. It does not change the frozen v3 study,
release its 96 evaluation calls, launch the main pilot, or make a provider call.
See the [design](../superpowers/specs/2026-09-07-evidence-addressing-design.md),
[attribution rationale](2026-09-07-evidence-attribution.md), and
[next evidence milestones](research-product-roadmap.md).

## Try the toy demonstration

```sh
python -m eval.evidence_addressing --demo
```

The four authored responses contain one supported citation, one invented ID,
one missing response, and one real but irrelevant citation. The report has two
locator-valid responses and two failures. Of four supplied construction answers,
one matches, one disagrees, and two are unscored. Semantic validity remains
`not_measured`; main collection remains unreleased.

These are software fixtures, not LLM responses or a new experiment. The demo
returns exit code 0 when it runs, including its deliberate negative examples.

## Prepare private inputs

`label_plane.addressed_judge.build_prompt(item)` accepts exactly:

```json
{
  "criteria": "The service stores the record.",
  "reference": "Store the record and retain earlier versions.",
  "scope": "complete",
  "obligations": [
    {"id": "c1", "text": "Store the record."},
    {"id": "c2", "text": "Retain earlier versions."}
  ]
}
```

The resulting private prompt contains `ARTIFACT_SEGMENTS`, `REFERENCE`,
`OBSERVATION_SCOPE`, and `OBLIGATIONS`. Only artifact segments have citable IDs.
No construction answer, source identity, or study split is accepted in the item.
The response contains exactly `checks`, with one ordered entry per obligation:
`id`, `status`, and `evidence_ids`. Obtain IDs from the prompt; do not invent them.

`parse_response(raw, item)` returns the reported status and resolved spans, with
`locator_integrity: valid` and `semantic_validity: not_measured`. Its returned
text, IDs, and artifact hash are private. A valid `covered` result is still the
judge's claim. For absence, a complete observation permits `omitted`; a partial
observation calls for `uncertain`. Visible support or contradiction can still
be assessed under partial scope. The parser checks format and locations, not
whether the judge applied those semantic rules correctly.

## Snapshot and response bounds

| Contract | Fixed rule |
| --- | --- |
| Artifact text | Nonblank, well-formed Unicode, at most 20,000 code points |
| Source preservation | UTF-8 bytes, no case folding or Unicode/newline normalization |
| Segmentation | `utf8-newline-window-400/v1`; while more text remains, prefer the last LF in a 400-code-point window; keep the final remainder intact |
| Segment location | Start-inclusive/end-exclusive UTF-8 byte offsets, at most 256 segments |
| Identity | ID derived from policy, full artifact SHA-256, and offsets; repeated spans at different positions have distinct IDs |
| Snapshot verification | `artifact-segments/v1`; exact recomputation, including types, text, order, offsets, and identity |
| Obligations | One to six, unique ordered IDs up to 64 characters, bounded text under the existing scope contract |
| Response | At most 32,768 characters; strict JSON without duplicate keys, nonstandard constants, extra fields, or repair |
| Citations | At most eight unique current segment IDs per check; covered needs at least one nonblank span |

A content hash detects changes relative to the supplied snapshot. Segment IDs
use 96-bit digest prefixes and are checked for uniqueness within the snapshot;
they are convenience locators, not authentication tokens. A hash does not
prove who authored the text, its license, independence, or the correctness of
the natural-language reference. Segment boundaries are mechanical and can split
an obligation; multiple citations are allowed. IDs and presentation can affect
model behavior, so their policy belongs in any future experimental freeze.

## Audit a supplied response set

Store a JSON array privately. Each record has `item`, `raw_response` (a JSON
string or `null` for an unavailable response), and optionally `expected_checks`
(one construction status per obligation). Omit `expected_checks` when no such
answer exists; `null`, malformed, or incomplete answer inventories are rejected.
Those answers never enter the prompt and are not independently validated labels.

```sh
python -m eval.evidence_addressing --input /approved/private/addressed-responses.json
```

The CLI reads at most 1 MiB and accepts 1-1,000 records. It writes aggregate JSON
to standard output without raw text, response content, source identifiers,
paths, segment IDs, or hashes. It returns 2 on an invalid input file or any
invalid record, otherwise 0. Exit code 0 means the supplied responses met the
software contract; it is not semantic approval or a launch decision.

`attempted_records` counts supplied records, including malformed ones. It is not
the number of planned or completed provider calls. `planned_provider_calls`
is null because this audit has no independent study manifest. Missing planned
rows cannot be discovered by inspecting a response array alone. Use the frozen
study ledger for completion and cost accounting, and keep configurations and
relations separate when assembling audit inputs.

`first_error_counts` reports one detected failure per invalid record, not an
exhaustive taxonomy of overlapping failures. `valid_response_status_counts`
excludes invalid responses explicitly. The construction section reports its
own answer, valid-response, matching, mismatching, and unscored counts. Records
with invalid input/answer inventories remain in the overall attempted count
but do not enter that construction denominator. No accuracy percentage or
confidence interval is inferred from the supplied records.

## Verification boundary

```sh
python -m pytest -q tests/test_artifact_segments.py tests/test_addressed_judge.py tests/test_evidence_addressing.py
```

Tests cover exact text recovery, source-bound identity, unknown/reference-only
cites, malformed payloads, nonstandard JSON, unavailable responses, planned-
denominator caveats, and output redaction. They also preserve the counterexample
where a real citation is irrelevant. No new external model or dependency is
required. Frozen v2/v3 code and the existing feature plane remain unchanged.
