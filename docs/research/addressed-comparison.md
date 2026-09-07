# Prepare and audit the v3/v4 comparison offline

Use this interface to prepare the next evaluator comparison from the preserved
failed study and inspect supplied responses. It verifies private custody and
calculates a budget proposal. It cannot call providers, close the previous
study, release reservations or authorize collection.

The [approved design](../superpowers/specs/2026-09-07-addressed-comparison-design.md)
defines 48 development calls and 96 conditional evaluation calls. The six
source locators, six operations, two providers and two arms come from the
preserved bank. Both arms receive the same artifact, reference, observation
scope and obligations, with a 512-token output allowance. V3 keeps its quote
contract; v4 uses artifact segment IDs. Presentation and wording differ, so
the comparison cannot isolate transcription as the cause of any later change.

## Prepare a private plan

Run in the unchanged implementation environment, using canonical absolute
paths. Input paths containing symlinks are rejected. The predecessor must have
complete failed development, zero evaluation receipts and no pending or stopped
journal. Preparation checks its claim, parent, sources, case bank, call plan,
budget and journal under the existing locks. Those files remain unchanged.

```sh
python -m eval.addressed_comparison prepare \
  --predecessor /absolute/private/failed-scoped-study \
  --approve-offline \
  --output-dir /absolute/private/new-comparison-plan
```

The output directory must be new and outside every Git checkout. The command
creates it with mode 0700 and writes `plan.json`, `plan-integrity.json` and an
aggregate `report.json`. Standard output contains only the aggregate report.
Omit `--output-dir` for a read-only estimate without exported files.

The plan contains private source joins, exact inputs, request hashes, provider
configuration, frozen prices, source-file hashes and environment identity. Do
not commit or publish it. Audit rederives the plan from unchanged predecessor
custody and compares canonical identities; the sidecar hash alone is not proof
of authenticity. Changed code or installed-package identity invalidates the
plan. Preserve the corresponding environment for replay.

## Understand the budget proposal

The proposal retains parent spending, every remaining parent reservation, the
parent's full contingency, predecessor spending and the earlier unresolved
reservation. It then adds the full new envelope, including contingency.
Arithmetic uses integer microdollars, with a shared US$7 ceiling and a US$1
ceiling for predecessor auxiliary spending plus the new envelope.

`proposed_cancelled_direct_microusd` and
`proposed_released_contingency_microusd` describe unused commitments that a
future audited closure could release. `closure_applied` remains false. The
report also shows the alternative total with the old full reservation retained.
These figures describe protocol reservations, not API credit balances or
verified future charges.

## Audit supplied responses

Provide a JSON array with one optional record per planned call:

```json
[
  {
    "call_id": "COPY_FROM_THE_PRIVATE_PLAN",
    "prompt_sha256": "COPY_FROM_THE_PRIVATE_PLAN",
    "raw_response": null
  }
]
```

Replace `raw_response` with the unmodified response string when available.
A missing record or `null` response counts as missing. Duplicate or unknown
call IDs, changed prompt digests and extra record fields invalidate the audit.
Malformed model responses count as invalid observations rather than disappearing
from its denominators. Each file is limited to 16 MiB and must be a regular,
UTF-8 JSON file without duplicate object keys or nonstandard constants.

```sh
python -m eval.addressed_comparison audit \
  --plan /absolute/private/new-comparison-plan/plan.json \
  --responses /absolute/private/supplied-responses.json
```

The report separates the following counts:

| Count | Meaning |
| --- | --- |
| `planned` | Every occurrence in the frozen call plan |
| `observed` | A supplied, non-null response; not proof of API dispatch |
| `valid` / `invalid` | Response and evidence-location contract outcomes |
| `missing` | Planned occurrences without a supplied response |
| `aggregate_matches` | Agreement with the constructed aggregate status |
| `exact_matches` | Agreement with the entire constructed obligation vector |

For every stratum, `planned = valid + invalid + missing` and
`observed = valid + invalid`. `arms` aggregates by phase, opaque provider and
arm; `strata` retains opaque source/project groups and operations. The paired
table keeps every planned pair, including missing or invalid arms. Its four
exact-match categories partition all pairs. `unscorable_pairs` overlaps those
categories and must not be added to them as another category.

For each provider, the prospective v4 development rule requires 12/12 valid
responses, at least 10/12 exact vectors, and 2/2 exact vectors for each of long
omission, partial missing, partial complete and partial contradiction.
Evaluation uses 24/24, at least 20/24 and 4/4 respectively. All baseline responses
must be present, but baseline schema failures remain comparison outcomes.
The offline evaluation rule also requires the development response rule.

`met_offline_only` means supplied responses satisfy this response rule. Even a
complete authored fixture can satisfy it. The auditor has no evidence of
verified provider dispatch, usage or cost: `usage_cost_verified` stays false.
Exit 0 for an audit means both candidate response rules are met; exit 2 means
they are not met or input validation failed. Neither exit code authorizes
collection. Preparation uses exit 0 only for a valid offline proposal.

## Execute an authorized comparison

The separate [live coordinator](addressed-comparison-live.md) enforces predecessor
closure and an exclusive successor claim under the shared locks. It retains
spending and unresolved calls, verifies the final runtime and uses one-attempt
dispatch with durable reservations and receipt-derived phase gates. This offline
interface remains read-only and does not supply spending authority.

Historical results remain unchanged. Source transformations and expected answers
are AI assisted, and repeated variants are dependent. A resolvable but irrelevant
citation can pass location validation, even with a matching status vector.
`semantic_validity` therefore remains `not_measured`; H1/H2 and main collection
remain unreleased. No provider improvement can be inferred from software tests.
