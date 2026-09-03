# Pre-pilot unlock plan

Status: 2026-09-03. This document turns the launch blockers into executable
steps without promoting a smoke test, a model panel, or a local seed to
confirmatory evidence.

## Current state

| Gate | Evidence already in the repository | Count/status now | Next owner |
|---|---|---:|---|
| Main synchronization | Real-provider pre-pilot gates are in merge commit \`e2b5f17\`; \`eval-gate\`, \`constraint-replay-gate\`, and \`wedge-check\` passed on the reviewed PR head | 1 synchronized main state at `e2b5f17` | engineering |
| Corpus | Seven checked-in seed records; private redacted-intake validator added | 7/12 unique intents; 0 admitted confirmatory records | researcher + advisor |
| Providers | OpenAI-compatible adapter, DeepSeek adapter, usage/cost propagation, and native smoke CLI | 0/2 runtime-native configurations qualified | operator |
| Annotation | Frozen \`tasks/annotation_rubric.json\`; duplicate selection and blinded packet CLI | 0/2 trained annotators; 0 adjudicated items | advisor + annotators |
| Budget | Per-stage token usage and cost fields now flow into episode/provider manifests | USD 0 measured for this phase; approval cap is still unset | operator + advisor |
| Reproducibility | Explicit model version, resolved configuration hash, pair hash, request/response hashes, timestamps, and redacted smoke report | technical path implemented; real report missing | operator |
| Approval | A decision memo is checked in below | 0/1 advisor authorization | advisor/institution |

The numbers above are a status inventory, not an efficacy result.

## Real-provider smoke

Install the live dependency in a clean environment:

\`\`\`bash
python -m pip install -e '.[dev,live]'
\`\`\`

Copy the secret-free example configuration or reference it directly:

\`\`\`bash
python scripts/run_native_provider_smoke.py \\
  --config tasks/native_provider_smoke.example.json \\
  --intents RF-04 \\
  --output /private/tmp/native-provider-smoke.json
\`\`\`

The private environment must define the model and immutable version values as
well as the credentials:

\`\`\`text
OPENAI_API_KEY=...
NATIVE_OPENAI_MODEL=<model selected for the run>
NATIVE_OPENAI_MODEL_VERSION=<provider snapshot or dated version>
NATIVE_OPENAI_INPUT_USD_PER_1K=<frozen price>
NATIVE_OPENAI_CACHED_INPUT_USD_PER_1K=<frozen price>
NATIVE_OPENAI_OUTPUT_USD_PER_1K=<frozen price>

DEEPSEEK_API_KEY=...
NATIVE_DEEPSEEK_MODEL=<model selected for the run>
NATIVE_DEEPSEEK_MODEL_VERSION=<provider snapshot or dated version>
NATIVE_DEEPSEEK_INPUT_USD_PER_1K=<frozen price>
NATIVE_DEEPSEEK_CACHED_INPUT_USD_PER_1K=<frozen price>
NATIVE_DEEPSEEK_OUTPUT_USD_PER_1K=<frozen price>
\`\`\`

Do not paste credentials into chat, JSON, GitHub, or a tracked \`.env\` file.
The DeepSeek adapter defaults to \`https://api.deepseek.com\`, its documented
OpenAI-compatible endpoint. Model aliases and prices are intentionally not
hardcoded: the operator must record the values returned by the provider
documentation at collection time.

A smoke report is operationally acceptable only when both provider slots
complete clean and defective episodes through the same runtime and the report
shows:

1. runtime-native T1, T2, deterministic T3, and terminal stages;
2. monotonic timestamps with the terminal request after T3;
3. three \`no_compaction\` context events and zero compactions per episode;
4. atomic-obligation fields in T1 and hash-bound observations in T3;
5. exact artifact keys from the generation contract;
6. observed usage, latency, response identity, and measured cost.

A passing smoke remains \`smoke_only\`. It does not authorize the 120-episode
pre-pilot and does not enter H1 or H2.

## Corpus intake

Raw source material must be assembled outside the repository as JSONL. Each row
needs the source text, clean and defective variants, a source URL, an immutable
source revision URL and revision ID, license evidence, project ID, retrieval
timestamp, declared removed constraint,
near-clone review, the five manipulation checks, and a timestamped human rights
review confirming redistribution, derivative transformation, attribution, and
transmission to the configured external providers. The validator rejects
placeholders, missing rights evidence, duplicate hashes, missing projects, and
any defect family other than the fixed
\`incompleteness_missing_condition\`.

Example:

\`\`\`bash
python scripts/validate_corpus_intake.py \\
  --input /private/data/prepilot-corpus.jsonl \\
  --output data/prepilot/corpus-manifest.json \\
  --expected-intents 12 \\
  --minimum-projects 6
\`\`\`

The output is a redacted candidate manifest. It contains no requirement text.
A license name or URL alone is insufficient: schema `prepilot-corpus/v4`
fails closed unless all four rights assertions and the reviewer/timestamp are
present. The validator records that review; it does not establish that the
legal interpretation is correct. The exact
redistribution and transformation right must be confirmed by the researcher or
advisor. Current source-screening decisions remain in
\`docs/research/prepilot-corpus-screening.md\`.

## Annotation rehearsal

Prepare private blinded tasks only after the episode/artifact packet is frozen:

\`\`\`bash
python scripts/prepare_blinded_annotation.py \\
  --input /private/data/annotation-input.jsonl \\
  --tasks /private/data/annotator-tasks.jsonl \\
  --manifest /private/data/annotation-selection.json \\
  --kind primary_outcome
\`\`\`

The selection is deterministic, made from item IDs before labels exist, and
records the 20% duplicate subset plus its hash. The primary-outcome packet
includes only the generated artifact and independent reference constraints. It
excludes variant, defect family, oracle result, provider/model identity,
checkpoint evidence, and detector predictions from the coordinator's source
record. Two annotators, a training set outside the
pre-pilot, a named adjudicator, and the alpha/bootstrapping calculation remain
human responsibilities.

## Budget and reproducibility

The observed episode cost is the sum of the three provider calls (T1, T2, and
the terminal artifact). After qualification:

\`\`\`text
estimated pre-pilot provider cap
  = mean observed episode cost × 120 × 1.25
\`\`\`

The approval record must add annotation hours for first coding, the duplicate
subset, adjudication, and quality control. A missing price or missing usage
does not become zero; the runtime reports \`not_configured\` or \`partial\` and
the budget gate stays blocked.

The resolved configuration hash binds the secret-free configuration template
to provider/model/version and pricing identities. The private report, pair hash,
run interval, Python/platform information, stage hashes, and redacted usage
summary form the reproducibility bundle. Preserve the report and the exact
private inputs under the approved project storage policy.

## Approval sequence

1. Advisor confirms the non-confirmatory 120-episode scope, the fixed
   no-compaction primary condition, and the separate four-cell interaction
   check.
2. Researcher/advisor confirm source licenses and the six-project minimum.
3. Operator runs both provider smoke slots and stores the private report.
4. Two annotators complete rehearsal and the adjudicator is named.
5. Operator calculates the provider cap and annotation-hour estimate.
6. Advisor/institution confirms whether an ethics or institutional review is
   required before human annotation and external-provider calls.
7. Only then does \`python -m eval.prepilot_readiness\` become eligible to
   return \`go\`.

## Why the context control is in scope

This implementation treats context transformation as a measured mechanism and
not as a replacement hypothesis. That is consistent with peer-reviewed evidence
that long-context models can underuse information in the middle of a prompt,
and that context compression can trade token savings against information loss.
The article that motivated the typed hard lane is still an emerging preprint;
it is useful for mechanism design, not a peer-reviewed validation of this
experiment.

Relevant sources and credibility ratings:

- [Lost in the Middle, TACL 2024](https://aclanthology.org/2024.tacl-1.9/) —
  peer-reviewed venue, credibility 9/10.
- [LongBench, ACL 2024](https://aclanthology.org/2024.acl-long.172/) —
  peer-reviewed venue, credibility 8/10.
- [LLMLingua-2, Findings of ACL 2024](https://aclanthology.org/2024.findings-acl.57/) —
  peer-reviewed venue, credibility 8/10.
- [Factual Consistency of Abstractive Summarization, EMNLP 2020](https://aclanthology.org/2020.emnlp-main.750/) —
  peer-reviewed venue, credibility 8/10.
- [Requirements Smells in Prompts, ICSE-NIER 2025](https://doi.org/10.1109/ICSE-NIER66352.2025.00016) —
  peer-reviewed venue, credibility 8/10.
- [The Compaction Cliff in Long-Running AI Agent Memory](https://arxiv.org/html/2608.22752) —
  arXiv preprint and mechanism motivation, credibility 6/10.
- [DeepSeek API documentation](https://api-docs.deepseek.com/api/create-chat-completion/) —
  primary operational source for the endpoint, credibility 9/10 for API behavior,
  not peer-reviewed.
- [OpenAI Chat Completions documentation](https://developers.openai.com/api/reference/resources/chat) —
  primary operational source for the endpoint and usage fields, credibility 9/10
  for API behavior, not peer-reviewed.
