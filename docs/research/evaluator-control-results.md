# Real-provider evaluator controls

The PR #39 suite was merged as `17b4184c470a6c5a0604ade2aae64ff431346ad2`.
Collection used runner revision `fae94de0c935e88b7367f2fd24bb5e04e7bdf619`.
Twelve original controls × two configurations × three repetitions produced
72 responses, with no missing or invalid responses and no unreconciled attempts.
Measured provider cost was US$0.008785 under the US$1.00 cap. The cost ledger
conservatively reserved the existing larger pre-pilot envelope (US$0.988200);
the control runner issued 72 calls, not the envelope's 1,296 planned slots.

| Construction-oracle result | OpenAI GPT-5.6 Luna | DeepSeek V4 Pro |
| --- | ---: | ---: |
| Literal coverage correct | 9/9 | 9/9 |
| Reordered coverage correct | 9/9 | 9/9 |
| Deleted condition correct | 0/9 | 0/9 |
| Opposite behavior correct | 0/9 | 7/9 |
| Total correct | 18/36 | 25/36 |
| False coverage on negative controls | 9/18 | 11/18 |
| Abstentions | 9/36 | 0/36 |
| Order switches | 0/9 pairs | 0/9 pairs |

Both configurations failed every deletion control under the historical prompt.
They cannot support reliable omission decisions on this constructed suite.
No order switches were observed, so stability did not imply error sensitivity.
OpenAI abstained on opposite behavior; the report separates abstention from
false coverage.

The previous 279 clean / 9 uncertain distribution remains an operational
exploratory result. These controls provide a concrete reason to withhold any
inference about semantic preservation from that distribution. They do not tell
us how many of those natural artifacts were actually defective. Prompt
anchoring, task underspecification and model behavior remain possible causes;
the experiment does not isolate them.

The construction oracle treats opposite behavior as omitted because the frozen
status vocabulary lacks contradicted. This is a diagnostic mapping. There are
only three base templates, repeated under four operations; 36 judgments per
configuration are not 36 independent natural requirements. No inferential
confidence intervals or human-validity claims are made.

Private evidence: frozen manifest, responses, prompt hashes, configuration
records, per-call latency and append-only usage/cost ledger. No raw provider
responses are tracked. Configured model/version strings and returned model IDs
are recorded; these identifiers alone do not prove immutable vendor weights.

## Executable contract checkpoint

`python -m eval.executable_controls` evaluates four original formal contracts:
numeric limit, role permission, allowed state and authentication precondition.
All 16 test-vector executions matched the specified contract and all four
deliberate mutants were detected. Boolean precondition vectors include repeated
true/false checks; these are executions, not independent semantic cases.
These auxiliary oracles validate evaluator implementation only. They do not
establish correspondence between a formal contract and a natural requirement.

## Immediate interpretation and next experiment

Keep the historical prompt frozen. A future comparison should specify rubric
instructions and balanced examples before collection, hash that new prompt,
retain this baseline, and evaluate fresh held-out control templates as well as
these public diagnostics. A better score on reused examples is development
evidence, not generalization or H1/H2 confirmation.

Temporal analysis is specified in `temporal-warning-protocol.md`. Human audit
and product utility studies are roadmap items in `evidence-priorities-plan.md`.
