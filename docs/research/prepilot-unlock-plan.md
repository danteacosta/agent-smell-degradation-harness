# Pre-pilot unlock plan

Status: 2026-09-03. This plan separates operational readiness from evidence
that could support H1 or H2. A smoke test, an LLM judge, or a local seed is not
confirmatory evidence.

## Current state

| Gate | Evidence available | Current status | Owner |
|---|---|---|---|
| Main synchronization | PR #35 is squash-merged as `e2b5f17bbdda0c072a89c6f3f4500f367613c929`; `eval-gate`, `constraint-replay-gate`, and `wedge-check` passed | Reconciled on `main`; launch fields remain fail-closed | Engineering |
| Corpus | v4 intake, immutable source references, rights review, hashes, and a frozen redacted manifest | 12 exploratory records across 6 projects validated; confirmatory admission remains a governance decision | Researcher and advisor |
| Providers | Runtime-native OpenAI and DeepSeek adapters, usage/cost propagation, and native smoke CLI | Latest minimal smoke passed both clean and defective RF-04 episodes for both providers; full corrected exploratory run is not complete | Operator |
| Substantive evidence | T1/T2 non-empty-field gate and retry contract | Implemented and covered by tests; full-run coverage is still pending | Engineering and operator |
| Annotation | Frozen rubric and blinded-packet tooling | Advisor authorized LLM judges for this exploratory phase; no human labels or adjudication exist | Advisor and operator |
| Budget | Per-stage cost ledger and frozen prices | Current corrected exploratory configuration reserves US$0.988200 in the US$1.00 cap; annotation effort is not included | Operator and advisor |
| Reproducibility | Prompt, schema, model, price, source, pair, request, response, and run hashes | Corrected exploratory configuration resolves to `160423c8ef1beb6c343bc5f51ab5550f9e40f7aeda0aec7049c5cabc27b2e150`; a full-run report is still missing | Operator |
| Readiness | Fail-closed `prepilot_readiness` report | `no_go` for any claim beyond an exploratory pre-pilot; no H1/H2 claim is authorized | Researcher and advisor |

These are process statuses, not efficacy results.

## What the previous `284 clean` result means

The earlier private run produced 240 artifacts, 288 judging occurrences, 1,296
provider calls, and 284 `clean` versus 4 `uncertain` consolidated judgments.
That count means only that the two LLM judge responses reached the `clean`
label on 284 occurrences under the old protocol. It does not show that the
artifacts were correct, that the reference constraints were covered, or that
the smelly condition caused degradation. There was no independent ground-truth
label in that count.

The run is now diagnostic only. Its T1 and T2 responses could pass the shape
validator while leaving the evidence arrays empty. Therefore its labels cannot
be used as evidence for H1 or H2, and its old prompt/configuration hashes must
not be reused for the corrected run.

## What was missing for H1/H2-oriented evidence

The missing item was not merely a JSON key. The runtime needed a substantive,
pre-final observation that could be audited before T4:

- T1 must contain at least one constraint summary and one valid atomic
  obligation;
- T2 must contain at least one validation check and one coverage target;
- T3 must validate the T1-to-T2 lineage before the terminal artifact is
  requested;
- the terminal artifact must still satisfy the exact task contract; and
- an independent outcome label is required before interpreting an artifact as
  correct or degraded.

The new gate stops an episode with `incomplete_substantive_evidence` when T1 or
T2 is structurally valid but vacuous. It records the failed stage and the
passed/failed completeness counts in the redacted report. It does not infer
that a non-empty field is true; it only prevents an empty field from being
mistaken for evidence.

For H1, the confirmatory outcome must be a frozen clean-versus-defective task
metric with independent labels. For H2, the pre-final feature manifest must be
frozen before outcome labels are inspected, and its incremental value must be
tested against the registered baselines. The exploratory LLM judge can expose
failure modes and feasibility; it is not the ground truth for either
hypothesis.

## Verification schedule

Verification occurs at three distinct points:

1. **Before network calls.** The runner checks the source revision, protocol
   hashes, private corpus join, exactly 12 reference constraints, model/version
   identities, token bounds, and the US$1.00 budget envelope.
2. **Before each terminal artifact.** The runtime validates T1 and T2 shape,
   semantic completeness, conditional fields, atomic obligations, and T3
   lineage. A failure stops the episode before T4.
3. **After the corrected run.** The report must show complete counts for the
   planned artifacts and judgment occurrences, per-stage usage and cost,
   native context events, configuration hashes, and any incomplete episodes.
   Only after that report is reviewed can the run be used as a non-confirmatory
   feasibility result. H1/H2 claims require the separate label and analysis
   gates described above.

The latest low-cost native smoke already verified point 2 on two RF-04 episodes
per provider: 4/4 episodes passed with `no_compaction`, runtime-native T1-T3
and artifact stages, usage, and measured cost. The smoke report remains
`smoke_only`.

