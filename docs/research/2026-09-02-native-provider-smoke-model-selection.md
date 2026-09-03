# Native-provider smoke: model selection and compatibility

Date: 2026-09-02

## Question

Which immutable provider/model identifiers and frozen prices can be used for
the runtime-native pre-pilot smoke, and what must the adapter send to obtain
bounded JSON responses without exposing hidden reasoning?

## External sources

| Source | Contribution |
|---|---|
| [OpenAI GPT-5.6 Luna model page](https://developers.openai.com/api/docs/models/gpt-5.6-luna) | Lists `gpt-5.6-luna`, Chat Completions support, supported reasoning efforts, and prices of $0.20/M input, $0.02/M cached input, and $1.20/M output. The page does not currently list a dated snapshot. |
| [OpenAI latest-model guidance](https://developers.openai.com/api/docs/guides/latest-model) | Recommends GPT-5.6 Luna for efficient, high-volume workloads and documents its supported reasoning effort levels. |
| [DeepSeek models and pricing](https://api-docs.deepseek.com/quick_start/pricing/) | Lists `deepseek-v4-pro`, the published version `DeepSeek-V4-Pro-0813`, the official OpenAI-compatible base URL, and peak/off-peak V4 prices. |
| [DeepSeek thinking mode](https://api-docs.deepseek.com/guides/thinking_mode/) | States that thinking is enabled by default, is toggled with `thinking.type`, and returns hidden reasoning in `reasoning_content`; `disabled` selects non-thinking mode. |
| [DeepSeek Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/) | Confirms `max_tokens`, JSON output, and the V4 model identifiers for the OpenAI-compatible endpoint. |
| [DeepSeek change log](https://api-docs.deepseek.com/updates/) | Confirms that the old `deepseek-chat`/`deepseek-reasoner` aliases move with backend upgrades and are not suitable as frozen identifiers for this protocol. |

## Frozen candidate configuration

Prices below are converted from the vendor's per-million-token table to the
smoke's per-1,000-token environment variables. DeepSeek uses peak prices for a
conservative budget envelope; off-peak billing may be lower but is not used to
understate the cap.

| Slot | Model | Published version | Input / cached input / output per 1K USD |
|---|---|---|---:|
| OpenAI | `gpt-5.6-luna` | `gpt-5.6-luna` | `0.0002 / 0.00002 / 0.0012` |
| DeepSeek | `deepseek-v4-pro` | `DeepSeek-V4-Pro-0813` | `0.00132 / 0.000044 / 0.00396` |

The OpenAI model ID is the current documented identifier and is recorded as
the resolved version for this smoke. Because the model page does not expose a
date-stamped snapshot, strict bit-level reproducibility remains a separate
gate item for advisor/committee approval.

The process-only environment mapping used for the private `.env` was:

```text
OPENAI_API_KEY <- PANEL_OPENAI_API_KEY
DEEPSEEK_API_KEY <- PANEL_DEEPSEEK_API_KEY
```

No key value was copied to the repository, printed, or written to a report.

## Local evidence and synthesis

The first real run on commit `479be14941eb8cbd7cc16ab8e7f5aa4407dab823`
exposed two adapter incompatibilities: current OpenAI rejected `max_tokens`
and DeepSeek V4's default thinking mode sometimes returned no visible
`message.content` before the output budget was exhausted. The adapter now uses
`max_completion_tokens` for OpenAI, keeps `max_tokens` for DeepSeek, explicitly
disables DeepSeek thinking unless reasoning is requested, and requests JSON
object output for both providers.

A first GPT-5.6 Luna attempt then showed that this model rejects an explicit
`temperature=0.0`. The adapter now uses the provider default for GPT-5.6 and
records that effective setting in the redacted configuration metadata.

The earlier corrected OpenAI slot passed both clean and smelly RF-04 episodes. DeepSeek
V4 Flash remained unqualified after two complete smoke attempts: it produced an
unsupported `atom_type=pattern`, and separately malformed/truncated JSON. The
V4 Pro candidate was initially unstable: before JSON mode, one complete
two-episode smoke had one pass and one malformed-JSON failure; after JSON mode,
one complete attempt had two malformed-JSON failures. A final complete smoke on
commit `df90b97f3a2338be5be7eaa557521d3370bb9b65` passed both RF-04 variants for
both providers. The subsequent complete smoke with GPT-5.6 Luna and V4 Pro on
commit `2258b21bb05c765a225f0a1d7d98e70e68750405` passed both RF-04 variants for
both providers, measured US$0.00579582, and produced configuration hash
`47b4752bfba36c95e610c67916d9553646d6f503ef7d080e4146c85fa8074db1`.
The canonical rerun after commit `a6f52c29c44a5f65ff2a182255c4e4f66b72477f`
also passed both variants for both providers, measured US$0.00734218, and
retained the same configuration hash. This qualifies both selected slots for
this minimal smoke protocol, while the earlier failures remain useful
robustness evidence and do not get erased from the private audit trail.

The next smoke on 3 September 2026, at the exploratory branch's then-current
commit, reproduced a DeepSeek V4 Pro failure on the clean RF-04 artifact: the
response reached the configured 4,096-token limit and JSON parsing failed. The
OpenAI slot passed both variants, so the run was correctly classified as a
failure rather than promoted. Root-cause tracing showed that the generic
terminal prompt allowed an unnecessarily verbose artifact response. The
terminal prompt now requires a minimal, concise JSON object, and the
exploratory runner forwards the frozen output bound separately to T1, T2,
artifact, and judge calls so the provider request limits match the cost ledger.

A single post-fix smoke rerun passed both RF-04 variants for both providers,
with `no_compaction`, runtime-native T1–T3/artifact evidence, measured usage,
and measured cost of US$0.00498518. The report used for the final audit must be
rerun after these changes are committed so its source revision is the exact
code revision under test; the uncommitted working-tree run is retained only as
diagnostic evidence.

The project therefore keeps the gate fail-closed: a successful individual
episode is not converted into a provider qualification when another episode in
the same smoke fails. The reports are redacted and private:

- `/private/tmp/native-provider-smoke-20260902-gpt54mini-dsv4flash-fixed.json`
- `/private/tmp/native-provider-smoke-20260902-gpt54mini-dsv4flash-retry.json`
- `/private/tmp/native-provider-smoke-20260902-gpt54mini-dsv4pro.json`
- `/private/tmp/native-provider-smoke-20260902-gpt54mini-dsv4pro-jsonmode.json`
- `/private/tmp/native-provider-smoke-20260902-gpt54mini-dsv4pro-final.json`
- `/private/tmp/native-provider-smoke-20260902-gpt54mini-dsv4pro-accounted.json`
- `/private/tmp/native-provider-smoke-20260902-gpt56luna-dsv4pro.json`
- `/private/tmp/native-provider-smoke-20260902-gpt56luna-dsv4pro-retry.json`
- `/private/tmp/native-provider-smoke-20260902-gpt56luna-dsv4pro-final.json`
- `/private/tmp/native-provider-smoke-20260902-gpt56luna-dsv4pro-final-retry.json`

## Downstream uses

- Use the table above to populate the private native-smoke environment, never
  the tracked example with credentials.
- Treat the GPT-5.6 Luna and DeepSeek V4 Pro slots as smoke-qualified for the
  tested RF-04 pair only. The latest report contains both variants,
  runtime-native T1–T3 provenance, usage, measured cost, and the configuration
  hash; it remains a smoke qualification, not pre-pilot execution.
- Keep the strict reproducibility gate open until the missing date-stamped
  OpenAI snapshot issue is resolved or explicitly approved by the advisor or
  committee.
- Do not replace the DeepSeek semantic contract with coercion or post-hoc
  repair; that would change the observed provider behavior and weaken the
  leakage-resistant measurement.
