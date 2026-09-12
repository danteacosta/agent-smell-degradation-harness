# Behavioral oracle review — 2026-09-11

Status: blocked for real-source behavioral claims. This is an assistant review, not independent human validation. Existing corpus and oracle bytes remain unchanged; the accompanying JSON fingerprints a candidate snapshot, not an approved freeze.

## Executed comparison
Executed both reference implementations for all 12 cases against each case's identical oracle using the trusted-fixture adapter: 12 clean references passed; 12 constructed defective references failed one target test and no unrelated test. This expected construction check is circular as scientific evidence and says nothing about real LLM error frequency.

## Source-to-oracle findings
| Case | Finding and required resolution |
| --- | --- |
| CCTNS-001 | Opt-in guard is supported. Explicitly define event input semantics and add the missing false/false combination. |
| CCTNS-002 | A supplied immutable boolean checks a record predicate, not actual resistance to modification/deletion. Use state transitions and attempted mutations before claiming immutable code behavior. |
| ERTMS-001 | Source states capability to prevent movement; clean rewrite imposes blocking. “Only when” also does not establish sufficient conditions. Resolve modality and behavior outside RBC supervision. |
| ERTMS-002 | Source specifies braking under a conjunction; “continue” outside it assumes a closed world. Explicitly scope the function as this rule alone. |
| FUN-001 | Speaker restriction is supported, but the mutant broadly rewrites the requirement. Verify single-defect isolation. |
| FUN-002 | “Up to six” supports an upper bound; one-party acceptance and zero-party rejection need an explicit input-domain contract. |
| GAMMA-001 | Elapsed-time boolean is a deadline predicate, not measured deployment latency. Define what the boolean means; do not claim runtime performance. |
| GAMMA-002 | Source requires capacity for 1000 concurrent users; clean rewrite imposes maximum 1000 and rejects 1001. This is unsupported strengthening. Quarantine this case from source-faithful inference until revised. |
| NFR-001 | “Exactly every 60 seconds” and a stateless >=60 predicate need a reset/last-refresh model. A predicate does not demonstrate periodic behavior. |
| NFR-002 | “Only authorized” prohibits unauthorized access but does not require allowing every authorized user. State the simplified access-policy assumptions. |
| PEERING-001 | Benign=allow is not established by malicious=reject. Scope other rejection policies explicitly. |
| PEERING-002 | Two booleans test declared category coverage, not processing actual traffic. Clarify construct and executable contract. |

## Qualification outcome and next executable dependency
OpenAI and DeepSeek key variables were absent in the current execution environment. No live calls were made and neither provider was qualified in this review. Existing private qualification evidence elsewhere is not invalidated by this environment limitation.

Do not promote this candidate snapshot to a frozen scientific oracle. Resolve the source-contract discrepancies, obtain independent review of assumptions and rights, then freeze the reviewed pair/oracle hashes. Run both prompt variants with the same reviewed oracle, provider configuration and planned repetitions. Preserve rejected/unexecuted cases separately from behavioral failures. Keep all hidden tests outside provider-visible input and T1–T3 features.

The user authorized proceeding with qualification and comparison; the unresolved dependencies are semantic decisions and access to configured credentials, not a request to repeat authorization. Tests of constructed reference implementations remain instrument checks only.