The 120-episode corrected rerun has not yet been verified. The execution layer
blocked another full external rerun after the earlier failed attempts; it
requires a fresh explicit authorization for that single run. Until it is
completed, the corrected configuration hash is a planned run identity, not a
claim about results.

## Real-provider smoke

Install the live dependency in a clean environment:

```bash
python -m pip install -e '.[dev,live]'
```

Run the secret-free smoke configuration:

```bash
python scripts/run_native_provider_smoke.py \
  --config tasks/native_provider_smoke.example.json \
  --intents RF-04 \
  --output /private/tmp/native-provider-smoke.json
```

The private environment supplies only the two credentials:

```text
PANEL_OPENAI_API_KEY=...
PANEL_DEEPSEEK_API_KEY=...
```

Do not paste credentials into chat, JSON, GitHub, or a tracked `.env` file.
The selected model identifiers, versions, endpoints, and dated price snapshot
are recorded in the secret-free configuration and the companion research note.

A passing smoke must show, for both provider slots and both RF-04 variants:

1. runtime-native T1, T2, deterministic T3, and terminal stages;
2. timestamps that place the terminal request after T3;
3. three `no_compaction` context events and zero compactions per episode;
4. non-empty atomic-obligation evidence in T1 and hash-bound observations in
   T3;
5. the exact artifact keys from the generation contract; and
6. observed usage, latency, response identity, and measured cost.

A passing smoke does not authorize the 120-episode run and does not enter H1 or
H2.

## Corpus intake

Raw source material is assembled outside the repository as JSONL. Each row
needs the source text, clean and defective variants, source URL, immutable
source revision URL and ID, license evidence, project ID, retrieval timestamp,
the removed constraint, near-clone review, five manipulation checks, and a
timestamped rights review covering redistribution, transformation,
attribution, and transmission to the selected external providers.

The v4 validator emits a redacted manifest and fails closed on placeholders,
missing rights evidence, duplicate hashes, missing projects, missing immutable
references, or an unsupported defect family. The validator records the review;
it does not make a legal determination. A license name or URL alone is
insufficient: all four rights assertions and the reviewer/timestamp must be
present. That determination belongs to the researcher and advisor.

## Annotation and adjudication

For this exploratory run, the advisor authorized the two configured LLMs to act
as independent judges. Their labels are machine observations and must remain
separate from human ground truth. They do not replace two trained annotators or
an adjudicator for any confirmatory analysis.

If the project later claims H1 or H2, the outcome packet must be frozen before
labels are collected, selected without access to labels, and reviewed by
independent human annotators with an explicit adjudication rule. The 20%
duplicate subset remains selected before annotation. Missing labels are
reported, not imputed.

## Budget and reproducibility

The corrected exploratory configuration uses the conservative peak-price
worksheet and reserves US$0.988200 in the US$1.00 cap, including worst-case
retries and the 25% contingency. A missing usage value or price is never
treated as zero.

The private run package must preserve the redacted report, append-only cost
ledger, frozen corpus and constraint hashes, source revision, configuration
hash, protocol hashes, execution window, platform information, and the exact
private input locations under the approved storage policy. Raw requirements,
responses, artifacts, and credentials stay outside tracked artifacts.

## Approval sequence

1. Confirm the 120-episode non-confirmatory scope and `no_compaction` primary
   condition.
2. Confirm the 12-record corpus and six-project minimum under v4 rights review.
3. Verify the current two-provider smoke report.
4. Confirm the advisor's authorization for LLM judges and the US$1.00 provider
   cap.
5. Authorize one corrected 120-episode external run.
6. Review the redacted report for completeness, failures, cost, and hashes.
7. Keep H1/H2 and confirmatory readiness blocked until independent labels and
   the registered analysis gates are complete.

## Sources

- [Lost in the Middle, TACL 2024](https://aclanthology.org/2024.tacl-1.9/) —
  peer-reviewed evidence about long-context retrieval failures.
- [LongBench, ACL 2024](https://aclanthology.org/2024.acl-long.172/) —
  peer-reviewed long-context evaluation benchmark.
- [LLMLingua-2, Findings of ACL 2024](https://aclanthology.org/2024.findings-acl.57/)
  — peer-reviewed work on context compression.
- [Factual Consistency of Abstractive Summarization, EMNLP 2020](https://aclanthology.org/2020.emnlp-main.750/)
  — peer-reviewed work on factual consistency.
- [Requirements Smells in Prompts, ICSE-NIER 2025](https://doi.org/10.1109/ICSE-NIER66352.2025.00016)
  — peer-reviewed task-specific requirements-smell evidence.
- [The Compaction Cliff in Long-Running AI Agent Memory](https://arxiv.org/html/2608.22752)
  — preprint used for mechanism design, not validation.
- [DeepSeek API documentation](https://api-docs.deepseek.com/api/create-chat-completion/)
  — primary operational source for the API.
- [OpenAI Chat Completions documentation](https://developers.openai.com/api/reference/resources/chat)
  — primary operational source for the API and usage fields.
