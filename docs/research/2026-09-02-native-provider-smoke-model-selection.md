# Native-provider smoke: model selection and compatibility

Date: 2026-09-02

## Question

Which immutable provider/model identifiers and frozen prices can be used for
the runtime-native pre-pilot smoke, and what must the adapter send to obtain
bounded JSON responses without exposing hidden reasoning?

## External sources

| Source | Contribution |
|---|---|
| [OpenAI GPT-5.4 Mini model page](https://developers.openai.com/api/docs/models/gpt-5.4-mini) | Lists the dated snapshot `gpt-5.4-mini-2026-03-17`, Chat Completions support, and prices of $0.75/M input, $0.075/M cached input, and $4.50/M output. |
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
| OpenAI | `gpt-5.4-mini-2026-03-17` | `gpt-5.4-mini-2026-03-17` | `0.00075 / 0.000075 / 0.0045` |
| DeepSeek | `deepseek-v4-pro` | `DeepSeek-V4-Pro-0813` | `0.00132 / 0.000044 / 0.00396` |

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

The corrected OpenAI slot passed both clean and smelly RF-04 episodes. DeepSeek
V4 Flash remained unqualified after two complete smoke attempts: it produced an
unsupported `atom_type=pattern`, and separately malformed/truncated JSON. The
V4 Pro candidate also remains unqualified. Before JSON mode, one complete
two-episode smoke had one pass and one malformed-JSON failure; after JSON mode,
the latest complete two-episode smoke had two malformed-JSON failures. A later
single diagnostic execution of V4 Pro passed, so the evidence indicates
response instability rather than an authentication or endpoint failure; it is
not enough to mark the provider gate as passed.

The project therefore keeps the gate fail-closed: a successful individual
episode is not converted into a provider qualification when another episode in
the same smoke fails. The reports are redacted and private:

- `/private/tmp/native-provider-smoke-20260902-gpt54mini-dsv4flash-fixed.json`
- `/private/tmp/native-provider-smoke-20260902-gpt54mini-dsv4flash-retry.json`
- `/private/tmp/native-provider-smoke-20260902-gpt54mini-dsv4pro.json`
- `/private/tmp/native-provider-smoke-20260902-gpt54mini-dsv4pro-jsonmode.json`
- `/private/tmp/native-provider-smoke-20260902-gpt54mini-dsv4pro-final.json`

## Downstream uses

- Use the table above to populate the private native-smoke environment, never
  the tracked example with credentials.
- Treat the OpenAI slot as smoke-qualified for the tested RF-04 pair only.
- Keep the DeepSeek provider gate blocked until one pre-specified complete
  smoke passes for the chosen model/version, including both variants,
  runtime-native T1–T3 provenance, usage, measured cost, and the configuration
  hash.
- Do not replace the DeepSeek semantic contract with coercion or post-hoc
  repair; that would change the observed provider behavior and weaken the
  leakage-resistant measurement.
