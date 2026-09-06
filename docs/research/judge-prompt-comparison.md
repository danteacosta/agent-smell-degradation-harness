# Comparing the historical judge with an explicit coverage prompt

This auxiliary experiment follows the failure of both original configurations
to detect deletion in the PR #39 controls. The plan is recorded in
[judge-prompt-comparison-plan.md](judge-prompt-comparison-plan.md).
The [results](judge-prompt-comparison-results.md) retain the interrupted v1
comparison and the separate successful 16-call schema-repair smoke.

The historical arm uses the original prompt verbatim. The evidence arm defines
coverage, omission, ambiguity and severity, asks the judge to assess every
clause, and requires a short criterion excerpt for covered behavior. Missing
behavior may have an empty excerpt. The parser checks that excerpts come from
the criteria; it cannot prove that a quoted passage entails the reference.
No control answers or evaluation examples appear in the prompt.

Both arms use a 96-token output limit in this comparison. The previous 72-call
baseline used 48 tokens and remains a separate historical experiment. Model,
pricing and decoding records are frozen before collection. Changes to wording,
input formatting and evidence requirements are evaluated together; the design
does not identify which individual change caused a difference.

## Control strata and denominators

The development stratum contains the 12 existing controls over three templates.
The new stratum contains six original templates, each with literal coverage,
paraphrase, deletion and opposite behavior. Some deletions preserve part of the
requirement while removing a limit or prerequisite. No corpus record is used.

Thirty-six cases, two prompts, two providers and two repetitions give 288 calls.
Each prompt/provider combination has 72 planned judgments. Its new deletion
subset has 12 occurrences over six templates. These occurrences are not twelve
independent requirements. Newly authored examples are not an independently
validated benchmark or a secret holdout.

Report omission detection alongside false alarms on complete cases, abstention,
invalid/missing responses, opposite-behavior performance and paraphrase results.
Evidence validity is a separate count. Do not equate a low false-alarm count with
good performance if calls are missing, invalid or abstaining.

## Reproduction and operational safety

```sh
python -m eval.judge_prompt_comparison --output-dir /approved/private/new-comparison
python -m eval.judge_prompt_comparison --output-dir /approved/private/new-comparison --env-file /approved/private/provider.env --live
```

The first command does not create providers or spend money. The second requires
the existing OpenAI and DeepSeek credentials and a fresh output directory
outside every Git checkout. It freezes the call order, pack, source hashes,
configuration records and price envelope before collection. It never resumes,
overwrites a run, silently retries or sends expected answers to the providers.

This runner dispatches only judge calls. The reused Task 3 cost ledger reserves
US$0.832032 under a US$1 cap for its larger fixed slot plan. Unused generation
slots have 1/1 bounds but are never called; judge bounds are 512/96. This is not
a valid launch configuration for the 120-episode pre-pilot. A separate envelope
for the actual prompt bytes plus a 64-token framing allowance, output limits
and 25% contingency is US$0.325688. The framing allowance is an assumption, not
a certified tokenizer bound. Missing usage or actual ledger-bound exceedance
stops collection and leaves missing denominators in the report.

Raw responses, per-call latency, usage, manifest and append-only cost ledger
remain in the private run directory. The CLI prints progress and budget status;
only aggregate findings belong in public research documents. Configured and
returned model IDs are recorded but do not prove immutable vendor weights.

The separate repaired-contract smoke uses `--study schema_smoke_v2` with a new
directory. It has 16 calls over two new templates, rather than the 288-call
comparison. Its direct byte-based envelope is US$0.027280; the reused ledger
still reserves US$0.832032. Historical and evidence-v1 prompts remain available.

The [expanded v2 plan](judge-v2-expanded-plan.md) uses `--study expanded_v2`:
48 new controls over 12 templates, two prompts (historical and evidence-v2),
two providers and two repetitions, for 384 calls. It does not reuse either
previous pack. Its direct envelope with contingency is US$0.466610, with the
same US$0.832032 conservative ledger envelope and no retries. Use a fresh
private directory; the interrupted v1 study remains a separate record.

## Interpretation boundary

Passing these controls supports further instrument development, not human
agreement, corpus admission, a natural degradation rate or H1/H2. A successful
new prompt does not retroactively validate the old 279 clean / 9 uncertain
distribution. Natural artifacts would need a separately authorized re-evaluation
with a new configuration identity, retaining the old labels and their limits.
