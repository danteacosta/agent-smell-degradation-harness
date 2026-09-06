# Provider account checks and reconciliation limits

Question: can the experiment keys establish remaining credit and recover the
usage of a response-less request? Checked 2026-09-06 using read-only access.

- DeepSeek, [Get User Balance](https://api-docs.deepseek.com/api/get-user-balance/):
  `GET /user/balance` reports availability and balances by currency. This enables
  a private account snapshot, not a key-specific research-spend attribution.
- OpenAI, [Organization usage and costs API](https://developers.openai.com/api/reference/resources/admin/subresources/organization/subresources/usage):
  costs are aggregated expenditure records, not a remaining-credit balance or
  proof of a particular request's token usage. The current experiment key's
  read-only costs request returned HTTP 403. No administrative key was available.

Local consequence: preserve the original ambiguous reservation, request-level
missingness and terminal state. Do not claim zero cost or infer a precise charge
from unrelated aggregated expenditure. An authenticated account owner may later
provide request-level evidence or a provider-confirmed billing resolution.
This does not prevent an independently authorized, separately frozen study.

Downstream use: [expanded v2 study](judge-v2-expanded-plan.md). No credentials,
account identifiers or account balances belong in this public note.
