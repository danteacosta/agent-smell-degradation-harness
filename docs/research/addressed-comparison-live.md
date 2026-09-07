# Run the frozen v3/v4 auxiliary comparison

The live coordinator executes the approved 48-call development phase and permits
the 96-call evaluation phase only after development passes. It preserves the
failed predecessor, records its budget closure and owns one exclusive successor
claim. It cannot release main-pilot collection.

The [7 September development run](addressed-comparison-results.md) completed
48 calls and failed its gate. Its 96 evaluation calls must remain unattempted;
the commands below document the interface, not permission to override that result.

Use the [offline interface](addressed-comparison.md) for read-only planning and
supplied-response audits. Its output is not a spending authorization. The
[live specification](../superpowers/specs/2026-09-07-addressed-comparison-live-design.md)
defines custody, accounting, phase gates and acceptance scenarios.

## Freeze and prepare

Use the approved private offline plan and the final committed runtime. The
coordinator can add its own source files to the runtime identity; it requires
every previously frozen source file, package identity, case, prompt, provider,
price and budget term to remain unchanged. Keep both plan versions.

```sh
python -m eval.addressed_comparison_live prepare \
  --approved-plan /absolute/private/approved/plan.json \
  --directory /absolute/private/new-comparison \
  --approve-live
```

Preparation does not call APIs. It requires complete failed predecessor
development, no predecessor evaluation receipts and no pending accounting.
The output must be a new canonical directory outside every Git checkout.
It receives mode 0700; manifest, closure and claim files use mode 0600.
Preparation writes a separate successor claim without replacing the original.

Closure retains actual predecessor spending and releases only the failed
auxiliary's unused direct reservations and contingency. Parent spending,
remaining parent reservations, full parent contingency and the earlier
unresolved amount remain committed. Both the US$1 auxiliary and US$7 shared
limits apply. A second directory cannot obtain another allowance.

## Execute development, then conditional evaluation

```sh
python -m eval.addressed_comparison_live development \
  --directory /absolute/private/new-comparison \
  --env-file /absolute/private/provider.env \
  --approve-live

python -m eval.addressed_comparison_live evaluation \
  --directory /absolute/private/new-comparison \
  --env-file /absolute/private/provider.env \
  --approve-live
```

Evaluation rederives development's decision from verified journal receipts,
not from a saved report. V4 must satisfy the exact-vector rule for each provider;
baseline v3 schema errors remain comparison outcomes. The cases and criteria
must not change after responses arrive.

The coordinator acquires parent, predecessor and successor journal locks in
that order. It reserves before each attempt and disables SDK retries. Resume
skips reconciled calls. Missing usage, changed runtime, corrupt custody or an
ambiguous attempt prevents further dispatch. Preserve the stopped journal;
deleting it does not create a new budget. A failed development judgment gate
leaves evaluation unattempted even when all 48 calls have valid accounting.

## Read the results

```sh
python -m eval.addressed_comparison_live report \
  --directory /absolute/private/new-comparison
```

Reporting is read-only and needs no credentials. Collection commands also save
an immutable report named by the private journal head. Public stdout includes
aggregate progress and a redacted report, not source text, request hashes,
provider names, key values or ledger identities.

The report separates reservations, observed outcomes, reconciled completions,
pending attempts and unattempted calls. A reservation can survive a crash before
network dispatch, so its presence alone does not prove the API received a call.
Pending commitments remain visible alongside verified spending. The nested
offline audit keeps its own authority flags; the live receipt-derived decision
appears separately in `phases`.

Costs use verified token usage and frozen rates. They are not independently
reconciled invoices. The frozen DeepSeek rates are peak rates, so off-peak debits
can be lower. On 2026-09-07, the official
[Luna model page](https://developers.openai.com/api/docs/models/gpt-5.6-luna)
and [DeepSeek pricing table](https://api-docs.deepseek.com/quick_start/pricing/)
matched the frozen input, cache-hit and output rates. Neither account credit
nor future pricing can be inferred from a protocol reservation.

Exit 0 means preparation succeeded, reporting succeeded, or the requested phase
passed. Exit 2 means a phase failed or execution/input validation stopped. A
successful report command does not mean the scientific gate passed.

All planned denominators, invalid judgments and missing observations remain in
the audit. Construction agreement is not human calibration; a resolvable segment
ID can still point to irrelevant evidence. Evaluation locators may have appeared
in earlier background material. Main collection remains blocked and semantic
validity remains unmeasured, including after a passing auxiliary comparison.
