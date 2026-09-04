# Native-provider smoke: model selection and compatibility

Date: 2026-09-02

## Question

Which provider/model identifiers and frozen prices are suitable for the
runtime-native pre-pilot, and what adapter behavior is required for bounded
JSON without exposing hidden reasoning?

## Sources

| Source | Use in this protocol |
|---|---|
| [OpenAI GPT-5.6 Luna model page](https://developers.openai.com/api/docs/models/gpt-5.6-luna) | Model ID, Chat Completions support, supported reasoning efforts, and prices of $0.20/M input, $0.02/M cached input, and $1.20/M output. No dated snapshot is listed. |
| [OpenAI latest-model guidance](https://developers.openai.com/api/docs/guides/latest-model) | Current guidance for efficient, high-volume workloads. |
| [DeepSeek models and pricing](https://api-docs.deepseek.com/quick_start/pricing/) | `deepseek-v4-pro`, published version `DeepSeek-V4-Pro-0813`, endpoint, and peak/off-peak prices. |
| [DeepSeek thinking mode](https://api-docs.deepseek.com/guides/thinking_mode/) | Thinking-mode behavior and the `thinking.type` control. |
| [DeepSeek Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/) | `max_tokens`, JSON output, and V4 model identifiers. |
| [DeepSeek change log](https://api-docs.deepseek.com/updates/) | Evidence that moving aliases such as `deepseek-chat` and `deepseek-reasoner` are not frozen identifiers. |

## Frozen candidate configuration

Prices are expressed per 1,000 tokens. DeepSeek uses peak prices for the
conservative budget envelope.

| Slot | Model | Published version | Input / cached input / output per 1K USD |
|---|---|---|---:|
| OpenAI | `gpt-5.6-luna` | `gpt-5.6-luna` | `0.0002 / 0.00002 / 0.0012` |
| DeepSeek | `deepseek-v4-pro` | `DeepSeek-V4-Pro-0813` | `0.00132 / 0.000044 / 0.00396` |

The OpenAI model page does not expose a date-stamped snapshot. Strict
bit-level reproducibility therefore remains an explicit approval item. The
private environment mapping is:

```text
OPENAI_API_KEY <- PANEL_OPENAI_API_KEY
DEEPSEEK_API_KEY <- PANEL_DEEPSEEK_API_KEY
```

No key value is stored in the repository, printed, or included in a report.

## Compatibility findings

The first real calls on commit
`479be14941eb8cbd7cc16ab8e7f5aa4407dab823` found three provider differences:

- OpenAI rejected `max_tokens`; the adapter uses `max_completion_tokens`.
- DeepSeek V4's default thinking mode could exhaust the output budget without
  returning visible `message.content`; the adapter disables thinking unless it
  is explicitly requested.
- GPT-5.6 Luna rejected an explicit `temperature=0.0`; the adapter now lets the
  provider default apply and records the effective setting.

The adapter requests JSON object output and keeps provider-specific request
parameters separate. It does not coerce unsupported atomic-obligation types
or repair provider responses after the fact.

## Smoke evidence

Earlier attempts remain in the private audit trail. OpenAI initially passed the
two RF-04 variants while DeepSeek V4 Flash produced unsupported obligation types
and malformed/truncated JSON. DeepSeek V4 Pro also had malformed responses
before JSON mode. A complete run on commit
`df90b97f3a2338be5be7eaa557521d3370bb9b65` passed both variants for both
providers. The subsequent run on commit
`2258b21bb05c765a225f0a1d7d98e70e68750405` measured US$0.00579582 with
configuration hash
`47b4752bfba36c95e610c67916d9553646d6f503ef7d080e4146c85fa8074db1`.
The canonical rerun on commit `a6f52c29c44a5f65ff2a182255c4e4f66b72477f`
measured US$0.00734218 and retained that configuration hash.

On 3 September, a subsequent smoke exposed a DeepSeek V4 Pro failure on the
clean RF-04 artifact: the response reached the 4,096-token limit and JSON
parsing failed. The terminal prompt was shortened and now requires a minimal
JSON object. The runtime also forwards separate output bounds for T1, T2,
artifact, and judge calls so the cost ledger matches the requests.

The latest post-fix native smoke report is private at
`/private/tmp/prepilot-corpus-20260903/native-smoke-after-substantive-fix-v3.json`.
It passed 4/4 episodes, covering clean and defective RF-04 cases for both
providers, with `no_compaction`, runtime-native T1-T3 and artifact evidence,
usage, response identity, and measured cost. The measured totals were
US$0.00114240 for OpenAI and US$0.00256907 for DeepSeek, approximately
US$0.00371147 combined. Its configuration hash is
`305a557d5e546392039871677c2b763e9ea2ab76732e4b3b016f39c0af8cbcc3`.

This report is `smoke_only`. It qualifies the tested minimal path, not the
120-episode exploratory run. The earlier failures remain relevant and are not
erased by the passing smoke.

## Substantive-completeness correction

The smoke and exploratory runner now share a stricter interpretation of
pre-final evidence. A T1 response must contain non-empty `constraints` and
`atomic_obligations`; a T2 response must contain non-empty
`validation_checks` and `coverage_targets`. The runtime stops before T4 with
`incomplete_substantive_evidence` if the response has the right shape but no
usable content.

The token-fit-corrected exploratory prompt protocol resolves to generation
prompt hash
`85859c0a8ff5f7ab784bab4e4188aa1de7ec4bd84f3e0547927e266c569e2326`.
The corresponding exploratory configuration resolves to
`fecd185cd77c0ac12b6372a3ae301fd531e112e1497cf417ec5a86ca12eeafb0`.
These hashes identify the next run; they do not imply that the full run has
already passed.

The correction removes the repeated raw requirement from T2, passes only the
constraint summary and atomic-obligation fields, serializes that context
compactly, and limits each planned evidence phrase to four words. The stage
token bounds and US$1.00 cap remain unchanged.

## Downstream use

- Use the frozen identifiers and peak prices in the private environment only.
- Treat the latest report as smoke evidence for the tested RF-04 pair.
- Keep the provider and reproducibility gates fail-closed until the corrected
  exploratory run is complete and reviewed.
- Do not use LLM judge agreement as ground truth or as a degradation rate.
- Do not replace the DeepSeek semantic contract with coercion or post-hoc
  repair.
