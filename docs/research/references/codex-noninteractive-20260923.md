# Codex non-interactive execution

Source: https://learn.chatgpt.com/docs/non-interactive-mode
Inspected: 2026-09-23, redirected from official developers.openai.com.
Use: verify documented ephemeral noninteractive execution and config isolation.
Decision: preserve installed executable identity and exact flags, supplement docs
with local help, saved-login checks, independent fake CLI isolation integration
and separate availability calls. No immutable model snapshot is inferred.
Related method: ../persistence-collection-method-20260923.md.
