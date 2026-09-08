# Pricing check before the addressed-evidence comparison

Question: do the approved frozen token rates still bound the authorized
v3/v4 comparison without changing models, prompts or the study envelope?

The sources below were opened on 2026-09-07. They are vendor documentation,
not evidence of evaluator quality or account-specific billing.

| Organization and source | What was verified | Use in the study |
| --- | --- | --- |
| OpenAI, [GPT-5.6 Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna) | US$0.20 input, US$0.02 cached input and US$1.20 output per million tokens | Retain the approved token rates and explicitly selected model |
| DeepSeek, [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/) | V4 Pro peak rates of US$1.32 input, US$0.044 cached input and US$3.96 output per million tokens; off-peak rates are half | Retain the conservative peak-rate freeze; distinguish computed cost from a billed debit |
| DeepSeek, [V4 Pro GA release](https://api-docs.deepseek.com/news/news260813/) | The peak/off-peak update took effect on 2026-08-16 at 16:00 UTC | Check the current pricing table rather than an older cached search excerpt |

The current DeepSeek table identifies V4 Pro as `DeepSeek-V4-Pro-0813`.
The requested and returned identifiers remain evidence of API configuration,
not independent proof that vendor weights are immutable. No model migration
or decoding change follows from this check.

Decision: retain the approved rates and envelope. The
[live report](addressed-comparison-live.md) labels costs as verified token usage
priced at frozen rates and states that invoices have not been reconciled.
DeepSeek charges can be lower outside peak hours. Do not retrospectively rewrite
old journal costs, treat budget reservations as account credits, or use a tariff
discount to launch additional calls outside the approved plan.
